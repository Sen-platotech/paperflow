#!/usr/bin/env python3
"""Generate Markdown report."""

import argparse
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".paperflow"
DB_PATH = DATA_DIR / "papers.db"


def generate_report(days: int, output_path: str = None, title: str = None):
    """Generate a Markdown report."""
    conn = sqlite3.connect(DB_PATH)

    from_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")

    cur = conn.execute("""
        SELECT title, title_zh, abstract, abstract_zh, summary, authors, doi, url, pdf_url,
               published_date, journal_name
        FROM articles
        WHERE published_date >= ?
        ORDER BY journal_name, published_date DESC
    """, (from_date,))

    papers = cur.fetchall()
    conn.close()

    if not papers:
        return None

    # Group by journal
    journals = {}
    for p in papers:
        journal = p[10] or "Unknown"
        if journal not in journals:
            journals[journal] = []
        journals[journal].append(p)

    # Generate markdown
    lines = []
    lines.append(f"# {title or '学术论文聚合报告'}")
    lines.append("")
    lines.append(f"**时间范围:** {from_date} ~ {date.today()}")
    lines.append(f"**共收录:** {len(papers)} 篇论文，来自 {len(journals)} 个期刊")
    lines.append("")

    # TOC
    lines.append("## 目录")
    for journal, papers_list in journals.items():
        lines.append(f"- [{journal}](#{journal.lower().replace(' ', '-')}) ({len(papers_list)}篇)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Papers by journal
    for journal, papers_list in journals.items():
        lines.append(f"## {journal}")
        lines.append("")

        for i, p in enumerate(papers_list, 1):
            title, title_zh, abstract, abstract_zh, summary, authors, doi, url, pdf_url, pub_date, _ = p

            lines.append(f"### {i}. {title}")
            if title_zh:
                lines.append(f"**译名:** {title_zh}")
            lines.append("")

            if authors:
                try:
                    author_list = json.loads(authors)
                    if author_list:
                        lines.append(f"**作者:** {', '.join(author_list[:5])}")
                except:
                    pass

            if pub_date:
                lines.append(f"**发布时间:** {pub_date}")

            if doi:
                lines.append(f"**DOI:** [{doi}](https://doi.org/{doi})")

            lines.append("")

            if summary:
                lines.append("**🤖 AI总结:**")
                lines.append(f"> {summary}")
                lines.append("")

            # Links
            links = []
            if url:
                links.append(f"[原文]({url})")
            if pdf_url:
                links.append(f"[PDF]({pdf_url})")
            if doi:
                links.append(f"[DOI](https://doi.org/{doi})")
            if links:
                lines.append(f"**链接:** {' | '.join(links)}")

            lines.append("")
            lines.append("---")
            lines.append("")

    content = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")

    return content


def main():
    parser = argparse.ArgumentParser(description="Generate Markdown report")
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--days", "-d", type=int, default=7, help="Days to cover")
    parser.add_argument("--title", "-t", default=None, help="Report title")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    content = generate_report(args.days, args.output, args.title)

    if content is None:
        result = {"error": "No papers found"}
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("No papers found in the specified date range.")
        return

    result = {"generated": True, "output": args.output, "length": len(content)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        if args.output:
            print(f"Report saved to: {args.output}")
        else:
            print(content)


if __name__ == "__main__":
    import sys
    main()
