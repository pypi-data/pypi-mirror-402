# models/category_models.py - Category data models
from pydantic import BaseModel
from typing import List, Optional


class CategoryItem(BaseModel):
    id: int
    name: str