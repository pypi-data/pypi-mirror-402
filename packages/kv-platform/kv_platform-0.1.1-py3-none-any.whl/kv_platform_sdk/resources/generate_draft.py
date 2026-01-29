from kv_platform_sdk.models.generation import (
    DraftGenerateTemplateRequest,
    DraftCreateDraftRequest,
)


class DraftGenerator:
    def __init__(self, http_client):
        self._http = http_client

    def generate_template(self, request: DraftGenerateTemplateRequest):
        response = self._http.post(
            "/api/agent/draft/generate_template",
            json=request.model_dump(exclude_none=True),
        )
        return response

    def create_draft(self, request: DraftCreateDraftRequest):
        response = self._http.post(
            "/api/agent/draft/create_draft",
            json=request.model_dump(exclude_none=True),
        )
        return response


class AsyncDraftGenerator:
    def __init__(self, http_client):
        self._http = http_client

    async def generate_template(self, request: DraftGenerateTemplateRequest):
        response = await self._http.post(
            "/api/agent/draft/generate_template",
            json=request.model_dump(exclude_none=True),
        )
        return response

    async def create_draft(self, request: DraftCreateDraftRequest):
        response = await self._http.post(
            "/api/agent/draft/create_draft",
            json=request.model_dump(exclude_none=True),
        )
        return response
