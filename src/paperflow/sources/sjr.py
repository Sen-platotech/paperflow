"""Journal search from multiple sources."""

import re
from typing import Optional
from urllib.parse import quote

import httpx
from rich.console import Console
from rich.table import Table

from ..models import Journal

console = Console()

# CrossRef API for journal search
CROSSREF_API = "https://api.crossref.org"


class JournalSearcher:
    """Search for journals using multiple sources."""

    def __init__(self, timeout: int = 30):
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
        self.headers = {
            "User-Agent": "Paperflow/0.1 (mailto:paperflow@example.com)",
        }

    def search_by_topic(self, topic: str, top_n: int = 20) -> list[Journal]:
        """
        Search for journals by topic/keyword.

        Priority: Preset top journals > CrossRef search

        Args:
            topic: Topic or keyword (e.g., "Artificial Intelligence", "Quantum Physics")
            top_n: Number of results

        Returns:
            List of Journal objects
        """
        console.print(f"[cyan]Searching journals for: {topic}[/cyan]")

        # Check preset first for known categories
        preset = self._get_preset_journals(topic, top_n)
        if preset:
            console.print(f"[green]Found {len(preset)} top journals from database[/green]")
            return preset[:top_n]

        # Try CrossRef for unknown topics
        journals = self._search_crossref(topic, top_n)

        if not journals:
            # Fallback to AI journals
            console.print("[yellow]No journals found, showing AI journals as reference...[/yellow]")
            journals = self._get_default_journals(top_n)

        console.print(f"[green]Found {len(journals)} journals[/green]")
        return journals[:top_n]

    def _get_default_journals(self, top_n: int) -> list[Journal]:
        """Return default AI journals when no match found."""
        return [
            Journal(name="Nature Machine Intelligence", issn="2522-5839", publisher="Springer Nature"),
            Journal(name="Journal of Machine Learning Research", issn="1532-4435", publisher="JMLR"),
            Journal(name="IEEE TPAMI", issn="0162-8828", publisher="IEEE"),
        ][:top_n]

    def _search_crossref(self, query: str, limit: int) -> list[Journal]:
        """Search journals via CrossRef API."""
        try:
            # CrossRef journals endpoint
            url = f"{CROSSREF_API}/journals"
            params = {
                "query": query,
                "rows": limit,
            }

            response = self.client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            journals = []
            items = data.get("message", {}).get("items", [])

            for i, item in enumerate(items):
                try:
                    # Extract journal info
                    title = item.get("title")
                    if not title:
                        continue

                    # Get ISSN
                    issn_list = item.get("ISSN", [])
                    issn = issn_list[0] if issn_list else None

                    if not issn:
                        continue

                    # Get publisher
                    publisher = item.get("publisher")

                    journal = Journal(
                        name=title,
                        issn=issn,
                        publisher=publisher,
                        rank=i + 1,
                    )
                    journals.append(journal)

                except Exception as e:
                    continue

            return journals

        except Exception as e:
            console.print(f"[yellow]CrossRef search error: {e}[/yellow]")
            return []

    def search_by_name(self, name: str, limit: int = 10) -> list[Journal]:
        """
        Search for a specific journal by name.

        Args:
            name: Journal name to search
            limit: Maximum results

        Returns:
            List of Journal objects
        """
        return self._search_crossref(name, limit)

    def get_journal_info(self, issn: str) -> Optional[Journal]:
        """
        Get journal information by ISSN.

        Args:
            issn: Journal ISSN

        Returns:
            Journal object or None
        """
        try:
            url = f"{CROSSREF_API}/journals/{issn}"
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            item = data.get("message", {})
            title = item.get("title")
            publisher = item.get("publisher")

            if title:
                return Journal(
                    name=title,
                    issn=issn,
                    publisher=publisher,
                )

        except Exception as e:
            console.print(f"[yellow]Error fetching journal info: {e}[/yellow]")

        return None

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def _get_preset_journals(self, category: str, top_n: int) -> list[Journal]:
        """Return preset journals for common categories as fallback."""
        category_lower = category.lower()

        # Expanded preset journals for various categories
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
                Journal(name="IEEE Transactions on Cybernetics", issn="2168-2267", publisher="IEEE", sjr_score=3.5, h_index=145, rank=6),
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
            "robotics": [
                Journal(name="International Journal of Robotics Research", issn="0278-3649", publisher="SAGE", sjr_score=3.8, h_index=165, rank=1),
                Journal(name="IEEE Transactions on Robotics", issn="1552-3098", publisher="IEEE", sjr_score=3.5, h_index=145, rank=2),
                Journal(name="Robotics and Autonomous Systems", issn="0921-8890", publisher="Elsevier", sjr_score=1.8, h_index=98, rank=3),
                Journal(name="IEEE Robotics and Automation Letters", issn="2377-3766", publisher="IEEE", sjr_score=2.8, h_index=85, rank=4),
            ],
            "bioinformatics": [
                Journal(name="Bioinformatics", issn="1367-4803", publisher="Oxford University Press", sjr_score=4.2, h_index=285, rank=1),
                Journal(name="BMC Bioinformatics", issn="1471-2105", publisher="BMC", sjr_score=1.5, h_index=125, rank=2),
                Journal(name="Journal of Computational Biology", issn="1066-5277", publisher="Mary Ann Liebert", sjr_score=1.2, h_index=85, rank=3),
                Journal(name="PLOS Computational Biology", issn="1553-7358", publisher="PLOS", sjr_score=3.5, h_index=195, rank=4),
            ],
            "neuroscience": [
                Journal(name="Nature Neuroscience", issn="1097-6256", publisher="Nature Publishing Group", sjr_score=8.5, h_index=325, rank=1),
                Journal(name="Neuron", issn="0896-6273", publisher="Cell Press", sjr_score=7.2, h_index=285, rank=2),
                Journal(name="Journal of Neuroscience", issn="0270-6474", publisher="Society for Neuroscience", sjr_score=3.5, h_index=425, rank=3),
                Journal(name="Trends in Neurosciences", issn="0166-2236", publisher="Elsevier", sjr_score=5.8, h_index=185, rank=4),
            ],
            "quantum": [
                Journal(name="Quantum", issn="2521-327X", publisher="Quantum Open", sjr_score=2.8, h_index=45, rank=1),
                Journal(name="npj Quantum Information", issn="2056-6387", publisher="Nature Publishing Group", sjr_score=3.5, h_index=65, rank=2),
                Journal(name="Quantum Science and Technology", issn="2058-9565", publisher="IOP Publishing", sjr_score=2.5, h_index=42, rank=3),
                Journal(name="Physical Review A", issn="2469-9926", publisher="APS", sjr_score=2.2, h_index=185, rank=4),
            ],
            "climate": [
                Journal(name="Nature Climate Change", issn="1758-678X", publisher="Nature Publishing Group", sjr_score=12.5, h_index=185, rank=1),
                Journal(name="Climatic Change", issn="0165-0009", publisher="Springer", sjr_score=2.8, h_index=145, rank=2),
                Journal(name="Journal of Climate", issn="0894-8755", publisher="American Meteorological Society", sjr_score=3.2, h_index=225, rank=3),
                Journal(name="Global Environmental Change", issn="0959-3780", publisher="Elsevier", sjr_score=5.5, h_index=145, rank=4),
            ],
            "materials science": [
                Journal(name="Nature Materials", issn="1476-1122", publisher="Nature Publishing Group", sjr_score=15.8, h_index=425, rank=1),
                Journal(name="Advanced Materials", issn="0935-9648", publisher="Wiley", sjr_score=8.5, h_index=385, rank=2),
                Journal(name="Materials Science and Engineering: R: Reports", issn="0927-796X", publisher="Elsevier", sjr_score=12.2, h_index=165, rank=3),
                Journal(name="Nano Letters", issn="1530-6984", publisher="ACS", sjr_score=6.8, h_index=325, rank=4),
            ],
            "medicine": [
                Journal(name="New England Journal of Medicine", issn="0028-4793", publisher="Massachusetts Medical Society", sjr_score=18.5, h_index=885, rank=1),
                Journal(name="The Lancet", issn="0140-6736", publisher="Elsevier", sjr_score=17.2, h_index=685, rank=2),
                Journal(name="JAMA", issn="0098-7484", publisher="American Medical Association", sjr_score=14.5, h_index=585, rank=3),
                Journal(name="Nature Medicine", issn="1078-8956", publisher="Nature Publishing Group", sjr_score=12.8, h_index=385, rank=4),
            ],
            "chemistry": [
                Journal(name="Nature Chemistry", issn="1755-4330", publisher="Nature Publishing Group", sjr_score=12.5, h_index=285, rank=1),
                Journal(name="Journal of the American Chemical Society", issn="0002-7863", publisher="ACS", sjr_score=5.8, h_index=525, rank=2),
                Journal(name="Angewandte Chemie", issn="0044-8249", publisher="Wiley", sjr_score=4.5, h_index=385, rank=3),
                Journal(name="Chemical Reviews", issn="0009-2665", publisher="ACS", sjr_score=8.5, h_index=325, rank=4),
            ],
            "physics": [
                Journal(name="Physical Review Letters", issn="0031-9007", publisher="APS", sjr_score=5.5, h_index=585, rank=1),
                Journal(name="Nature Physics", issn="1745-2473", publisher="Nature Publishing Group", sjr_score=8.2, h_index=285, rank=2),
                Journal(name="Reviews of Modern Physics", issn="0034-6861", publisher="APS", sjr_score=15.5, h_index=225, rank=3),
                Journal(name="Physical Review X", issn="2160-3308", publisher="APS", sjr_score=6.5, h_index=125, rank=4),
            ],
            "biology": [
                Journal(name="Nature", issn="0028-0836", publisher="Nature Publishing Group", sjr_score=15.2, h_index=985, rank=1),
                Journal(name="Science", issn="0036-8075", publisher="AAAS", sjr_score=14.8, h_index=885, rank=2),
                Journal(name="Cell", issn="0092-8674", publisher="Cell Press", sjr_score=13.5, h_index=685, rank=3),
                Journal(name="Nature Cell Biology", issn="1465-7392", publisher="Nature Publishing Group", sjr_score=9.5, h_index=285, rank=4),
            ],
            "economics": [
                Journal(name="American Economic Review", issn="0002-8282", publisher="American Economic Association", sjr_score=8.5, h_index=285, rank=1),
                Journal(name="Journal of Economic Literature", issn="0022-0515", publisher="American Economic Association", sjr_score=7.2, h_index=145, rank=2),
                Journal(name="Quarterly Journal of Economics", issn="0033-5533", publisher="Oxford University Press", sjr_score=9.5, h_index=185, rank=3),
                Journal(name="Journal of Political Economy", issn="0022-3808", publisher="University of Chicago Press", sjr_score=6.8, h_index=165, rank=4),
            ],
            "psychology": [
                Journal(name="Annual Review of Psychology", issn="0066-4308", publisher="Annual Reviews", sjr_score=5.5, h_index=285, rank=1),
                Journal(name="Psychological Bulletin", issn="0033-2909", publisher="APA", sjr_score=4.8, h_index=225, rank=2),
                Journal(name="Psychological Review", issn="0033-295X", publisher="APA", sjr_score=4.2, h_index=185, rank=3),
                Journal(name="Trends in Cognitive Sciences", issn="1364-6613", publisher="Elsevier", sjr_score=5.8, h_index=185, rank=4),
            ],
            "sustainability": [
                Journal(name="Nature Sustainability", issn="2398-9629", publisher="Nature Publishing Group", sjr_score=8.5, h_index=85, rank=1),
                Journal(name="Sustainable Development", issn="0968-0802", publisher="Wiley", sjr_score=2.5, h_index=85, rank=2),
                Journal(name="Journal of Cleaner Production", issn="0959-6526", publisher="Elsevier", sjr_score=2.2, h_index=225, rank=3),
            ],
            "data science": [
                Journal(name="Journal of Data Science", issn="1680-743X", publisher="International Chinese Statistical Association", sjr_score=1.2, h_index=25, rank=1),
                Journal(name="EPJ Data Science", issn="2193-1127", publisher="Springer", sjr_score=2.8, h_index=45, rank=2),
                Journal(name="Data Science Journal", issn="1683-1470", publisher="Ubiquity Press", sjr_score=0.8, h_index=28, rank=3),
            ],
        }

        # Find matching category
        for key, journals in presets.items():
            if key in category_lower or category_lower in key:
                return journals[:top_n]

        # Try to find partial match
        for key, journals in presets.items():
            key_words = key.split()
            category_words = category_lower.split()
            if any(word in category_lower for word in key_words) or any(word in key for word in category_words):
                return journals[:top_n]

        # No match - return empty list (will trigger CrossRef search)
        return []


# Keep backward compatibility
SJRSearcher = JournalSearcher


def display_journals_table(journals: list[Journal]) -> None:
    """Display journals in a rich table."""
    table = Table(title="Journals")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Journal Name", style="green")
    table.add_column("ISSN", style="yellow")
    table.add_column("Publisher", style="blue")

    for i, j in enumerate(journals, 1):
        table.add_row(
            str(i),
            j.name[:50] + "..." if len(j.name) > 50 else j.name,
            j.issn,
            (j.publisher[:25] + "...") if j.publisher and len(j.publisher) > 25 else (j.publisher or "-"),
        )

    console.print(table)
