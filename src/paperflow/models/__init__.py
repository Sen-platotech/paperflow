"""Data models for paperflow."""

from .article import Article, ArticleWithJournal
from .journal import Journal, JournalCreate

__all__ = ["Journal", "JournalCreate", "Article", "ArticleWithJournal"]
