#!/usr/bin/env python3
"""Subscribe to journals."""

import argparse
import json
import sys
from pathlib import Path

DATA_DIR = Path.home() / ".paperflow"
DB_PATH = DATA_DIR / "papers.db"


def init_db():
    """Initialize database."""
    import sqlite3
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS journals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            issn TEXT UNIQUE NOT NULL,
            publisher TEXT,
            active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    return conn


def add_journal(issn: str, name: str = None):
    """Add a journal subscription."""
    conn = init_db()

    # Check if exists
    cur = conn.execute("SELECT name FROM journals WHERE issn = ?", (issn,))
    if cur.fetchone():
        return {"success": False, "error": "Already subscribed"}

    # Get journal name if not provided
    if not name:
        try:
            import httpx
            response = httpx.get(
                f"https://api.crossref.org/journals/{issn}",
                headers={"User-Agent": "Paperflow/0.1"},
                timeout=30
            )
            data = response.json()
            name = data.get("message", {}).get("title", issn)
        except Exception:
            name = issn

    conn.execute(
        "INSERT INTO journals (name, issn, publisher) VALUES (?, ?, ?)",
        (name, issn, "")
    )
    conn.commit()
    conn.close()

    return {"success": True, "name": name, "issn": issn}


def remove_journal(issn: str):
    """Remove a journal subscription."""
    conn = init_db()
    cur = conn.execute("DELETE FROM journals WHERE issn = ?", (issn,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return {"success": deleted, "issn": issn}


def list_journals():
    """List subscribed journals."""
    conn = init_db()
    cur = conn.execute("SELECT name, issn, publisher FROM journals WHERE active = 1")
    journals = [{"name": r[0], "issn": r[1], "publisher": r[2]} for r in cur.fetchall()]
    conn.close()
    return journals


def main():
    parser = argparse.ArgumentParser(description="Manage journal subscriptions")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add
    add_parser = subparsers.add_parser("add", help="Subscribe to a journal")
    add_parser.add_argument("issn", help="Journal ISSN")
    add_parser.add_argument("--name", "-n", help="Journal name")

    # Remove
    remove_parser = subparsers.add_parser("remove", help="Unsubscribe from a journal")
    remove_parser.add_argument("issn", help="Journal ISSN")

    # List
    subparsers.add_parser("list", help="List subscribed journals")

    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.command == "add":
        result = add_journal(args.issn, args.name)
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        elif result["success"]:
            print(f"Subscribed to: {result['name']} ({result['issn']})")
        else:
            print(f"Error: {result['error']}")

    elif args.command == "remove":
        result = remove_journal(args.issn)
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        elif result["success"]:
            print(f"Unsubscribed from: {args.issn}")
        else:
            print(f"Not subscribed: {args.issn}")

    elif args.command == "list":
        journals = list_journals()
        if args.json:
            print(json.dumps({"journals": journals}, ensure_ascii=False, indent=2))
        else:
            for i, j in enumerate(journals, 1):
                print(f"{i}. {j['name']} ({j['issn']})")


if __name__ == "__main__":
    main()
