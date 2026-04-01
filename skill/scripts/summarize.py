#!/usr/bin/env python3
"""Generate AI summaries for papers."""

import argparse
import json
import sqlite3
from pathlib import Path

DATA_DIR = Path.home() / ".paperflow"
DB_PATH = DATA_DIR / "papers.db"


def summarize_with_ollama(title: str, abstract: str, model: str = "qwen2.5"):
    """Summarize using Ollama."""
    if not abstract:
        return None

    prompt = f"""请对以下学术论文进行简洁总结，要求：

1. 用2-3句话概括论文的核心贡献
2. 说明研究方法和主要发现
3. 指出研究的意义或应用价值

论文标题：{title}

摘要：
{abstract}

请用中文输出总结（约100-150字）："""

    try:
        import ollama
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3},
        )
        return response["message"]["content"].strip()
    except Exception as e:
        print(f"Ollama error: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate AI summaries")
    parser.add_argument("--days", "-d", type=int, default=7, help="Days to look back")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max papers to summarize")
    parser.add_argument("--model", "-m", default="qwen2.5", help="Ollama model")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)

    # Ensure summary column
    try:
        conn.execute("ALTER TABLE articles ADD COLUMN summary TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()

    # Get unsummarized papers
    cur = conn.execute("""
        SELECT id, title, abstract FROM articles
        WHERE summary IS NULL AND abstract IS NOT NULL
        LIMIT ?
    """, (args.limit,))

    papers = cur.fetchall()
    if not papers:
        result = {"summarized": 0, "message": "All papers summarized"}
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print("All papers have been summarized.")
        return

    summarized = 0
    for paper_id, title, abstract in papers:
        print(f"Summarizing: {title[:50]}...", file=sys.stderr)
        summary = summarize_with_ollama(title, abstract, args.model)

        if summary:
            conn.execute("UPDATE articles SET summary = ? WHERE id = ?", (summary, paper_id))
            conn.commit()
            summarized += 1
            print(f"  Summary: {summary[:100]}...", file=sys.stderr)

    conn.close()

    result = {"summarized": summarized, "total": len(papers)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Summarized {summarized}/{len(papers)} papers")


if __name__ == "__main__":
    import sys
    main()
