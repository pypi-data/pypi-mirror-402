from typing import Optional, List, Any
from pydantic import BaseModel
from .model_data import ModelData


class UserValue(BaseModel):
    source: Optional[str] = None
    possible_value: Optional[Any] = None
    page_numbers: Optional[List[str]] = None
    doc_hash: Optional[List[str]] = None



class QuestionnaireItem(BaseModel):
    question: str
    type: str  
    options: Optional[List[str]] = None
    example: Optional[str] = None
    user_value: UserValue


class QuestionnaireGenerateRequest(BaseModel):
    doc_process_id: str
    model_data: ModelData




class QuestionnaireItem(BaseModel):
    question: str
    type: str
    options: Optional[List[str]] = None
    example: Optional[str] = None
    user_value: UserValue


class QuestionnaireFillRequest(BaseModel):
    source_doc_process_ids: List[str]
    model_data: ModelData
    unfilled_questionnaire_data: List[QuestionnaireItem]


class PossibleAnswer(BaseModel):
    source: str
    possible_value: Any
    page_numbers: List[str]
    doc_hash: List[str]