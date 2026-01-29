from kv_platform_sdk._http._async import AsyncHTTPClient
from kv_platform_sdk.resources.faq_generator import AsyncFAQGeneratorResource
from kv_platform_sdk.resources.documents import AsyncDocumentsResource
from kv_platform_sdk.resources.k_search import AsyncKnowledgeSearchResource
from kv_platform_sdk.resources.data_extractor import AsyncDataExtractorResource
from kv_platform_sdk.resources.timeline_builder import AsyncTimelineBuilderResource
from kv_platform_sdk.resources.generate_draft import AsyncDraftGenerator
from kv_platform_sdk.resources.form_filler import AsyncFormFillerResource
from kv_platform_sdk.resources.questionnarie_filler import AsyncQuestionnaireGenerateResource
from kv_platform_sdk.resources.comparison import AsyncFormatComparisonResource
from kv_platform_sdk.resources.text_summarizer import AsyncTextSummarizerResource


class AsyncClient:
    def __init__(
        self,
        access_key: str,
        base_url: str = "https://api.k-v.ai",
        timeout: float = 1000.0,
    ):
        self._http = AsyncHTTPClient(base_url, access_key, timeout)
        self.faq_generator = AsyncFAQGeneratorResource(self._http)
        self.documents = AsyncDocumentsResource(self._http)
        self.k_search = AsyncKnowledgeSearchResource(self._http)
        self.data_extractor = AsyncDataExtractorResource(self._http)
        self.timeline_builder = AsyncTimelineBuilderResource(self._http)
        self.draft_generate = AsyncDraftGenerator(self._http)
        self.form_filler = AsyncFormFillerResource(self._http)
        self.questionnaire_filler = AsyncQuestionnaireGenerateResource(self._http)
        self.comparison = AsyncFormatComparisonResource(self._http)
        self.text_summarizer = AsyncTextSummarizerResource(self._http)

    async def close(self) -> None:
        await self._http.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
