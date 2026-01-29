from typing import List, Optional
from pydantic import BaseModel
from .model_data import ModelData



class DataExtractorRequest(BaseModel):
    doc_process_ids: List[str]
    entity_list: Optional[List[str]] = None
    model_data: ModelData


class DataExtractorResponse(BaseModel):
    data: dict
    message: str


class TimelineBuilderRequest(BaseModel):
    doc_process_ids: List[str]
    domain: str  
    model_data: ModelData


class TimelineBuilderResponse(BaseModel):
    data: dict
    message: str