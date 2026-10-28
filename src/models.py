from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class Place:
    """Data model representing a scraped place on Neshan Maps"""
    name: str = ""
    category: str = ""
    address: str = ""
    phone_number: str = ""
    website: str = ""
    opening_hours_today: str = ""
    rating: str = ""
    reviews_count: str = ""
    latitude: str = ""
    longitude: str = ""
    neshan_url: str = ""
    description: str = ""
    photo_count: int = 0
    photo_paths: str = ""

@dataclass
class BoundingBox:
    """Represents a selected bounding box on the map"""
    left: float = 0.0
    top: float = 0.0
    width: float = 0.0
    height: float = 0.0
    center_x: float = 0.0
    center_y: float = 0.0

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional["BoundingBox"]:
        if not data:
            return None
        return cls(
            left=float(data.get("left", 0)),
            top=float(data.get("top", 0)),
            width=float(data.get("width", 0)),
            height=float(data.get("height", 0)),
            center_x=float(data.get("centerX", 0)),
            center_y=float(data.get("centerY", 0))
        )

@dataclass
class ScrapeOptions:
    """Configuration options for a scraping session"""
    query: str = "آرایشگاه"
    limit: int = 20
    ask_confirm: bool = True
    download_photos: bool = True
    delay_mode: str = "medium"
    output_name: str = "neshan_export"
    output_format: str = "csv"
    box: Optional[BoundingBox] = None
