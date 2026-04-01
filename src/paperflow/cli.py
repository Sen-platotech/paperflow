"""Paperflow CLI application."""

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import get_settings, load_settings, save_settings
from .core.reporter import ReportGenerator
from .core.storage import Storage
from .core.translator import OllamaTranslator
from .models import Article, Journal
from .sources import CrossRefFetcher, JournalSearcher, RSSFetcher, display_journals_table, get_rss_url

app = typer.Typer(
    name="paperflow",
    help="Academic journal aggregation CLI with bilingual translation",
    add_completion=False,
)
console = Console()

# Sub-apps
subscribe_app = typer.Typer(name="subscribe", help="Manage journal subscriptions")
app.add_typer(subscribe_app, name="subscribe")

config_app = typer.Typer(name="config", help="Configure paperflow")
app.add_typer(config_app, name="config")


# --- Main commands ---
@app.command()
def search_journals(
    query: str = typer.Argument(..., help="Search query (topic or journal name)"),
    top: int = typer.Option(20, "--top", "-n", help="Number of results"),
):
    """Search for journals by topic or name."""
    searcher = JournalSearcher()
    try:
        journals = searcher.search_by_topic(query, top)
        if not journals:
            console.print("[yellow]No journals found. Try a different query.[/yellow]")
            return
        display_journals_table(journals)
    finally:
        searcher.close()


@app.command()
def fetch(
    days: int = typer.Option(7, "--days", "-d", help="Days to look back"),
    translate: bool = typer.Option(True, "--translate/--no-translate", help="Translate articles"),
):
    """Fetch articles from subscribed journals."""
    settings = load_settings()
    settings.ensure_data_dir()
    storage = Storage(settings.database_path)

    journals = storage.get_all_journals()
    if not journals:
        console.print("[yellow]No journals subscribed. Use 'paperflow subscribe add' first.[/yellow]")
        return

    console.print(f"[cyan]Fetching articles from {len(journals)} journals...[/cyan]")

    crossref = CrossRefFetcher()
    rss_fetcher = RSSFetcher()

    total_articles = 0

    for journal in journals:
        console.print(f"\n[cyan]Fetching: {journal.name}[/cyan]")

        articles = []

        # Try RSS first
        if journal.rss_url:
            articles = rss_fetcher.fetch_articles(
                journal.rss_url, journal.issn, journal.name, days
            )

        # Fallback to CrossRef
        if not articles:
            articles = crossref.fetch_articles_by_issn(journal.issn, days, journal.name)

        # Store articles
        for article in articles:
            if not storage.article_exists(article.doi, article.title):
                storage.add_article(article)
                total_articles += 1

    crossref.close()
    rss_fetcher.close()

    console.print(f"\n[green]Fetched {total_articles} new articles[/green]")

    # Translate if enabled
    if translate and total_articles > 0:
        _translate_pending(storage, settings)


def _translate_pending(storage: Storage, settings):
    """Translate untranslated articles."""
    translator = OllamaTranslator(
        model=settings.ollama_model,
        host=settings.ollama_host,
    )

    if not translator.check_connection():
        console.print("[yellow]Ollama not available. Skipping translation.[/yellow]")
        console.print("[yellow]Make sure Ollama is running with: ollama serve[/yellow]")
        return

    untranslated = storage.get_untranslated_articles()
    console.print(f"[cyan]Translating {len(untranslated)} articles...[/cyan]")

    for article in untranslated:
        title_zh = translator.translate(article.title)
        abstract_zh = translator.translate(article.abstract) if article.abstract else None

        if title_zh:
            storage.update_article_translation(article.id, title_zh, abstract_zh)


@app.command()
def report(
    output: Path = typer.Option(Path("paperflow_report.md"), "--output", "-o", help="Output file path"),
    days: int = typer.Option(7, "--days", "-d", help="Days to cover"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Report title"),
):
    """Generate a Markdown report."""
    settings = load_settings()
    storage = Storage(settings.database_path)

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    articles_by_journal = storage.get_articles_grouped_by_journal(start_date, end_date)

    if not articles_by_journal:
        console.print("[yellow]No articles found in the specified date range.[/yellow]")
        return

    generator = ReportGenerator()
    generator.generate(
        articles_by_journal=articles_by_journal,
        start_date=start_date,
        end_date=end_date,
        output_path=output,
        title=title,
    )


@app.command()
def list_articles(
    journal: Optional[str] = typer.Option(None, "--journal", "-j", help="Filter by journal ISSN"),
    days: int = typer.Option(7, "--days", "-d", help="Days to look back"),
):
    """List stored articles."""
    settings = load_settings()
    storage = Storage(settings.database_path)

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    articles = storage.get_articles_by_date_range(start_date, end_date, journal)

    if not articles:
        console.print("[yellow]No articles found.[/yellow]")
        return

    table = Table(title=f"Articles ({start_date} ~ {end_date})")
    table.add_column("Date", width=12)
    table.add_column("Title", width=50)
    table.add_column("Journal", width=20)

    for article in articles[:50]:  # Limit display
        table.add_row(
            str(article.published_date) if article.published_date else "-",
            article.title[:50] + "..." if len(article.title) > 50 else article.title,
            article.journal_name[:20] if article.journal_name else article.journal_issn,
        )

    console.print(table)
    console.print(f"\nTotal: {len(articles)} articles")


# --- Subscribe commands ---
@subscribe_app.command("add")
def subscribe_add(
    issn: str = typer.Argument(..., help="Journal ISSN"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Journal name"),
):
    """Subscribe to a journal."""
    settings = load_settings()
    settings.ensure_data_dir()
    storage = Storage(settings.database_path)

    # Check if already subscribed
    existing = storage.get_journal_by_issn(issn)
    if existing:
        console.print(f"[yellow]Already subscribed to: {existing.name}[/yellow]")
        return

    # Fetch journal info
    crossref = CrossRefFetcher()
    journal_name = name or crossref.get_journal_name(issn)
    crossref.close()

    if not journal_name:
        console.print(f"[red]Could not find journal with ISSN: {issn}[/red]")
        raise typer.Exit(1)

    # Add subscription
    journal = Journal(
        name=journal_name,
        issn=issn,
        rss_url=get_rss_url(issn),
    )

    storage.add_journal(journal)
    console.print(f"[green]Subscribed to: {journal_name} ({issn})[/green]")


@subscribe_app.command("remove")
def subscribe_remove(
    issn: str = typer.Argument(..., help="Journal ISSN to remove"),
):
    """Unsubscribe from a journal."""
    settings = load_settings()
    storage = Storage(settings.database_path)

    if storage.remove_journal(issn):
        console.print(f"[green]Unsubscribed from: {issn}[/green]")
    else:
        console.print(f"[red]Not subscribed to: {issn}[/red]")


@subscribe_app.command("list")
def subscribe_list():
    """List subscribed journals."""
    settings = load_settings()
    storage = Storage(settings.database_path)

    journals = storage.get_all_journals()

    if not journals:
        console.print("[yellow]No journals subscribed.[/yellow]")
        return

    table = Table(title="Subscribed Journals")
    table.add_column("ISSN", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Publisher")

    for j in journals:
        table.add_row(j.issn, j.name, j.publisher or "-")

    console.print(table)


# --- Config commands ---
@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key"),
    value: str = typer.Argument(..., help="Config value"),
):
    """Set a configuration value."""
    settings = load_settings()

    valid_keys = ["ollama_host", "ollama_model", "translate_enabled", "fetch_days"]

    if key not in valid_keys:
        console.print(f"[red]Invalid config key: {key}[/red]")
        console.print(f"Valid keys: {', '.join(valid_keys)}")
        raise typer.Exit(1)

    # Convert value type
    if key == "translate_enabled":
        value = value.lower() in ("true", "yes", "1")
    elif key == "fetch_days":
        value = int(value)

    setattr(settings, key, value)
    save_settings(settings)
    console.print(f"[green]Set {key} = {value}[/green]")


@config_app.command("show")
def config_show():
    """Show current configuration."""
    settings = load_settings()

    table = Table(title="Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("data_dir", str(settings.data_dir))
    table.add_row("ollama_host", settings.ollama_host)
    table.add_row("ollama_model", settings.ollama_model)
    table.add_row("translate_enabled", str(settings.translate_enabled))
    table.add_row("fetch_days", str(settings.fetch_days))

    console.print(table)


if __name__ == "__main__":
    app()
