import httpx
from typing import Any, Dict, Optional
from .base import BaseHTTPClient


class AsyncHTTPClient(BaseHTTPClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        response = await self._client.post(
            f"{self.base_url}{path}",
            headers=self._headers(headers),
            json=json,
            files=files,
        )
        response.raise_for_status()
        return response.json()

    async def get(self, path: str) -> Dict[str, Any]:
        response = await self._client.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()
    

    async def close(self) -> None:
        await self._client.aclose()
