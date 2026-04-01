"""Translation module using Ollama."""

import time
from typing import Optional

import ollama
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class OllamaTranslator:
    """Translate text using Ollama local models."""

    def __init__(self, model: str = "qwen2", host: str = "http://localhost:11434"):
        self.model = model
        self.client = ollama.Client(host=host)
        self._cache: dict[str, str] = {}

    def check_connection(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            models = self.client.list()
            model_names = [m["model"] for m in models.get("models", [])]
            return self.model in model_names or any(self.model in m for m in model_names)
        except Exception:
            return False

    def translate(self, text: str, target_lang: str = "中文") -> Optional[str]:
        """
        Translate text to target language.

        Args:
            text: Text to translate
            target_lang: Target language (default: Chinese)

        Returns:
            Translated text or None if translation fails
        """
        if not text or not text.strip():
            return None

        # Check cache
        cache_key = f"{text}:{target_lang}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        prompt = f"""请将以下学术文本翻译成{target_lang}。
要求：
1. 保持专业术语的准确性
2. 保持学术写作风格
3. 不要添加任何解释或说明，只输出翻译结果

原文：
{text}

翻译："""

        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3},  # Lower temperature for more consistent translations
            )
            result = response["message"]["content"].strip()
            self._cache[cache_key] = result
            return result
        except Exception as e:
            console.print(f"[red]Translation error: {e}[/red]")
            return None

    def translate_batch(
        self,
        items: list[dict],
        title_key: str = "title",
        abstract_key: str = "abstract",
        show_progress: bool = True,
    ) -> list[dict]:
        """
        Translate a batch of items with title and abstract.

        Args:
            items: List of dicts containing title and abstract
            title_key: Key for title field
            abstract_key: Key for abstract field
            show_progress: Show progress indicator

        Returns:
            List of items with translated fields added
        """
        results = []

        iterator = items
        if show_progress:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            )
            with progress:
                task = progress.add_task("Translating...", total=len(items))
                for item in iterator:
                    translated = self._translate_item(item, title_key, abstract_key)
                    results.append(translated)
                    progress.advance(task)
        else:
            for item in iterator:
                translated = self._translate_item(item, title_key, abstract_key)
                results.append(translated)

        return results

    def _translate_item(
        self, item: dict, title_key: str, abstract_key: str
    ) -> dict:
        """Translate a single item."""
        result = item.copy()

        if title_key in item and item[title_key]:
            result[f"{title_key}_zh"] = self.translate(item[title_key])
            time.sleep(0.1)  # Small delay to avoid overwhelming the model

        if abstract_key in item and item[abstract_key]:
            result[f"{abstract_key}_zh"] = self.translate(item[abstract_key])
            time.sleep(0.1)

        return result

    def ensure_model(self) -> bool:
        """Ensure the translation model is available, pull if needed."""
        try:
            if self.check_connection():
                return True

            console.print(f"[yellow]Pulling model {self.model}...[/yellow]")
            self.client.pull(self.model)
            return True
        except Exception as e:
            console.print(f"[red]Failed to ensure model: {e}[/red]")
            return False
