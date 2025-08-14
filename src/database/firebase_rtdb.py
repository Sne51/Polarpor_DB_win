
# src/firebase_manager.py
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from google.auth.transport.requests import Request

from src.database.base import DatabaseManager
from src.database.firebase_rtdb import FirebaseRTDBManager

FIREBASE_DB_URL = "https://polapordb-default-rtdb.asia-southeast1.firebasedatabase.app"
CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "config" / "firebase_credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/firebase.database",
    "https://www.googleapis.com/auth/userinfo.email",
]

def _make_access_token_getter():
    if not CREDENTIALS_PATH.exists():
        logging.error(f"Firebase credentials not found: {CREDENTIALS_PATH}")
        return lambda: None

    creds = service_account.Credentials.from_service_account_file(
        str(CREDENTIALS_PATH),
        scopes=SCOPES
    )

    def _getter() -> Optional[str]:
        nonlocal creds
        try:
            if not creds.valid:
                creds.refresh(Request())
            return creds.token
        except Exception as e:
            logging.error(f"Failed to refresh Firebase token: {e}")
            return None

    return _getter


class FirebaseManager(DatabaseManager):
    """Тонкий адаптер вокруг FirebaseRTDBManager."""

    def __init__(self, db_url: str = FIREBASE_DB_URL):
        self._db = FirebaseRTDBManager(
            base_url=db_url,
            access_token_getter=_make_access_token_getter()
        )

    # -------- Realtime --------
    def on(self, channel: str, callback):
        return self._db.on(channel, callback)

    def off(self, token: str) -> None:
        return self._db.off(token)

    # -------- Cases --------
    def get_all_cases(self):
        return self._db.get_all_cases()

    def add_case(self, data: dict) -> str:
        return self._db.add_case(data)

    def delete_case(self, case_id: str) -> None:
        return self._db.delete_case(case_id)

    # -------- Proformas --------
    def get_all_proformas(self):
        return self._db.get_all_proformas()

    def add_proforma(self, data: dict) -> str:
        return self._db.add_proforma(data)

    def delete_proforma(self, proforma_id: str) -> None:
        return self._db.delete_proforma(proforma_id)

    def reserve_proforma_case_number(self, case_number: str) -> bool:
        return self._db.reserve_proforma_case_number(case_number)

    def release_proforma_case_number(self, case_number: str) -> None:
        return self._db.release_proforma_case_number(case_number)

    # -------- Clients --------
    def get_all_clients(self):
        return self._db.get_all_clients()

    def check_and_add_client(self, name: str) -> str:
        return self._db.check_and_add_client(name)

    def delete_client(self, client_id: str) -> None:
        return self._db.delete_client(client_id)

    # -------- Suppliers --------
    def get_all_suppliers(self):
        return self._db.get_all_suppliers()

    def add_supplier(self, name: str) -> str:
        return self._db.add_supplier(name)

    def delete_supplier(self, supplier_id: str) -> None:
        return self._db.delete_supplier(supplier_id)

    # -------- Cargo --------
    def get_all_cargo(self):
        return self._db.get_all_cargo()

    def add_cargo(self, data: dict) -> str:
        return self._db.add_cargo(data)

    def delete_cargo(self, cargo_id: str) -> None:
        return self._db.delete_cargo(cargo_id)

    # -------- Managers --------
    def get_all_managers(self):
        return self._db.get_all_managers()