from typing import Dict, Any
from kv_platform_sdk.models.search_and_inference import TextSummarizerRequest


class TextSummarizerResource:
    def __init__(self, http_client):
        self._http = http_client

    def generate(self, request: TextSummarizerRequest):
        return self._http.post(
            "/api/agent/text_summarizer",
            json=request.model_dump(exclude_none=True),
        )


class AsyncTextSummarizerResource:
    def __init__(self, http_client):
        self._http = http_client

    async def generate(self, request: TextSummarizerRequest):
        return await self._http.post(
            "/api/agent/text_summarizer",
            json=request.model_dump(exclude_none=True),
        )
