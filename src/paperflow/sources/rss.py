"""RSS feed parser for journals."""

from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import feedparser
import httpx
from rich.console import Console

from ..models import Article

console = Console()


class RSSFetcher:
    """Fetch articles from RSS/Atom feeds."""

    def __init__(self, timeout: int = 30):
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)

    def fetch_articles(
        self,
        rss_url: str,
        issn: str,
        journal_name: Optional[str] = None,
        days: int = 7,
    ) -> list[Article]:
        """
        Fetch recent articles from an RSS feed.

        Args:
            rss_url: URL of the RSS/Atom feed
            issn: Journal ISSN
            journal_name: Journal name
            days: Number of days to look back

        Returns:
            List of Article objects
        """
        try:
            response = self.client.get(rss_url)
            response.raise_for_status()

            feed = feedparser.parse(response.text)
            articles = []

            cutoff = datetime.now().timestamp() - (days * 86400)

            for entry in feed.entries:
                # Check publication date
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    pub_timestamp = datetime(*published[:6]).timestamp()
                    if pub_timestamp < cutoff:
                        continue

                article = self._parse_entry(entry, issn, journal_name)
                if article:
                    articles.append(article)

            console.print(f"[green]Found {len(articles)} articles from RSS[/green]")
            return articles

        except Exception as e:
            console.print(f"[red]RSS fetch error: {e}[/red]")
            return []

    def _parse_entry(
        self, entry: dict, issn: str, journal_name: Optional[str]
    ) -> Optional[Article]:
        """Parse an RSS entry into an Article."""
        try:
            # Title
            title = entry.get("title")
            if not title:
                return None

            # Abstract/Summary
            abstract = entry.get("summary") or entry.get("description")
            if abstract:
                # Clean HTML
                abstract = self._clean_html(abstract)

            # Authors
            authors = []
            author_data = entry.get("authors", [])
            for author in author_data:
                name = author.get("name", "")
                if name:
                    authors.append(name)

            if not authors and entry.get("author"):
                authors = [entry.get("author")]

            # DOI
            doi = None
            # Try to extract DOI from various places
            if "prism_doi" in entry:
                doi = entry.prism_doi
            elif "dc_identifier" in entry:
                ident = entry.dc_identifier
                if ident.startswith("doi:"):
                    doi = ident[4:]

            # Try link for DOI
            link = entry.get("link", "")
            if not doi and "doi.org/" in link:
                doi = link.split("doi.org/")[-1]

            # URL
            url = link or entry.get("guid", "")

            # PDF URL
            pdf_url = None
            links = entry.get("links", [])
            for l in links:
                if l.get("type") == "application/pdf":
                    pdf_url = l.get("href")
                    break
                elif "pdf" in l.get("href", "").lower():
                    pdf_url = l.get("href")
                    break

            # Publication date
            published_date = None
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                from datetime import date

                published_date = date(published[0], published[1], published[2])

            return Article(
                title=title,
                abstract=abstract,
                authors=authors,
                affiliations=[],  # RSS usually doesn't have affiliations
                doi=doi,
                url=url,
                pdf_url=pdf_url,
                published_date=published_date,
                journal_issn=issn,
                journal_name=journal_name,
                source="rss",
            )

        except Exception as e:
            console.print(f"[yellow]Error parsing RSS entry: {e}[/yellow]")
            return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean text."""
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def close(self):
        """Close the HTTP client."""
        self.client.close()


# Common RSS feed patterns for publishers
PUBLISHER_RSS_PATTERNS = {
    "springer": "https://link.springer.com/search.rss?journal={issn}",
    "elsevier": "https://rss.sciencedirect.com/publication/science/{issn}",
    "wiley": "https://onlinelibrary.wiley.com/rss/journal/{issn}",
    "ieee": "https://ieeexplore.ieee.org/rss/{issn}",
    "nature": "https://www.nature.com/{journal_code}/rss/current",
}


def get_rss_url(issn: str, publisher: Optional[str] = None) -> Optional[str]:
    """
    Try to construct an RSS URL for a journal.

    Args:
        issn: Journal ISSN
        publisher: Publisher name

    Returns:
        RSS URL or None
    """
    if publisher:
        publisher_lower = publisher.lower()
        for key, pattern in PUBLISHER_RSS_PATTERNS.items():
            if key in publisher_lower:
                return pattern.format(issn=issn)

    return None
