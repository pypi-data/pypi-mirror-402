from kv_platform_sdk.models.comparison import FormatComparisonRequest, ContentComparisonRequest 


class FormatComparisonResource:
    def __init__(self, http_client):
        self._http = http_client

    def format_compare(self, request: FormatComparisonRequest):
        response = self._http.post(
            "/api/agent/format_comparison",
            json=request.model_dump(),
        )
        return response
    def content_compare(self, request: ContentComparisonRequest):
        return self._http.post(
            "/api/agent/content_comparison",
            json=request.model_dump(),
        )



class AsyncFormatComparisonResource:
    def __init__(self, http_client):
        self._http = http_client
    async def format_compare(self, request: FormatComparisonRequest):
        response = await self._http.post(
            "/api/agent/format_comparison",
            json=request.model_dump(),
        )
        return response

    async def content_compare(self, request: ContentComparisonRequest):
        return await self._http.post(
            "/api/agent/content_comparison",
            json=request.model_dump(),
        )