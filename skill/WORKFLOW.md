# Paperflow Workflow

完整的工作流程指南。

## 工作流程 1: 发现顶刊

**场景**: 用户想要了解某个领域的顶级期刊

**步骤**:
1. 用户提问："AI领域有哪些顶刊？"
2. 使用 `search_journals.py` 搜索：
   ```bash
   python3 scripts/search_journals.py "Artificial Intelligence" --top 10
   ```
3. 返回期刊列表，包含：名称、ISSN、出版社、SJR分数
4. 用户可以选择订阅感兴趣的期刊

**输出示例**:
```
Found 5 top journals from database
1. Nature Machine Intelligence (2522-5839) - Springer Nature
2. Journal of Machine Learning Research (1532-4435) - JMLR
3. IEEE TPAMI (0162-8828) - IEEE
4. Artificial Intelligence (0004-3702) - Elsevier
5. Machine Learning (0885-6125) - Springer
```

## 工作流程 2: 订阅与获取论文

**场景**: 用户想跟踪特定期刊的最新论文

**步骤**:
1. 订阅期刊：
   ```bash
   python3 scripts/subscribe.py add 2522-5839
   ```
2. 获取最新论文：
   ```bash
   python3 scripts/fetch_papers.py --days 7
   ```
3. 系统自动：
   - 从CrossRef/RSS获取论文元数据
   - 翻译标题和摘要（可选）
   - 存储到本地数据库

**输出示例**:
```json
{
  "fetched": 15,
  "translated": 15,
  "journals": ["Nature Machine Intelligence"]
}
```

## 工作流程 3: AI总结论文

**场景**: 用户想要论文的中文总结

**步骤**:
1. 基于摘要总结（快速）：
   ```bash
   python3 scripts/summarize.py --days 7 --limit 10
   ```
2. 或基于全文总结（详细）：
   ```bash
   python3 scripts/summarize.py --days 7 --fulltext --limit 5
   ```
3. 系统自动：
   - 提取未总结的论文
   - 调用Ollama生成中文总结
   - 如需全文，下载PDF并提取文本

**输出示例**:
```
[1/3] Machine learning global atomic representations...
  ✓ Summary generated

Summary: 本文提出了一种基于欧几里得快速注意力机制的原子表示学习方法...
```

## 工作流程 4: 生成报告

**场景**: 用户想要一份汇总报告

**步骤**:
1. 生成报告：
   ```bash
   python3 scripts/report.py --output ai_papers.md --days 7
   ```
2. 报告包含：
   - 目录（按期刊分组）
   - 每篇论文：标题、作者、摘要、译文、AI总结、链接

**报告格式**:
```markdown
# 学术论文聚合报告

**时间范围:** 2024-01-15 ~ 2024-01-22

## Nature Machine Intelligence

### 1. Title...
**译名:** ...

**🤖 AI总结:**
> ...

**链接:** [原文] | [PDF] | [DOI]
```

## 自动化工作流

可以设置定时任务：

```bash
# 每天获取新论文
0 9 * * * cd /path/to/paperflow-skill && python3 scripts/fetch_papers.py --days 1

# 每周生成报告
0 10 * * 1 cd /path/to/paperflow-skill && python3 scripts/report.py --days 7 --output weekly.md
```
