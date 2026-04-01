# Paperflow Skill

> Search top journals across 15+ fields, fetch latest papers from subscriptions, generate AI summaries and bilingual Markdown reports. Use when: (1) User asks about top journals in a specific field (AI, ML, Political Science, etc.), (2) User wants to subscribe to journals and track new papers, (3) User needs paper translations or AI-generated summaries, (4) User requests a consolidated research paper report.
Triggers: top journals, journal search, paper aggregation, academic papers, research papers, journal subscription, paper summary, AI summary, literature review, paper report, 顶刊, 期刊搜索, 论文聚合, 学术论文, 文献综述.

> 搜索15+领域的顶级期刊，订阅并获取最新论文，生成AI总结与中英双语Markdown报告。适用场景：（1）用户询问某领域顶级期刊（AI、机器学习、政治学等），（2）用户想订阅期刊并跟踪新论文，（3）用户需要论文翻译或AI总结，（4）用户请求生成论文聚合报告。
触发词：顶刊、期刊搜索、论文聚合、学术论文、研究论文、期刊订阅、论文总结、AI总结、文献综述、论文报告。

一个用于学术研究论文聚合的 OpenClaw/Claude Code Skill。支持从15+领域搜索顶刊，获取最新论文，生成中英双语报告和AI总结。

## 功能特点

- **智能期刊搜索** - 内置15+领域顶刊数据，支持动态搜索
- **论文获取** - CrossRef API + RSS订阅获取最新论文
- **中英双语翻译** - 本地Ollama翻译，无需API费用
- **AI智能总结** - 基于摘要或全文生成中文总结
- **PDF下载解析** - 下载论文PDF并提取文本
- **Markdown报告** - 按期刊分组生成报告

## 触发条件

当用户：
- 询问某个领域的顶刊/期刊排名
- 想订阅/获取学术论文
- 需要论文翻译或总结
- 请求生成论文报告

## 使用方式

### 1. 搜索期刊

```bash
# 使用脚本搜索期刊
python3 scripts/search_journals.py "Artificial Intelligence" --top 10
```

### 2. 订阅期刊

```bash
# 订阅期刊（通过ISSN）
python3 scripts/subscribe.py add 2522-5839  # Nature Machine Intelligence
```

### 3. 获取论文

```bash
# 获取最近7天的论文
python3 scripts/fetch_papers.py --days 7
```

### 4. 生成总结

```bash
# 生成AI总结
python3 scripts/summarize.py --days 7 --limit 10

# 全文总结（需PDF）
python3 scripts/summarize.py --days 7 --fulltext --limit 5
```

### 5. 生成报告

```bash
# 生成Markdown报告
python3 scripts/report.py --output report.md --days 7
```

## 支持的领域

**计算机科学**: AI, ML, NLP, CV, Robotics, Data Science
**自然科学**: Biology, Neuroscience, Chemistry, Physics, Materials, Quantum, Climate
**医学**: Medicine, Bioinformatics
**社会科学**: Political Science, Computational Social Science, Economics, Psychology

## 依赖

- Python 3.10+
- Ollama (用于翻译和总结)
- httpx, feedparser, beautifulsoup4, sqlalchemy

## 安装

```bash
# 安装依赖
pip install httpx feedparser beautifulsoup4 sqlalchemy ollama pyyaml

# 可选：PDF支持
pip install pymupdf

# 启动Ollama服务
ollama serve

# 下载模型
ollama pull qwen2.5
```

## 数据存储

- 数据库: `~/.paperflow/papers.db`
- PDF文件: `~/.paperflow/pdfs/`
- 配置: `~/.paperflow/config.yaml`
