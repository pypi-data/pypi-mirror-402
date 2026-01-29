from typing import Optional
from kv_platform_sdk.models.search_and_inference import FAQGeneratorRequest


class FAQGeneratorResource:
    def __init__(self, http_client):
        self._http = http_client

    def generate(self, request: FAQGeneratorRequest) :
        response = self._http.post(
            "/api/agent/faq_generator",
            json=request.model_dump(exclude_none=True),
        )
        return response


class AsyncFAQGeneratorResource:
    def __init__(self, http_client):
        self._http = http_client

    async def generate(self, request: FAQGeneratorRequest) :
        response = await self._http.post(
            "/api/agent/faq_generator", json=request.model_dump(exclude_none=True)
        )
        return response
