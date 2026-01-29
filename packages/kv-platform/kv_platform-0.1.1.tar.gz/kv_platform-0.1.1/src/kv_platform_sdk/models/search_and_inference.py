from typing import List, Optional

from pydantic import BaseModel, Field


from .model_data import ModelData


class FAQGeneratorRequest(BaseModel):
    doc_process_ids: List[str]
    question_count: int
    focus_areas: Optional[List[str]] = None
    model_data: Optional[ModelData] = None


class FAQItem(BaseModel):
    question: str
    answer: str
    focus_area: Optional[str]
    page_numbers: List[str]
    rank: int
    source: str
    doc_hash: List[str]


class FAQGeneratorResponse(BaseModel):
    questions_answers: List[FAQItem]
    is_sufficient: bool


class KnowledgeSearchRequest(BaseModel):
    doc_process_ids: List[str]
    question: str
    context: Optional[str] = "medium"
    model_data: ModelData


class KnowledgeSource(BaseModel):
    content: str
    score: float
    filename: str
    doc_hash: str
    page_number: int


class KnowledgeSearchData(BaseModel):
    answer: str
    sources: List[KnowledgeSource]


class TextSummarizerRequest(BaseModel):
    doc_process_ids: List[str] = Field(..., min_items=1)
    focus_areas: Optional[List[str]] = []
    compression_ratio: Optional[int] = Field(default=30, ge=20, le=80)
    type: str = Field(..., pattern="^(abstractive|extractive)$")
    model_data: Optional[ModelData] = None


class TextSummarizerResponse(BaseModel):
    data: dict
    message: str
