from typing import List, Optional
from pydantic import BaseModel, Field


class OCRRequest(BaseModel):
    images: List[str]
    lang: List[str]


class Message(BaseModel):
    message: str


class OCRResponse(BaseModel):
    texts: List[str]
    errors: Optional[List[Message]]
    warnings: Optional[List[Message]]
