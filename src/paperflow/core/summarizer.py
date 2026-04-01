"""AI Summarization module using Ollama."""

import time
from pathlib import Path
from typing import Optional

import httpx
import ollama
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class ArticleSummarizer:
    """Summarize articles using Ollama local models."""

    def __init__(self, model: str = "qwen2", host: str = "http://localhost:11434"):
        self.model = model
        self.client = ollama.Client(host=host)

    def check_connection(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            models = self.client.list()
            model_names = [m["model"] for m in models.get("models", [])]
            return self.model in model_names or any(self.model in m for m in model_names)
        except Exception:
            return False

    def summarize_abstract(self, title: str, abstract: str) -> Optional[str]:
        """
        Generate a concise summary from title and abstract.

        Args:
            title: Article title
            abstract: Article abstract

        Returns:
            Summary text or None if fails
        """
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
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3},
            )
            return response["message"]["content"].strip()
        except Exception as e:
            console.print(f"[red]Summarization error: {e}[/red]")
            return None

    def summarize_fulltext(self, text: str, title: str) -> Optional[str]:
        """
        Generate a detailed summary from full text.

        Args:
            text: Full article text
            title: Article title

        Returns:
            Summary text or None if fails
        """
        if not text or len(text) < 100:
            return None

        # Truncate if too long
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        prompt = f"""请对以下学术论文全文进行详细总结，要求：

1. 研究背景与动机（为什么做这个研究）
2. 核心方法与创新点（用了什么方法，有什么创新）
3. 主要实验结果（发现了什么）
4. 研究意义与局限（有什么价值，有什么不足）

论文标题：{title}

论文内容：
{text}

请用中文输出详细总结（约300-500字）："""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3},
            )
            return response["message"]["content"].strip()
        except Exception as e:
            console.print(f"[red]Full text summarization error: {e}[/red]")
            return None

    def summarize_batch(
        self,
        articles: list[dict],
        use_fulltext: bool = False,
        show_progress: bool = True,
    ) -> list[dict]:
        """
        Summarize a batch of articles.

        Args:
            articles: List of article dicts with title, abstract, and optionally fulltext
            use_fulltext: Whether to use full text for summarization
            show_progress: Show progress indicator

        Returns:
            List of articles with summary added
        """
        results = []

        if show_progress:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            )
            with progress:
                task = progress.add_task("Summarizing...", total=len(articles))
                for article in articles:
                    result = self._summarize_one(article, use_fulltext)
                    results.append(result)
                    progress.advance(task)
                    time.sleep(0.2)  # Rate limiting
        else:
            for article in articles:
                result = self._summarize_one(article, use_fulltext)
                results.append(result)
                time.sleep(0.2)

        return results

    def _summarize_one(self, article: dict, use_fulltext: bool) -> dict:
        """Summarize a single article."""
        result = article.copy()
        title = article.get("title", "")

        if use_fulltext and article.get("fulltext"):
            summary = self.summarize_fulltext(article["fulltext"], title)
        else:
            abstract = article.get("abstract", "")
            summary = self.summarize_abstract(title, abstract)

        result["summary_zh"] = summary
        return result


class PDFDownloader:
    """Download and extract text from PDFs."""

    def __init__(self, download_dir: Path, timeout: int = 60):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

    def download_pdf(self, url: str, filename: str) -> Optional[Path]:
        """
        Download a PDF from URL.

        Args:
            url: PDF URL
            filename: Local filename

        Returns:
            Path to downloaded file or None
        """
        try:
            response = self.client.get(url, headers=self.headers)
            response.raise_for_status()

            pdf_path = self.download_dir / filename
            pdf_path.write_bytes(response.content)
            return pdf_path

        except Exception as e:
            console.print(f"[yellow]PDF download failed: {e}[/yellow]")
            return None

    def extract_text(self, pdf_path: Path) -> Optional[str]:
        """
        Extract text from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text or None
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            text_parts = []

            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text.strip())

            doc.close()

            if text_parts:
                return "\n\n".join(text_parts)
            return None

        except ImportError:
            console.print("[yellow]PyMuPDF not installed. Install with: pip install pymupdf[/yellow]")
            return None
        except Exception as e:
            console.print(f"[yellow]PDF text extraction failed: {e}[/yellow]")
            return None

    def close(self):
        """Close the HTTP client."""
        self.client.close()
