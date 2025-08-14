# src/realtime.py
import json, logging, threading, requests
from sseclient import SSEClient
from typing import Callable

class RTDBListener:
    def __init__(self, base_url: str, token_getter: Callable[[], str | None],
                 path_json: str, on_event: Callable[[dict | list | None], None]):
        self.base = base_url.rstrip("/")
        self.path = path_json if path_json.startswith("/") else "/" + path_json
        self.token_getter = token_getter
        self.on_event = on_event
        self._stop = threading.Event()
        self._t = None

    def start(self):
        if self._t and self._t.is_alive():
            return
        self._stop.clear()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        try:
            url = f"{self.base}{self.path}"
            params = {}
            tok = self.token_getter() if self.token_getter else None
            if tok:
                params["auth"] = tok
            headers = {"Accept": "text/event-stream"}
            with requests.get(url, params=params, headers=headers, stream=True, timeout=60) as r:
                r.raise_for_status()
                client = SSEClient(r)
                for evt in client.events():
                    if self._stop.is_set():
                        break
                    if evt.event in ("put", "patch"):
                        try:
                            payload = json.loads(evt.data)  # {"path": "...", "data": ...}
                            self.on_event(payload.get("data"))
                        except Exception as e:
                            logging.error(f"[RTDBListener] parse error: {e}")
        except Exception as e:
            logging.error(f"[RTDBListener] stream error: {e}")