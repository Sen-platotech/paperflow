# Paperflow

<p align="center">
  <strong>📚 学术期刊聚合工具</strong><br>
  <sub>搜索顶刊、获取论文、AI总结、生成报告</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/OpenClaw-Skill-purple.svg" alt="OpenClaw Skill">
</p>

---

## 功能特点

- 🔍 **智能期刊搜索** - 内置15+领域顶刊数据，支持动态搜索
- 📰 **多源文章获取** - CrossRef API + RSS订阅，自动获取最新论文
- 🌐 **中英双语翻译** - 基于Ollama本地翻译，无需API费用
- 🤖 **AI智能总结** - 基于摘要或全文生成中文总结
- 📄 **PDF下载与解析** - 下载论文PDF并提取文本用于全文总结
- 📊 **Markdown报告** - 按期刊分组，时间倒序，一键生成可读报告

## 安装

### 方式1: Python CLI 安装

```bash
# 克隆仓库
git clone https://github.com/Sen-platotech/paperflow.git
cd paperflow

# 安装
pip install -e .

# 安装PDF支持（可选）
pip install pymupdf

# 安装Ollama模型
ollama pull qwen2.5
```

### 方式2: OpenClaw Skill 安装

```bash
# 在OpenClaw中安装
skillhub install paperflow

# 或手动安装
git clone https://github.com/Sen-platotech/paperflow.git
cd paperflow/skill
```

## 使用方式

### Python CLI

```bash
# 搜索期刊
paperflow search-journals "Artificial Intelligence" --top 10

# 订阅期刊
paperflow subscribe add 2522-5839

# 获取论文
paperflow fetch --days 7

# AI总结
paperflow summarize --days 7 --limit 10

# 生成报告
paperflow report --output report.md --days 7
```

### OpenClaw Skill

```bash
# 搜索期刊
python3 skill/scripts/search_journals.py "Artificial Intelligence" --top 10

# 订阅期刊
python3 skill/scripts/subscribe.py add 2522-5839

# 获取论文
python3 skill/scripts/fetch_papers.py --days 7

# AI总结
python3 skill/scripts/summarize.py --days 7 --limit 10

# 生成报告
python3 skill/scripts/report.py --output report.md --days 7
```

## 支持的领域

**计算机科学**: AI, ML, NLP, CV, Robotics, Data Science
**自然科学**: Biology, Neuroscience, Chemistry, Physics, Materials, Quantum, Climate
**医学**: Medicine, Bioinformatics
**社会科学**: Political Science, Computational Social Science, Economics, Psychology

## 项目结构

```
paperflow/
├── src/paperflow/        # Python包
│   ├── cli.py            # CLI入口
│   ├── core/             # 核心功能
│   ├── models/           # 数据模型
│   └── sources/          # 数据源
├── skill/                # OpenClaw Skill
│   ├── SKILL.md          # Skill描述
│   ├── WORKFLOW.md       # 工作流
│   ├── _meta.json        # 元数据
│   └── scripts/          # 独立脚本
└── README.md
```

## 依赖

```
pip install httpx feedparser beautifulsoup4 sqlalchemy ollama pyyaml
pip install pymupdf  # 可选，PDF支持
```

## License

MIT License

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Sen-platotech">Sen-platotech</a>
</p>
