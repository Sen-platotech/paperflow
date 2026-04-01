# Paperflow

"你这周看了几篇论文？"
"顶刊都有哪些？"
"文献综述写得怎么样了？"
"这个问题有人研究过吗？"
"这个领域的最新进展是什么？"

License: MIT | Python 3.10+ | OpenClaw Skill | Claude Code Compatible

---

你导师问你最近看了什么论文，你支支吾吾说在找？
你老板让你写文献综述，你打开 Google Scholar 手动一篇篇搜？
你想投顶刊但不知道这个领域哪些是顶刊？
你刷到一篇好论文，想找同类型的却发现已经晚了三个月？
你看到一堆英文摘要，翻译软件开了又关关了又开？

别再用浏览器收藏夹假装自己在做科研了，欢迎加入 Paperflow！

一键搜索 15+ 领域顶刊，自动订阅、自动获取、自动翻译、自动总结。
你的 AI 助手每天帮你刷论文，你只管读你感兴趣的。

**安装 · 使用 · 支持领域 · 效果示例 · Skill 版本**

---

<p align="center">
  <strong>📚 学术期刊聚合工具</strong><br>
  <sub>搜索顶刊 · 获取论文 · AI总结 · 双语报告</sub>
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
