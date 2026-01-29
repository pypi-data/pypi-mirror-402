from kv_platform_sdk.models.extractor import DataExtractorRequest, DataExtractorResponse


class DataExtractorResource:
    def __init__(self, http_client):
        self._http = http_client

    def extract(self, request: DataExtractorRequest) :
        response = self._http.post(
            "/api/agent/data_extractor",
            json=request.model_dump(exclude_none=True),
        )
        return response




class AsyncDataExtractorResource:
    def __init__(self, http_client):
        self._http = http_client

    async def extract(self, request: DataExtractorRequest):
        response = await self._http.post(
            "/api/agent/data_extractor",
            json=request.model_dump(exclude_none=True),
        )
        return response
