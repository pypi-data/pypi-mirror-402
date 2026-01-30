# DocuFix: AI 兼容性审计与增强套件

> [!TIP]
> **让你的文档不再是 AI 的“幻觉来源”，而是它的“知识引擎”。**

**DocuFix** 是专为 AI 时代设计的文档优化工具 (GEO - Generative Engine Optimization)。它通过模拟 RAG 系统的检索逻辑，一键检测并修复文档中的 AI 可读性缺陷。

## 🌟 核心理念：GEO (生成引擎优化)

在 AI 驱动开发的今天，文档的价值不再仅仅取决于人类是否好读，而取决于 **AI Agent 是否好用**。DocuFix 帮助您：
- **消除幻觉**：确保代码片段自包含，包含必要的注释和引用。
- **防止断层**：优化分块结构，确保 AI 在检索时不会丢失上下文。
- **主动交互**：将文档转化为 **MCP (Model Context Protocol)** 工具。

## 🚀 快速开始

### 1. 安装
```bash
# 克隆仓库
git clone https://github.com/your-repo/docufix.git
cd docufix

# 安装依赖
pip install -e .

# 安装浏览器内核 (用于抓取动态页面)
playwright install chromium
```

### 2. 运行审计 (GEO Scan)
一键获取文档的“灯塔”评分报告：
```bash
python -m src.cli scan https://example.com/docs
```

### 3. 一键修复与增强 (GEO Fix)
生成专为 AI 设计的补丁文件：
```bash
python -m src.cli fix https://example.com/docs
```
完成后将产出：
- `llms.txt`: 极简 Markdown 索引，适合 RAG 投喂。
- `mcp-server.json`: 本地 MCP 服务器配置，可挂载至 Cursor/Claude。

## 🧩 MCP 挂载指南

1. 运行 `fix` 命令生成 `mcp-server.json`。
2. 拷贝 JSON 中的配置到您的 MCP 客户端。
3. **享受超能力**：直接在对话中输入“查询文档中关于 XXX 的内容”，AI 将自动调用 DocuFix 工具。

## 📈 审计维度 (GEO Metrics)

- **分块健康度 (40%)**: 检测长文本是否缺少标题导致语义漂移。
- **代码可读性 (30%)**: 检查代码块是否包含必要的 Import 和注释。
- **元数据与链接 (30%)**: 确保 SEO/GEO 元数据完整且无死链。

## 🏷️ GEO Score Badge
成功审计后，您可以将 Badge 添加到您的项目 README 中：
`![DocuFix GEO Score](https://img.shields.io/badge/GEO_Score-95/100-green)`

## 📜 开源协议
本项目采用 [MIT License](LICENSE) 协议开源。
