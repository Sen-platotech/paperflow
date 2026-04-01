# Paperflow

<p align="center">
  <strong>📚 学术期刊聚合CLI工具</strong><br>
  <sub>从顶刊获取最新论文，一键生成中英双语报告</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Translation-Ollama-orange.svg" alt="Translation">
</p>

---

## ✨ 功能特点

- 🔍 **智能期刊搜索** - 从SJR获取领域顶刊排名，支持自定义期刊订阅
- 📰 **多源文章获取** - CrossRef API + RSS订阅，自动获取最新论文
- 🌐 **中英双语翻译** - 基于Ollama本地翻译，无需API费用
- 📊 **Markdown报告** - 按期刊分组，时间倒序，一键生成可读报告
- 💾 **本地存储** - SQLite数据库，支持全文搜索
- ⚡ **快速高效** - 异步获取，批量翻译

## 📦 安装

### 前置要求

- Python 3.10+
- Ollama (用于翻译)

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/Sen-platotech/paperflow.git
cd paperflow

# 安装
pip install -e .

# 安装Ollama翻译模型
ollama pull qwen2
```

## 🚀 快速开始

### 1. 搜索期刊

```bash
# 搜索AI领域顶刊
paperflow search-journals "Artificial Intelligence" --top 10

# 搜索机器学习领域
paperflow search-journals "Machine Learning" --top 5

# 搜索计算机视觉领域
paperflow search-journals "Computer Vision" --top 5
```

### 2. 订阅期刊

```bash
# 使用ISSN订阅期刊
paperflow subscribe add 2522-5839  # Nature Machine Intelligence
paperflow subscribe add 1532-4435  # JMLR

# 查看已订阅期刊
paperflow subscribe list

# 取消订阅
paperflow subscribe remove 2522-5839
```

### 3. 获取论文

```bash
# 获取最近7天的论文（带翻译）
paperflow fetch --days 7

# 获取论文（不翻译，更快）
paperflow fetch --days 30 --no-translate

# 查看已获取的论文
paperflow list-articles --days 30
```

### 4. 生成报告

```bash
# 生成Markdown报告
paperflow report --output ai_papers.md --days 7

# 自定义标题
paperflow report --output report.md --title "AI领域最新论文" --days 14
```

## 📝 报告示例

生成的Markdown报告格式：

```markdown
# 学术论文聚合报告

**时间范围:** 2024-01-15 ~ 2024-01-22
**共收录:** 15 篇论文，来自 2 个期刊

## 目录
- [Nature Machine Intelligence](#nature-machine-intelligence) (10篇)
- [Journal of Machine Learning Research](#jmlr) (5篇)

---

## Nature Machine Intelligence

### 1. A Unified Framework for Large Language Model Reasoning
**译名:** 大语言模型推理的统一框架

**作者:** Wei Chen, Li Zhang (Tsinghua University)

**发布时间:** 2024-01-20

**摘要 (Abstract):**
> This paper proposes a unified framework...

**摘要译文:**
> 本文提出了一种统一框架...

**链接:** [原文](...) | [PDF](...) | [DOI](...)
```

## ⚙️ 配置

### 查看配置

```bash
paperflow config show
```

### 修改配置

```bash
# 设置翻译模型
paperflow config set ollama_model qwen2.5

# 设置Ollama服务地址
paperflow config set ollama_host http://localhost:11434

# 启用/禁用翻译
paperflow config set translate_enabled true

# 设置默认获取天数
paperflow config set fetch_days 14
```

### 配置文件位置

- 数据目录: `~/.paperflow/`
- 数据库: `~/.paperflow/papers.db`
- 配置: `~/.paperflow/config.yaml`

## 🏗️ 项目结构

```
paperflow/
├── src/paperflow/
│   ├── cli.py           # CLI入口
│   ├── config.py        # 配置管理
│   ├── models/          # 数据模型
│   │   ├── journal.py   # 期刊模型
│   │   └── article.py   # 文章模型
│   ├── core/            # 核心功能
│   │   ├── storage.py   # SQLite存储
│   │   ├── translator.py # Ollama翻译
│   │   └── reporter.py  # 报告生成
│   └── sources/         # 数据源
│       ├── sjr.py       # SJR期刊搜索
│       ├── crossref.py  # CrossRef API
│       └── rss.py       # RSS解析
└── pyproject.toml
```

## 📊 数据源

| 来源 | 类型 | 说明 |
|------|------|------|
| SJR | 期刊排名 | Scimago Journal Rank，获取领域顶刊 |
| CrossRef | 论文元数据 | 通过ISSN获取期刊文章 |
| RSS | 论文订阅 | 部分期刊提供RSS feed |

## 🌐 支持的期刊

预设支持以下领域的顶级期刊：

- **人工智能**: Nature MI, JMLR, TPAMI, AI Journal, Machine Learning
- **机器学习**: JMLR, Nature MI, ML, IEEE TNNLS, Neurocomputing
- **自然语言处理**: Computational Linguistics, TACL, NLE
- **计算机视觉**: IJCV, TPAMI, Pattern Recognition, CVIU

也可以通过ISSN订阅任意期刊。

## 🔧 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
```

## 📄 License

MIT License

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Sen-platotech">Sen-platotech</a>
</p>
