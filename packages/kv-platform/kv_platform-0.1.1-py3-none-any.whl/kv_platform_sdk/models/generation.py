from typing import Optional, List, Any
from pydantic import BaseModel


from .model_data import ModelData



class DraftGenerateTemplateRequest(BaseModel):
    doc_process_id: str
    model_data: ModelData


class DraftTemplateField(BaseModel):
    category: str
    label: str
    type: str
    description: Optional[str]
    current_value: List[Any]
    options: Optional[List[Any]]
    page_no: Optional[int]
    user_value: Optional[Any]


class TokenUsage(BaseModel):
    input: int
    output: int
    total: int


class DraftGenerateTemplateData(BaseModel):
    form: List[DraftTemplateField]
    tokens: TokenUsage


class FilledTemplateVariable(BaseModel):
    category: str
    label: str
    type: str
    description: Optional[str]
    current_value: List[Any]
    options: Optional[List[Any]]
    page_no: Optional[int]
    user_value: Optional[Any]


class DraftCreateDraftRequest(BaseModel):
    template_doc_process_id: str
    model_data: ModelData
    filled_template_variables: List[FilledTemplateVariable]

