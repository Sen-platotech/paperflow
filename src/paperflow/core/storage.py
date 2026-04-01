"""Local storage using SQLite and SQLAlchemy."""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from ..models import Article, Journal


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class JournalDB(Base):
    """Journal database model."""

    __tablename__ = "journals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    issn: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(200))
    sjr_score: Mapped[Optional[float]] = mapped_column(Float)
    h_index: Mapped[Optional[int]] = mapped_column(Integer)
    category: Mapped[Optional[str]] = mapped_column(String(200))
    rss_url: Mapped[Optional[str]] = mapped_column(String(500))
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ArticleDB(Base):
    """Article database model."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    title_zh: Mapped[Optional[str]] = mapped_column(Text)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    abstract_zh: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    summary_zh: Mapped[Optional[str]] = mapped_column(Text)
    authors: Mapped[Optional[str]] = mapped_column(JSON)  # List as JSON
    affiliations: Mapped[Optional[str]] = mapped_column(JSON)  # List as JSON
    doi: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    url: Mapped[Optional[str]] = mapped_column(String(500))
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    published_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    journal_issn: Mapped[str] = mapped_column(String(20), index=True)
    journal_name: Mapped[Optional[str]] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    translated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    summarized_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Storage:
    """Local storage manager."""

    def __init__(self, db_path: Path):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create tables if they don't exist and run migrations."""
        import sqlite3

        # Run migrations first using raw sqlite3
        migrations = [
            "ALTER TABLE articles ADD COLUMN summary TEXT",
            "ALTER TABLE articles ADD COLUMN summary_zh TEXT",
            "ALTER TABLE articles ADD COLUMN pdf_path VARCHAR(500)",
            "ALTER TABLE articles ADD COLUMN summarized_at DATETIME",
        ]

        db_path = str(self.engine.url).replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        for alter_sql in migrations:
            try:
                conn.execute(alter_sql)
            except sqlite3.OperationalError:
                pass  # Column already exists
        conn.commit()
        conn.close()

        # Now create any missing tables
        Base.metadata.create_all(self.engine)

    # Journal operations
    def add_journal(self, journal: Journal) -> JournalDB:
        """Add a journal to the database."""
        with Session(self.engine) as session:
            db_journal = JournalDB(
                name=journal.name,
                issn=journal.issn,
                publisher=journal.publisher,
                sjr_score=journal.sjr_score,
                h_index=journal.h_index,
                category=journal.category,
                rss_url=journal.rss_url,
                rank=journal.rank,
            )
            session.add(db_journal)
            session.commit()
            session.refresh(db_journal)
            return db_journal

    def get_journal_by_issn(self, issn: str) -> Optional[JournalDB]:
        """Get a journal by ISSN."""
        with Session(self.engine) as session:
            return session.execute(select(JournalDB).where(JournalDB.issn == issn)).scalar_one_or_none()

    def get_all_journals(self, active_only: bool = True) -> list[JournalDB]:
        """Get all journals."""
        with Session(self.engine) as session:
            query = select(JournalDB)
            if active_only:
                query = query.where(JournalDB.active == True)
            return list(session.execute(query).scalars().all())

    def remove_journal(self, issn: str) -> bool:
        """Remove a journal subscription."""
        with Session(self.engine) as session:
            journal = session.execute(select(JournalDB).where(JournalDB.issn == issn)).scalar_one_or_none()
            if journal:
                session.delete(journal)
                session.commit()
                return True
            return False

    # Article operations
    def add_article(self, article: Article) -> ArticleDB:
        """Add an article to the database."""
        with Session(self.engine) as session:
            db_article = ArticleDB(
                title=article.title,
                title_zh=article.title_zh,
                abstract=article.abstract,
                abstract_zh=article.abstract_zh,
                authors=article.authors,
                affiliations=article.affiliations,
                doi=article.doi,
                url=article.url,
                pdf_url=article.pdf_url,
                published_date=article.published_date,
                journal_issn=article.journal_issn,
                journal_name=article.journal_name,
                source=article.source,
            )
            session.add(db_article)
            session.commit()
            session.refresh(db_article)
            return db_article

    def article_exists(self, doi: Optional[str], title: str) -> bool:
        """Check if an article already exists."""
        with Session(self.engine) as session:
            if doi:
                existing = session.execute(select(ArticleDB).where(ArticleDB.doi == doi)).scalar_one_or_none()
                if existing:
                    return True
            # Check by title similarity
            existing = session.execute(select(ArticleDB).where(ArticleDB.title == title)).scalar_one_or_none()
            return existing is not None

    def get_articles_by_date_range(
        self, start_date: date, end_date: date, journal_issn: Optional[str] = None
    ) -> list[ArticleDB]:
        """Get articles within a date range."""
        with Session(self.engine) as session:
            query = select(ArticleDB).where(
                ArticleDB.published_date >= start_date, ArticleDB.published_date <= end_date
            )
            if journal_issn:
                query = query.where(ArticleDB.journal_issn == journal_issn)
            query = query.order_by(ArticleDB.published_date.desc())
            return list(session.execute(query).scalars().all())

    def get_untranslated_articles(self) -> list[ArticleDB]:
        """Get articles that haven't been translated yet."""
        with Session(self.engine) as session:
            return list(
                session.execute(select(ArticleDB).where(ArticleDB.translated_at == None)).scalars().all()
            )

    def update_article_translation(
        self, article_id: int, title_zh: str, abstract_zh: Optional[str]
    ) -> None:
        """Update article with translations."""
        with Session(self.engine) as session:
            article = session.get(ArticleDB, article_id)
            if article:
                article.title_zh = title_zh
                article.abstract_zh = abstract_zh
                article.translated_at = datetime.now()
                session.commit()

    def get_unsummarized_articles(self) -> list[ArticleDB]:
        """Get articles that haven't been summarized yet."""
        with Session(self.engine) as session:
            return list(
                session.execute(select(ArticleDB).where(ArticleDB.summarized_at == None)).scalars().all()
            )

    def update_article_summary(
        self, article_id: int, summary: str, summary_zh: Optional[str]
    ) -> None:
        """Update article with AI summary."""
        with Session(self.engine) as session:
            article = session.get(ArticleDB, article_id)
            if article:
                article.summary = summary
                article.summary_zh = summary_zh
                article.summarized_at = datetime.now()
                session.commit()

    def update_article_pdf_path(self, article_id: int, pdf_path: str) -> None:
        """Update article with local PDF path."""
        with Session(self.engine) as session:
            article = session.get(ArticleDB, article_id)
            if article:
                article.pdf_path = pdf_path
                session.commit()

    def get_article_by_id(self, article_id: int) -> Optional[ArticleDB]:
        """Get an article by ID."""
        with Session(self.engine) as session:
            return session.get(ArticleDB, article_id)

    def get_articles_grouped_by_journal(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> dict[str, list[ArticleDB]]:
        """Get articles grouped by journal name."""
        if start_date is None:
            start_date = date.today() - timedelta(days=7)
        if end_date is None:
            end_date = date.today()

        articles = self.get_articles_by_date_range(start_date, end_date)

        grouped: dict[str, list[ArticleDB]] = {}
        for article in articles:
            journal_name = article.journal_name or article.journal_issn
            if journal_name not in grouped:
                grouped[journal_name] = []
            grouped[journal_name].append(article)

        # Sort each group by date
        for journal_name in grouped:
            grouped[journal_name].sort(key=lambda a: a.published_date or date.min, reverse=True)

        return grouped
