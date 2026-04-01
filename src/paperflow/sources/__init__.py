"""Data sources for paperflow."""

from .crossref import CrossRefFetcher
from .rss import RSSFetcher, get_rss_url
from .sjr import JournalSearcher, SJRSearcher, display_journals_table

__all__ = [
    "JournalSearcher",
    "SJRSearcher",
    "display_journals_table",
    "CrossRefFetcher",
    "RSSFetcher",
    "get_rss_url",
]
