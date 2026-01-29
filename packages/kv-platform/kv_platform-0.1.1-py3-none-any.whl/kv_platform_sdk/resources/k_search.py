from kv_platform_sdk.models.search_and_inference import (
    KnowledgeSearchRequest
)


class KnowledgeSearchResource:
    def __init__(self, http_client):
        self._http = http_client

    def search(self, request: KnowledgeSearchRequest):
        response = self._http.post(
            "/api/agent/k_search",
            json=request.model_dump(),
            headers={"Content-Type": "application/json"},
        )
        return response


class AsyncKnowledgeSearchResource:
    def __init__(self, http_client):
        self._http = http_client

    async def search(self, request: KnowledgeSearchRequest):
        response = await self._http.post(
            "/api/agent/k_search",
            json=request.model_dump(),
            headers={"Content-Type": "application/json"},
        )
        return response
