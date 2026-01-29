from kv_platform_sdk.models.form_filler import (
    FormGenerateRequest, FormFillRequest
)


class FormFillerResource:
    def __init__(self, http_client):
        self._http = http_client

    def generate(self, request: FormGenerateRequest):
        response = self._http.post(
            "/api/agent/form/generate",
            json=request.model_dump(exclude_none=True),
        )
        return response
    def fill(self, request: FormFillRequest) :
        response = self._http.post(
            "/api/agent/form/fill",
            json=request.model_dump(exclude_none=True),
        )
        return response


class AsyncFormFillerResource:
    def __init__(self, http_client):
        self._http = http_client

    async def generate(
        self, request: FormGenerateRequest
    ) :
        response = await self._http.post(
            "/api/agent/form/generate",
            json=request.model_dump(exclude_none=True),
        )
        return response
    async def fill(self, request: FormFillRequest) :
        response = await self._http.post(
            "/api/agent/form/fill",
            json=request.model_dump(exclude_none=True),
        )
        return response