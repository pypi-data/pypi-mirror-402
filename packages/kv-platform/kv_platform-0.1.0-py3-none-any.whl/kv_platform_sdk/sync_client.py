from kv_platform_sdk._http.sync import SyncHTTPClient
from kv_platform_sdk.resources.faq_generator import FAQGeneratorResource
from kv_platform_sdk.resources.documents import DocumentsResource
from kv_platform_sdk.resources.k_search import KnowledgeSearchResource
from kv_platform_sdk.resources.data_extractor import DataExtractorResource
from kv_platform_sdk.resources.timeline_builder import TimelineBuilderResource
from kv_platform_sdk.resources.generate_draft import DraftGenerator
from kv_platform_sdk.resources.form_filler import FormFillerResource
from kv_platform_sdk.resources.questionnarie_filler import QuestionnaireGenerateResource
from kv_platform_sdk.resources.comparison import FormatComparisonResource
from kv_platform_sdk.resources.text_summarizer import TextSummarizerResource


class Client:
    def __init__(
        self,
        access_key: str,
        base_url: str = "https://api.k-v.ai",
        timeout: float = 1000.0,
    ):
        self._http = SyncHTTPClient(base_url, access_key, timeout)
        self.faq_generator = FAQGeneratorResource(self._http)
        self.documents = DocumentsResource(self._http)
        self.k_search = KnowledgeSearchResource(self._http)
        self.data_extractor = DataExtractorResource(self._http)
        self.timeline_builder = TimelineBuilderResource(self._http)
        self.draft_generate = DraftGenerator(self._http)
        self.form_filler = FormFillerResource(self._http)
        self.questionnaire_filler = QuestionnaireGenerateResource(self._http)
        self.comparison = FormatComparisonResource(self._http)
        self.text_summarizer = TextSummarizerResource(self._http)

    def close(self) -> None:
        self._http.close()
