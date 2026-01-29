# models/source_models.py - Source data models
from pydantic import BaseModel
from typing import Optional


class SourceItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None