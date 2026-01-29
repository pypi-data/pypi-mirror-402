# models/media_models.py - Media data models
from pydantic import BaseModel
from typing import Optional


class LanguageItem(BaseModel):
    language: str