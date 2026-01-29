from kv_platform_sdk.models.extractor import TimelineBuilderRequest


class TimelineBuilderResource:
    def __init__(self, http_client):
        self._http = http_client

    def build(self, request: TimelineBuilderRequest):
        response = self._http.post(
            "/api/agent/timeline_builder",
            json=request.model_dump(exclude_none=True),
        )
        return response


class AsyncTimelineBuilderResource:
    def __init__(self, http_client):
        self._http = http_client

    async def build(self, request: TimelineBuilderRequest):
        response = await self._http.post(
            "/api/agent/timeline_builder",
            json=request.model_dump(exclude_none=True),
        )
        return response
