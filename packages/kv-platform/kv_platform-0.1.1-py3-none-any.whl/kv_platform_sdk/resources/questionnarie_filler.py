from kv_platform_sdk.models.questionnaire_filler import (
    QuestionnaireGenerateRequest,
    QuestionnaireFillRequest
)


class QuestionnaireGenerateResource:
    def __init__(self, http_client):
        self._http = http_client

    def generate(
        self,
        request: QuestionnaireGenerateRequest,
    ) :
        response = self._http.post(
            "/api/agent/questionnaire/generate",
            json=request.model_dump(exclude_none=True),
        )
        return response
    def fill(self, request: QuestionnaireFillRequest):
        response = self._http.post(
            "/api/agent/questionnaire/fill",
            json=request.model_dump(exclude_none=True),
        )
        return response
    
class AsyncQuestionnaireGenerateResource:
    def __init__(self, http_client):
        self._http = http_client

    async def generate(
        self,
        request: QuestionnaireGenerateRequest,
    ) :
        response = await self._http.post(
            "/api/agent/questionnaire/generate",
            json=request.model_dump(exclude_none=True),
        )
        return response
    async def fill(
        self, request: QuestionnaireFillRequest
    ) :
        response = await self._http.post(
            "/api/agent/questionnaire/fill",
            json=request.model_dump(exclude_none=True),
        )
        return response