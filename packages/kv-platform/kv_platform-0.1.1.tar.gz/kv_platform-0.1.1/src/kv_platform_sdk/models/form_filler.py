from typing import Optional, List, Any
from pydantic import BaseModel
from .model_data import ModelData

class UserValue(BaseModel):
    source: Optional[str] = None
    possible_value: Optional[Any] = None


class FormField(BaseModel):
    label: str
    type: str
    example: Optional[str] = None
    options: Optional[List[Any]] = None
    user_value: UserValue


class FormGenerateRequest(BaseModel):
    doc_process_id: str
    model_data: ModelData

class UserValue(BaseModel):
    source: Optional[str] = None
    possible_value: Optional[Any] = None
    doc_hash: Optional[List[str]] = None


class PossibleValue(BaseModel):
    source: str
    possible_value: Any
    doc_hash: List[str]


class UnfilledFormField(BaseModel):
    label: str
    type: str
    example: Optional[str] = None
    options: Optional[List[Any]] = None
    user_value: UserValue


class FilledFormField(UnfilledFormField):
    possible_values: Optional[List[PossibleValue]] = None


class FormFillRequest(BaseModel):
    source_doc_process_ids: List[str]
    model_data: ModelData
    unfilled_form_data: List[UnfilledFormField]