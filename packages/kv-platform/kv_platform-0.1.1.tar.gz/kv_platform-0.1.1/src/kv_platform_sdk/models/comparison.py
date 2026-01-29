from typing import Dict
from pydantic import BaseModel


class CheckpointsToCompare(BaseModel):
    page_margins: bool = True
    links: bool = False
    font_sizes: bool = False


class FormatComparisonRequest(BaseModel):
    doc_1_process_id: str
    doc_2_process_id: str
    checkpoints_to_compare: CheckpointsToCompare

class ContentComparisonRequest(BaseModel):
    doc_1_process_id: str
    doc_2_process_id: str