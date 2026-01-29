from typing import List, Optional
from pydantic import BaseModel


class DocumentItem(BaseModel):

    created_at: str
    doc_name: str
    status: str
    doc_process_id: str
    transactions_utilised: int


class ListDocumentsResponse(BaseModel):
    documents: List[DocumentItem]


class DeleteDocs(BaseModel):
    doc_process_ids: List[str]


class ProcessDocResponseData(BaseModel):
    doc_process_id: str
    transactions_utilised: int


class ProcessDocResponse(BaseModel):
    data: ProcessDocResponseData
    message: str


class S3UploadRequest(BaseModel):
    s3_uri: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
