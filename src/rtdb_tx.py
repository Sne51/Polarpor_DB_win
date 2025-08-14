# src/rtdb_tx.py
import json, requests

def get_with_etag(base_url: str, path_json: str, token: str | None):
    url = f"{base_url.rstrip('/')}/{path_json.lstrip('/')}"
    headers = {"X-Firebase-ETag": "true"}
    params = {"auth": token} if token else {}
    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    etag = r.headers.get("ETag")
    data = r.json() if (r.text and r.text.strip()) else None
    return data, etag

def put_if_match(base_url: str, path_json: str, token: str | None, data, etag: str) -> bool:
    url = f"{base_url.rstrip('/')}/{path_json.lstrip('/')}"
    headers = {"If-Match": etag, "Content-Type": "application/json"}
    params = {"auth": token} if token else {}
    r = requests.put(url, headers=headers, params=params, data=json.dumps(data), timeout=30)
    if r.status_code == 412:  # кто-то изменил — не наша бронь
        return False
    r.raise_for_status()
    return True