"""Article data model."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class Article(BaseModel):
    """Represents an academic article."""

    id: Optional[int] = None
    title: str = Field(..., description="Article title (original)")
    title_zh: Optional[str] = Field(None, description="Translated Chinese title")
    abstract: Optional[str] = Field(None, description="Abstract (original)")
    abstract_zh: Optional[str] = Field(None, description="Translated Chinese abstract")
    authors: list[str] = Field(default_factory=list, description="Author names")
    affiliations: list[str] = Field(default_factory=list, description="Author affiliations")
    doi: Optional[str] = Field(None, description="DOI identifier")
    url: Optional[str] = Field(None, description="Article URL")
    pdf_url: Optional[str] = Field(None, description="PDF URL")
    published_date: Optional[date] = Field(None, description="Publication date")
    journal_issn: str = Field(..., description="ISSN of the journal")
    journal_name: Optional[str] = Field(None, description="Journal name")
    source: str = Field(default="unknown", description="Data source (crossref, rss, etc.)")
    created_at: datetime = Field(default_factory=datetime.now)
    translated_at: Optional[datetime] = Field(None, description="Translation timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "A Unified Framework for Large Language Model Reasoning",
                    "title_zh": "大语言模型推理的统一框架",
                    "abstract": "This paper proposes...",
                    "abstract_zh": "本文提出了...",
                    "authors": ["Wei Chen", "Li Zhang"],
                    "affiliations": ["Tsinghua University"],
                    "doi": "10.1234/example",
                    "published_date": "2024-01-15",
                    "journal_issn": "2522-5839",
                    "journal_name": "Nature Machine Intelligence",
                }
            ]
        }
    }


class ArticleWithJournal(Article):
    """Article with journal information included."""

    journal: Optional["Journal"] = None


# Import Journal for forward reference
from .journal import Journal  # noqa: E402

ArticleWithJournal.model_rebuild()
