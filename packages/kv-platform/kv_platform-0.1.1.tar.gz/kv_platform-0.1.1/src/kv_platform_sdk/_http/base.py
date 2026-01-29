from typing import Dict, Optional


class BaseHTTPClient:
    def __init__(self, base_url: str, access_key: str, timeout: float = 1000.0):
        self.base_url = base_url.rstrip("/")
        self.access_key = access_key
        self.timeout = timeout

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "access-key": self.access_key,
        }
        if extra:
            headers.update(extra)
        return headers
