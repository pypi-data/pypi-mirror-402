import httpx
from typing import Any, Dict, Optional
from .base import BaseHTTPClient


class SyncHTTPClient(BaseHTTPClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = httpx.Client(timeout=self.timeout)

    def post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        response = self._client.post(
            f"{self.base_url}{path}",
            headers=self._headers(headers),
            json=json,
            files=files,
        )
        response.raise_for_status()
        return response.json()

    def get(self, path: str) -> Dict[str, Any]:
        response = self._client.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()
