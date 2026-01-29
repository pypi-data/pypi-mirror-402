from pydantic import BaseModel
from typing import Optional

class ModelData(BaseModel):
    model_name: str
    api_key: Optional[str] = None
