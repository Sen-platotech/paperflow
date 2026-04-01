#!/usr/bin/env python3
"""Search journals by topic."""

import argparse
import json
import sys
from pathlib import Path

# Add paperflow to path if installed
try:
    from paperflow.sources import JournalSearcher, display_journals_table
    from paperflow.models import Journal
except ImportError:
    # Fallback: use inline implementation
    import httpx

    PRESET_JOURNALS = {
        "artificial intelligence": [
            {"name": "Nature Machine Intelligence", "issn": "2522-5839", "publisher": "Springer Nature"},
            {"name": "Journal of Machine Learning Research", "issn": "1532-4435", "publisher": "JMLR"},
            {"name": "IEEE TPAMI", "issn": "0162-8828", "publisher": "IEEE"},
            {"name": "Artificial Intelligence", "issn": "0004-3702", "publisher": "Elsevier"},
            {"name": "Machine Learning", "issn": "0885-6125", "publisher": "Springer"},
        ],
        "machine learning": [
            {"name": "JMLR", "issn": "1532-4435", "publisher": "JMLR"},
            {"name": "Nature Machine Intelligence", "issn": "2522-5839", "publisher": "Springer Nature"},
            {"name": "Machine Learning", "issn": "0885-6125", "publisher": "Springer"},
        ],
        "political science": [
            {"name": "American Political Science Review", "issn": "0003-0554", "publisher": "Cambridge"},
            {"name": "American Journal of Political Science", "issn": "0092-5853", "publisher": "MPSA"},
            {"name": "Journal of Politics", "issn": "0022-3816", "publisher": "Chicago"},
            {"name": "World Politics", "issn": "0043-8871", "publisher": "Cambridge"},
        ],
        "computational social science": [
            {"name": "Journal of Computational Social Science", "issn": "2435-4685", "publisher": "Springer"},
            {"name": "EPJ Data Science", "issn": "2193-1127", "publisher": "Springer"},
            {"name": "JASSS", "issn": "1460-7425", "publisher": "University of Surrey"},
        ],
    }

    def search_journals(topic: str, top: int):
        topic_lower = topic.lower()
        for key, journals in PRESET_JOURNALS.items():
            if key in topic_lower or topic_lower in key:
                return journals[:top]

        # Try CrossRef
        try:
            client = httpx.Client(timeout=30)
            response = client.get(
                "https://api.crossref.org/journals",
                params={"query": topic, "rows": top},
                headers={"User-Agent": "Paperflow/0.1"}
            )
            data = response.json()
            items = data.get("message", {}).get("items", [])
            return [
                {"name": i.get("title"), "issn": i.get("ISSN", [""])[0], "publisher": i.get("publisher")}
                for i in items if i.get("title") and i.get("ISSN")
            ][:top]
        except Exception:
            return PRESET_JOURNALS.get("artificial intelligence", [])[:top]


def main():
    parser = argparse.ArgumentParser(description="Search journals by topic")
    parser.add_argument("topic", help="Topic to search")
    parser.add_argument("--top", "-n", type=int, default=10, help="Number of results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        from paperflow.sources import JournalSearcher
        searcher = JournalSearcher()
        journals = searcher.search_by_topic(args.topic, args.top)
        searcher.close()

        if args.json:
            result = [{"name": j.name, "issn": j.issn, "publisher": j.publisher} for j in journals]
            print(json.dumps({"journals": result, "count": len(result)}, ensure_ascii=False, indent=2))
        else:
            for i, j in enumerate(journals, 1):
                print(f"{i}. {j.name} ({j.issn}) - {j.publisher or 'N/A'}")
    except ImportError:
        journals = search_journals(args.topic, args.top)

        if args.json:
            print(json.dumps({"journals": journals, "count": len(journals)}, ensure_ascii=False, indent=2))
        else:
            for i, j in enumerate(journals, 1):
                print(f"{i}. {j['name']} ({j['issn']}) - {j.get('publisher', 'N/A')}")


if __name__ == "__main__":
    main()
