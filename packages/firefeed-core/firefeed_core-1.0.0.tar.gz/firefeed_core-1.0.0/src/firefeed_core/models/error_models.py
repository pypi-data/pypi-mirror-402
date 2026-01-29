# models/error_models.py - Error response models
from pydantic import BaseModel


# Model for error response (optional, but useful)
class HTTPError(BaseModel):
    detail: str