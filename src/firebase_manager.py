# src/firebase_manager.py
import os
import json
import logging
from pathlib import Path
from typing import Callable, Dict, Any, Optional
import threading
from uuid import uuid4
import time

import requests
from firebase_admin import credentials, initialize_app, db

# --- Realtime (SSE) ---
try:
    from sseclient import SSEClient  # pip install sseclient-py
except Exception:
    SSEClient = None

# --- OAuth2 для service account токена ---
try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GARequest
except Exception:
    service_account = None
    GARequest = None


class FirebaseManager:
    """
    Менеджер Firebase для RTDB + SSE подписок (on/off).
    """

    # OAuth2 scope для доступа к RTDB от имени service account
    _SCOPES = (
        "https://www.googleapis.com/auth/firebase.database",
        "https://www.googleapis.com/auth/userinfo.email",
    )

    def __init__(self):
        # Корень проекта
        self.ROOT_DIR = Path(__file__).resolve().parents[1]

        # ---- Креды ----
        cred_path_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        cred_path = (
            Path(cred_path_env)
            if cred_path_env
            else self.ROOT_DIR / "config" / "firebase_credentials.json"
        )
        if not cred_path.exists():
            candidates = (
                list(self.ROOT_DIR.glob("*firebase*admin*.json"))
                + list((self.ROOT_DIR / "config").glob("*firebase*admin*.json"))
                + list((self.ROOT_DIR / "config").glob("*firebase*credentials*.json"))
            )
            if candidates:
                cred_path = candidates[0]
            else:
                raise FileNotFoundError(
                    "Firebase credentials file not found. "
                    f"Ожидался: {self.ROOT_DIR / 'config' / 'firebase_credentials.json'} "
                    "или укажи GOOGLE_APPLICATION_CREDENTIALS."
                )

        logging.info(f"Using Firebase credentials: {cred_path}")

        # ---- Admin SDK RTDB ----
        cred = credentials.Certificate(str(cred_path))
        initialize_app(
            cred,
            {
                "databaseURL": "https://polapordb-default-rtdb.asia-southeast1.firebasedatabase.app/"
            },
        )

        # Базовый URL БД (без завершающего '/')
        self.base_url = "https://polapordb-default-rtdb.asia-southeast1.firebasedatabase.app"

        # RTDB references (Admin SDK)
        self.cases_ref = db.reference("cases")
        self.clients_ref = db.reference("clients")
        self.proformas_ref = db.reference("proformas")
        self.suppliers_ref = db.reference("suppliers")
        self.cargo_ref = db.reference("cargo")

        # Локальные файлы
        self.managers_file = self.ROOT_DIR / "managers.json"

        # HTTP-сессия и подписки
        self._session = requests.Session()
        self._streams: Dict[str, Dict[str, Any]] = {}

        # Готовим креды для получения access_token
        self._cred_file = str(cred_path)
        self._creds = None
        self._access_token: Optional[str] = None
        self._token_expiry_ts: float = 0.0  # unix ts

        if service_account is None:
            logging.warning(
                "google-auth не найден — realtime через SSE работать не сможет. "
                "Установи: pip install google-auth"
            )

        # Предварительно получим токен (не критично, но ускоряет первую подписку)
        try:
            self._ensure_access_token()
        except Exception as e:
            logging.warning(f"Access token init warning: {e}")

    # ===================== ВСПОМОГАТЕЛЬНОЕ: OAuth2 =====================

    def _ensure_access_token(self, min_ttl: int = 60) -> str:
        """
        Возвращает валидный access token; обновляет, если истёк.
        min_ttl — минимальный оставшийся срок жизни токена (сек), при котором мы считаем его «годным».
        """
        now = time.time()
        if self._access_token and (self._token_expiry_ts - now) > min_ttl:
            return self._access_token

        if service_account is None or GARequest is None:
            raise RuntimeError(
                "google-auth не установлен. Установи: pip install google-auth"
            )

        if self._creds is None:
            self._creds = service_account.Credentials.from_service_account_file(
                self._cred_file,
                scopes=list(self._SCOPES),
            )

        if not self._creds.valid or self._creds.expired:
            self._creds.refresh(GARequest())

        # google-auth сам хранит expiry (datetime). Переведём в ts.
        self._access_token = self._creds.token
        expiry_dt = getattr(self._creds, "expiry", None)
        self._token_expiry_ts = expiry_dt.timestamp() if expiry_dt else now + 300
        return self._access_token

    # ===================== УТИЛИТЫ =====================

    def _next_numeric_key(self, root_ref) -> str:
        """Определяет следующий ID."""
        try:
            data = root_ref.get() or {}
            if isinstance(data, list):
                return str(len(data))
            numeric = []
            if isinstance(data, dict):
                for k in data.keys():
                    try:
                        numeric.append(int(k))
                    except Exception:
                        pass
            return str(max(numeric) + 1) if numeric else "1"
        except Exception as e:
            logging.error(f"_next_numeric_key: {e}")
            return "1"

    # ===================== CASES =====================

    def get_all_cases(self) -> dict:
        try:
            data = self.cases_ref.get() or {}
            logging.debug(f"Cases loaded: {data}")
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logging.error(f"get_all_cases: {e}")
            return {}

    def add_case(self, case_data: dict) -> str:
        try:
            case_id = self._next_numeric_key(self.cases_ref)
            payload = dict(case_data or {})
            payload["id"] = case_id
            payload.setdefault("name", "")
            payload.setdefault("client", "")
            payload.setdefault("client_name", "")
            payload.setdefault("manager", "")
            payload.setdefault("manager_name", "")
            payload.setdefault("comment", "")
            payload.setdefault("date_created", "")
            self.cases_ref.child(case_id).set(payload)
            return case_id
        except Exception as e:
            logging.error(f"add_case: {e}")
            raise

    def delete_case(self, case_id: str) -> None:
        try:
            if not case_id:
                return
            self.cases_ref.child(str(case_id)).delete()
        except Exception as e:
            logging.error(f"delete_case: {e}")
            raise

    # ===================== CLIENTS =====================

    def get_all_clients(self) -> dict:
        try:
            data = self.clients_ref.get() or {}
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logging.error(f"get_all_clients: {e}")
            return {}

    def add_client(self, client_name: str) -> str:
        try:
            new_id = self._next_numeric_key(self.clients_ref)
            payload = {"id": new_id, "name": (client_name or "").strip()}
            self.clients_ref.child(new_id).set(payload)
            return new_id
        except Exception as e:
            logging.error(f"add_client: {e}")
            raise

    def delete_client(self, client_id: str) -> None:
        try:
            if not client_id:
                return
            self.clients_ref.child(str(client_id)).delete()
        except Exception as e:
            logging.error(f"delete_client: {e}")
            raise

    def check_and_add_client(self, client_name=None, check_only=False, client_id=None):
        """Проверяет и при необходимости добавляет клиента."""
        try:
            if client_id:
                node = self.clients_ref.child(str(client_id))
                existing = node.get()
                if not isinstance(existing, dict):
                    node.set({"id": str(client_id), "name": (client_name or "").strip()})
                return str(client_id)

            name = (client_name or "").strip()
            if not name:
                return None

            clients = self.get_all_clients() or {}
            for cid, data in clients.items():
                if isinstance(data, dict) and data.get("name", "").strip().lower() == name.lower():
                    return str(cid)

            if check_only:
                return None

            return self.add_client(name)
        except Exception as e:
            logging.error(f"check_and_add_client: {e}")
            raise

    # ===================== PROFORMAS =====================

    def get_all_proformas(self) -> dict:
        try:
            data = self.proformas_ref.get() or {}
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logging.error(f"get_all_proformas: {e}")
            return {}

    def add_proforma(self, proforma_data: dict) -> str:
        try:
            proforma_id = self._next_numeric_key(self.proformas_ref)
            payload = dict(proforma_data or {})
            payload.setdefault("name", "")
            payload.setdefault("case_number", "")
            payload.setdefault("comment", "")
            payload.setdefault("date_created", "")
            self.proformas_ref.child(proforma_id).set(payload)
            return proforma_id
        except Exception as e:
            logging.error(f"add_proforma: {e}")
            raise

    def delete_proforma(self, proforma_id: str) -> None:
        try:
            self.proformas_ref.child(str(proforma_id)).delete()
        except Exception as e:
            logging.error(f"delete_proforma: {e}")
            raise

    # ===================== SUPPLIERS =====================

    def get_all_suppliers(self):
        try:
            data = self.suppliers_ref.get() or {}
            logging.debug(f"get_all_suppliers type={type(data).__name__}")
            return data if isinstance(data, (list, dict)) else {}
        except Exception as e:
            logging.error(f"get_all_suppliers: {e}")
            return {}

    def add_supplier(self, supplier_data: dict) -> str:
        try:
            current = self.suppliers_ref.get()
            name = (supplier_data or {}).get("name", "").strip()
            payload = {"name": name}

            if isinstance(current, list):
                new_index = len(current) if current else 0
                self.suppliers_ref.child(str(new_index)).set(payload)
                return str(new_index)

            new_id = self._next_numeric_key(self.suppliers_ref)
            self.suppliers_ref.child(new_id).set(payload)
            return new_id
        except Exception as e:
            logging.error(f"add_supplier: {e}")
            raise

    def delete_supplier(self, supplier_id: str) -> None:
        try:
            current = self.suppliers_ref.get()
            if isinstance(current, list):
                idx = int(supplier_id)
                self.suppliers_ref.child(str(idx)).delete()
                return
            self.suppliers_ref.child(str(supplier_id)).delete()
        except Exception as e:
            logging.error(f"delete_supplier: {e}")
            raise

    # ===================== CARGO =====================

    def get_all_cargo(self):
        try:
            data = self.cargo_ref.get() or {}
            return data if isinstance(data, (list, dict)) else {}
        except Exception as e:
            logging.error(f"get_all_cargo: {e}")
            return {}

    def add_cargo(self, cargo_data: dict) -> str:
        try:
            cargo_id = self._next_numeric_key(self.cargo_ref)
            self.cargo_ref.child(cargo_id).set(cargo_data or {})
            return cargo_id
        except Exception as e:
            logging.error(f"add_cargo: {e}")
            raise

    def delete_cargo(self, cargo_id: str) -> None:
        try:
            self.cargo_ref.child(str(cargo_id)).delete()
        except Exception as e:
            logging.error(f"delete_cargo: {e}")
            raise

    # ===================== MANAGERS =====================

    def get_all_managers(self) -> list[str]:
        try:
            if not self.managers_file.exists():
                logging.warning(f"Managers file not found: {self.managers_file}")
                return []
            with open(self.managers_file, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            return [
                m["name"]
                for m in data.get("managers", [])
                if isinstance(m, dict) and "name" in m
            ]
        except Exception as e:
            logging.error(f"get_all_managers: {e}")
            return []

    # ===================== REALTIME (SSE) =====================

    def on(self, path: str, callback: Callable[[str], None]) -> str:
        """
        Подписка на события RTDB узла (например 'proformas', 'cases', 'suppliers').
        Возвращает token; передай его в off(token), чтобы отписаться.
        callback получает raw JSON-строку события (event.data).
        """
        if SSEClient is None:
            raise RuntimeError(
                "sseclient-py не установлен. Установи: pip install sseclient-py"
            )

        token = uuid4().hex
        stop_event = threading.Event()

        # Собираем URL вида:
        # https://<db>/<path>.json?access_token=<oauth2>
        def _make_url() -> str:
            base = self.base_url.rstrip("/")
            access_token = self._ensure_access_token()
            return f"{base}/{path}.json?access_token={access_token}"

        def _worker():
            while not stop_event.is_set():
                url = _make_url()
                try:
                    with self._session.get(
                        url,
                        headers={"Accept": "text/event-stream", "User-Agent": "Polarpor-Client/1.0"},
                        stream=True,
                        timeout=(10, 310),  # connect, read
                    ) as resp:
                        if resp.status_code >= 400:
                            body = ""
                            try:
                                body = resp.text[:200]
                            except Exception:
                                pass
                            logging.error(f"[RTDB stream] HTTP {resp.status_code}: {body}")
                            # возможно истёк токен — форсируем обновление перед ретраем
                            self._token_expiry_ts = 0
                            stop_event.wait(2)
                            continue

                        client = SSEClient(resp)
                        for event in client.events():
                            if stop_event.is_set():
                                break
                            evtype = (event.event or "").lower()
                            if evtype in ("put", "patch", "message", ""):
                                try:
                                    callback(event.data)
                                except Exception as cb_e:
                                    logging.error(f"[RTDB stream] callback error: {cb_e}")
                except Exception as e:
                    logging.error(f"[RTDB stream] connection error: {e}")
                    # В случае сетевого обрыва — подождём и переподключимся
                    stop_event.wait(2)

        th = threading.Thread(target=_worker, name=f"rtdb-{path}-{token}", daemon=True)
        th.start()
        self._streams[token] = {"thread": th, "stop": stop_event}
        return token

    def off(self, token: str) -> None:
        """Отключить подписку, полученную через on()."""
        info = self._streams.pop(token, None)
        if not info:
            return
        info["stop"].set()
        # Поток сам завершится на ближайшей итерации.