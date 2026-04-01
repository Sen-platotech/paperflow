"""Journal data model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Journal(BaseModel):
    """Represents an academic journal."""

    name: str = Field(..., description="Journal name")
    issn: str = Field(..., description="ISSN identifier")
    publisher: Optional[str] = Field(None, description="Publisher name")
    sjr_score: Optional[float] = Field(None, description="Scimago Journal Rank score")
    h_index: Optional[int] = Field(None, description="H-index")
    category: Optional[str] = Field(None, description="Subject category")
    rss_url: Optional[str] = Field(None, description="RSS feed URL")
    rank: Optional[int] = Field(None, description="Rank in category")
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Nature Machine Intelligence",
                    "issn": "2522-5839",
                    "publisher": "Springer Nature",
                    "sjr_score": 15.2,
                    "h_index": 85,
                    "category": "Artificial Intelligence",
                    "rank": 1,
                }
            ]
        }
    }


class JournalCreate(BaseModel):
    """Model for creating a new journal subscription."""

    issn: str
    name: Optional[str] = None
