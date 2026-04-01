"""Scimago Journal Rank (SJR) data source."""

import re
from typing import Optional
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

from ..models import Journal

console = Console()

SJR_BASE_URL = "https://www.scimagojr.com"


class SJRSearcher:
    """Search for journals on Scimago Journal Rank."""

    def __init__(self, timeout: int = 30):
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def search_by_category(self, category: str, top_n: int = 20) -> list[Journal]:
        """
        Search for top journals in a category.

        Args:
            category: Category name (e.g., "Artificial Intelligence")
            top_n: Number of top journals to return

        Returns:
            List of Journal objects
        """
        console.print(f"[cyan]Searching SJR for category: {category}[/cyan]")

        # First, search for the category
        search_url = f"{SJR_BASE_URL}/journalsearch.php?q={quote(category)}"
        try:
            response = self.client.get(search_url, headers=self.headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                console.print("[yellow]SJR blocked the request. Using preset journals instead.[/yellow]")
                return self._get_preset_journals(category, top_n)
            raise

        soup = BeautifulSoup(response.text, "lxml")

        # Find journal results
        journals = self._parse_search_results(soup, top_n)

        console.print(f"[green]Found {len(journals)} journals[/green]")
        return journals

    def search_by_name(self, name: str, limit: int = 10) -> list[Journal]:
        """
        Search for journals by name.

        Args:
            name: Journal name to search
            limit: Maximum results

        Returns:
            List of Journal objects
        """
        search_url = f"{SJR_BASE_URL}/journalsearch.php?q={quote(name)}"
        response = self.client.get(search_url, headers=self.headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        return self._parse_search_results(soup, limit)

    def get_journal_details(self, journal_id: str) -> Optional[Journal]:
        """
        Get detailed information for a specific journal.

        Args:
            journal_id: SJR journal ID

        Returns:
            Journal object with full details
        """
        url = f"{SJR_BASE_URL}/journalsearch.php?q={journal_id}&tip=sid"
        response = self.client.get(url, headers=self.headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        return self._parse_journal_detail(soup)

    def _parse_search_results(self, soup: BeautifulSoup, limit: int) -> list[Journal]:
        """Parse search results from SJR."""
        journals = []

        # SJR uses different layouts, try multiple selectors
        results = soup.select("div.search_results a") or soup.select("table tr td a")

        for i, result in enumerate(results[:limit]):
            try:
                # Get journal name
                name = result.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                # Get link to journal page
                href = result.get("href", "")
                journal_id = ""
                if "sid=" in href:
                    journal_id = href.split("sid=")[-1].split("&")[0]

                # Try to extract ISSN from the page
                issn = self._extract_issn_from_result(result)

                if issn:
                    journals.append(
                        Journal(
                            name=name,
                            issn=issn,
                            rank=i + 1,
                        )
                    )
            except Exception as e:
                console.print(f"[yellow]Error parsing result: {e}[/yellow]")
                continue

        return journals

    def _extract_issn_from_result(self, element) -> Optional[str]:
        """Extract ISSN from a search result element."""
        # Try to find ISSN in nearby text
        parent = element.find_parent("tr") or element.find_parent("div")
        if parent:
            text = parent.get_text()
            issn_match = re.search(r"\b(\d{4}-\d{3}[\dX])\b", text)
            if issn_match:
                return issn_match.group(1)
        return None

    def _parse_journal_detail(self, soup: BeautifulSoup) -> Optional[Journal]:
        """Parse journal detail page."""
        try:
            # Extract journal name
            name_elem = soup.select_one("h1.journalname") or soup.select_one("h1")
            name = name_elem.get_text(strip=True) if name_elem else ""

            # Extract ISSN
            issn = None
            issn_elem = soup.select_one("span.issn") or soup.find(string=re.compile(r"ISSN"))
            if issn_elem:
                if hasattr(issn_elem, "get_text"):
                    text = issn_elem.get_text()
                else:
                    text = str(issn_elem)
                issn_match = re.search(r"\b(\d{4}-\d{3}[\dX])\b", text)
                if issn_match:
                    issn = issn_match.group(1)

            # Extract SJR score
            sjr_score = None
            sjr_elem = soup.select_one("span.sjr") or soup.find(string=re.compile(r"SJR"))
            if sjr_elem:
                text = sjr_elem.get_text() if hasattr(sjr_elem, "get_text") else str(sjr_elem)
                sjr_match = re.search(r"[\d.]+", text)
                if sjr_match:
                    sjr_score = float(sjr_match.group())

            # Extract H-index
            h_index = None
            h_elem = soup.find(string=re.compile(r"H.index"))
            if h_elem:
                parent = h_elem.find_parent()
                if parent:
                    h_match = re.search(r"\d+", parent.get_text())
                    if h_match:
                        h_index = int(h_match.group())

            # Extract publisher
            publisher = None
            pub_elem = soup.select_one("span.publisher") or soup.find(string=re.compile(r"Publisher"))
            if pub_elem:
                parent = pub_elem.find_parent()
                if parent:
                    publisher = parent.get_text(strip=True).replace("Publisher:", "").strip()

            if name and issn:
                return Journal(
                    name=name,
                    issn=issn,
                    sjr_score=sjr_score,
                    h_index=h_index,
                    publisher=publisher,
                )

        except Exception as e:
            console.print(f"[red]Error parsing journal detail: {e}[/red]")

        return None

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def _get_preset_journals(self, category: str, top_n: int) -> list[Journal]:
        """Return preset journals for common categories."""
        category_lower = category.lower()

        # Preset journals for common categories
        presets = {
            "artificial intelligence": [
                Journal(name="Nature Machine Intelligence", issn="2522-5839", publisher="Springer Nature", sjr_score=15.2, h_index=85, rank=1),
                Journal(name="Journal of Machine Learning Research", issn="1532-4435", publisher="JMLR", sjr_score=6.8, h_index=145, rank=2),
                Journal(name="IEEE Transactions on Pattern Analysis and Machine Intelligence", issn="0162-8828", publisher="IEEE", sjr_score=5.9, h_index=289, rank=3),
                Journal(name="Artificial Intelligence", issn="0004-3702", publisher="Elsevier", sjr_score=4.5, h_index=132, rank=4),
                Journal(name="Machine Learning", issn="0885-6125", publisher="Springer", sjr_score=3.2, h_index=118, rank=5),
                Journal(name="Neural Networks", issn="0893-6080", publisher="Elsevier", sjr_score=2.8, h_index=145, rank=6),
                Journal(name="International Journal of Computer Vision", issn="0920-5691", publisher="Springer", sjr_score=4.1, h_index=185, rank=7),
                Journal(name="ACM Transactions on Intelligent Systems and Technology", issn="2157-6904", publisher="ACM", sjr_score=3.5, h_index=72, rank=8),
                Journal(name="Pattern Recognition", issn="0031-3203", publisher="Elsevier", sjr_score=2.9, h_index=165, rank=9),
                Journal(name="Expert Systems with Applications", issn="0957-4174", publisher="Elsevier", sjr_score=1.8, h_index=175, rank=10),
            ],
            "machine learning": [
                Journal(name="Journal of Machine Learning Research", issn="1532-4435", publisher="JMLR", sjr_score=6.8, h_index=145, rank=1),
                Journal(name="Nature Machine Intelligence", issn="2522-5839", publisher="Springer Nature", sjr_score=15.2, h_index=85, rank=2),
                Journal(name="Machine Learning", issn="0885-6125", publisher="Springer", sjr_score=3.2, h_index=118, rank=3),
                Journal(name="IEEE Transactions on Neural Networks and Learning Systems", issn="2162-237X", publisher="IEEE", sjr_score=4.2, h_index=125, rank=4),
                Journal(name="Neurocomputing", issn="0925-2312", publisher="Elsevier", sjr_score=1.9, h_index=155, rank=5),
            ],
            "natural language processing": [
                Journal(name="Computational Linguistics", issn="0891-2017", publisher="MIT Press", sjr_score=4.5, h_index=95, rank=1),
                Journal(name="Transactions of the Association for Computational Linguistics", issn="2307-387X", publisher="MIT Press", sjr_score=3.8, h_index=52, rank=2),
                Journal(name="Natural Language Engineering", issn="1350-3177", publisher="Cambridge University Press", sjr_score=1.5, h_index=65, rank=3),
                Journal(name="Journal of Natural Language Processing", issn="2185-8234", publisher="INLP", sjr_score=0.8, h_index=28, rank=4),
            ],
            "computer vision": [
                Journal(name="International Journal of Computer Vision", issn="0920-5691", publisher="Springer", sjr_score=4.1, h_index=185, rank=1),
                Journal(name="IEEE Transactions on Pattern Analysis and Machine Intelligence", issn="0162-8828", publisher="IEEE", sjr_score=5.9, h_index=289, rank=2),
                Journal(name="Pattern Recognition", issn="0031-3203", publisher="Elsevier", sjr_score=2.9, h_index=165, rank=3),
                Journal(name="Computer Vision and Image Understanding", issn="1077-3142", publisher="Elsevier", sjr_score=1.8, h_index=115, rank=4),
                Journal(name="Image and Vision Computing", issn="0262-8856", publisher="Elsevier", sjr_score=1.2, h_index=98, rank=5),
            ],
        }

        # Find matching category
        for key, journals in presets.items():
            if key in category_lower or category_lower in key:
                return journals[:top_n]

        # Default to AI journals if no match
        console.print(f"[yellow]No preset for '{category}', using AI journals[/yellow]")
        return presets["artificial intelligence"][:top_n]


def display_journals_table(journals: list[Journal]) -> None:
    """Display journals in a rich table."""
    table = Table(title="Journals")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Journal Name", style="green")
    table.add_column("ISSN", style="yellow")
    table.add_column("SJR", justify="right")
    table.add_column("H-index", justify="right")

    for i, j in enumerate(journals, 1):
        table.add_row(
            str(i),
            j.name[:50] + "..." if len(j.name) > 50 else j.name,
            j.issn,
            f"{j.sjr_score:.2f}" if j.sjr_score else "-",
            str(j.h_index) if j.h_index else "-",
        )

    console.print(table)
