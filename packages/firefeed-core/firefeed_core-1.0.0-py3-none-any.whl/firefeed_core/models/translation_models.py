# models/translation_models.py - Translation data models
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PreparedRSSItem:
    """Structure for storing prepared RSS item."""

    original_data: Dict[str, Any]
    translations: Dict[str, Dict[str, str]]
    image_filename: Optional[str]
    video_filename: Optional[str]
    feed_id: int