#!/usr/bin/env python3
"""Fetch papers from subscribed journals."""

import argparse
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".paperflow"
DB_PATH = DATA_DIR / "papers.db"


def init_db():
    """Initialize database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            title_zh TEXT,
            abstract TEXT,
            abstract_zh TEXT,
            summary TEXT,
            authors TEXT,
            doi TEXT,
            url TEXT,
            pdf_url TEXT,
            published_date DATE,
            journal_issn TEXT,
            journal_name TEXT
        )
    """)
    conn.commit()
    return conn


def fetch_from_crossref(issn: str, days: int, journal_name: str = None):
    """Fetch papers from CrossRef."""
    try:
        import httpx
        from_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")

        response = httpx.get(
            "https://api.crossref.org/works",
            params={
                "filter": f"issn:{issn},from-pub-date:{from_date}",
                "select": "DOI,title,abstract,author,published-print,published-online,URL,link",
                "rows": 50,
            },
            headers={"User-Agent": "Paperflow/0.1"},
            timeout=30
        )
        data = response.json()
        items = data.get("message", {}).get("items", [])

        papers = []
        for item in items:
            title = item.get("title", [""])[0]
            if not title:
                continue

            # Authors
            authors = []
            for author in item.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                if given or family:
                    authors.append(f"{given} {family}".strip())

            # Date
            pub = item.get("published-print") or item.get("published-online")
            pub_date = None
            if pub and pub.get("date-parts"):
                parts = pub["date-parts"][0]
                if len(parts) >= 3:
                    pub_date = f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"

            # PDF
            pdf_url = None
            for link in item.get("link", []):
                if link.get("content-type") == "application/pdf":
                    pdf_url = link.get("URL")
                    break

            papers.append({
                "title": title,
                "abstract": item.get("abstract"),
                "authors": authors,
                "doi": item.get("DOI"),
                "url": item.get("URL"),
                "pdf_url": pdf_url,
                "published_date": pub_date,
                "journal_issn": issn,
                "journal_name": journal_name,
            })

        return papers

    except Exception as e:
        print(f"Error fetching from CrossRef: {e}", file=sys.stderr)
        return []


def save_papers(conn, papers):
    """Save papers to database."""
    cur = conn.cursor()
    saved = 0

    for p in papers:
        # Check if exists
        if p.get("doi"):
            cur.execute("SELECT id FROM articles WHERE doi = ?", (p["doi"],))
            if cur.fetchone():
                continue

        cur.execute(
            """INSERT INTO articles
               (title, abstract, authors, doi, url, pdf_url, published_date, journal_issn, journal_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                p["title"],
                p.get("abstract"),
                json.dumps(p.get("authors", [])),
                p.get("doi"),
                p.get("url"),
                p.get("pdf_url"),
                p.get("published_date"),
                p.get("journal_issn"),
                p.get("journal_name"),
            )
        )
        saved += 1

    conn.commit()
    return saved


def main():
    parser = argparse.ArgumentParser(description="Fetch papers from subscribed journals")
    parser.add_argument("--days", "-d", type=int, default=7, help="Days to look back")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    conn = init_db()

    # Get subscribed journals
    cur = conn.execute("SELECT name, issn FROM journals WHERE active = 1")
    journals = cur.fetchall()

    if not journals:
        result = {"fetched": 0, "error": "No journals subscribed"}
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("No journals subscribed. Use 'subscribe add' first.")
        return

    total_fetched = 0
    for name, issn in journals:
        papers = fetch_from_crossref(issn, args.days, name)
        saved = save_papers(conn, papers)
        total_fetched += saved
        print(f"Fetched {saved} papers from {name}", file=sys.stderr)

    conn.close()

    result = {"fetched": total_fetched, "journals": [j[0] for j in journals], "days": args.days}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Total fetched: {total_fetched} papers")


if __name__ == "__main__":
    import sys
    main()
