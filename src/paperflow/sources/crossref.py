"""CrossRef API data source for fetching articles."""

from datetime import date, datetime, timedelta
from typing import Optional

import httpx
from rich.console import Console

from ..models import Article

console = Console()

CROSSREF_API = "https://api.crossref.org"


class CrossRefFetcher:
    """Fetch articles from CrossRef API."""

    def __init__(self, timeout: int = 30, delay: float = 1.0):
        self.client = httpx.Client(timeout=timeout)
        self.delay = delay
        self.headers = {
            "User-Agent": "Paperflow/0.1 (mailto:example@example.com)",
        }

    def fetch_articles_by_issn(
        self,
        issn: str,
        days: int = 7,
        journal_name: Optional[str] = None,
    ) -> list[Article]:
        """
        Fetch recent articles from a journal by ISSN.

        Args:
            issn: Journal ISSN
            days: Number of days to look back
            journal_name: Journal name (optional)

        Returns:
            List of Article objects
        """
        from_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        until_date = date.today().strftime("%Y-%m-%d")

        url = f"{CROSSREF_API}/works"
        params = {
            "filter": f"issn:{issn},from-pub-date:{from_date},until-pub-date:{until_date}",
            "select": "DOI,title,abstract,author,published-print,published-online,URL,link",
            "rows": 100,
            "sort": "published",
            "order": "desc",
        }

        try:
            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            articles = []
            items = data.get("message", {}).get("items", [])

            for item in items:
                article = self._parse_article(item, issn, journal_name)
                if article:
                    articles.append(article)

            console.print(f"[green]Found {len(articles)} articles from CrossRef[/green]")
            return articles

        except httpx.HTTPError as e:
            console.print(f"[red]CrossRef API error: {e}[/red]")
            return []

    def _parse_article(
        self, item: dict, issn: str, journal_name: Optional[str]
    ) -> Optional[Article]:
        """Parse an article from CrossRef response."""
        try:
            # Title
            titles = item.get("title", [])
            title = titles[0] if titles else None
            if not title:
                return None

            # Abstract (CrossRef rarely has abstracts)
            abstract = item.get("abstract")

            # Authors
            authors = []
            author_data = item.get("author", [])
            for author in author_data:
                given = author.get("given", "")
                family = author.get("family", "")
                if given or family:
                    authors.append(f"{given} {family}".strip())

            # Affiliations
            affiliations = []
            for author in author_data:
                aff = author.get("affiliation", [])
                for a in aff:
                    name = a.get("name", "")
                    if name and name not in affiliations:
                        affiliations.append(name)

            # DOI
            doi = item.get("DOI")

            # URL
            url = item.get("URL")

            # PDF URL
            pdf_url = None
            links = item.get("link", [])
            for link in links:
                if link.get("content-type") == "application/pdf":
                    pdf_url = link.get("URL")
                    break

            # Publication date
            published = item.get("published-print") or item.get("published-online")
            published_date = None
            if published:
                date_parts = published.get("date-parts", [[]])
                if date_parts and date_parts[0]:
                    parts = date_parts[0]
                    if len(parts) >= 3:
                        published_date = date(parts[0], parts[1], parts[2])
                    elif len(parts) >= 2:
                        published_date = date(parts[0], parts[1], 1)
                    elif len(parts) >= 1:
                        published_date = date(parts[0], 1, 1)

            return Article(
                title=title,
                abstract=abstract,
                authors=authors,
                affiliations=affiliations,
                doi=doi,
                url=url,
                pdf_url=pdf_url,
                published_date=published_date,
                journal_issn=issn,
                journal_name=journal_name,
                source="crossref",
            )

        except Exception as e:
            console.print(f"[yellow]Error parsing article: {e}[/yellow]")
            return None

    def get_journal_name(self, issn: str) -> Optional[str]:
        """Get journal name from CrossRef."""
        url = f"{CROSSREF_API}/journals/{issn}"
        try:
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("title")
        except Exception:
            return None

    def close(self):
        """Close the HTTP client."""
        self.client.close()
