# Paperflow Skill

> 学术期刊聚合助手 - 搜索顶刊、获取论文、AI总结、生成报告

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
