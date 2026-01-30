import tiktoken
from bs4 import BeautifulSoup
import re

class ContextAuditor:
    """
    检测长文本缺乏结构化标题的风险。
    """
    def __init__(self):
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = 512

    def audit_chunking_risk(self, text: str) -> dict:
        tokens = self.encoder.encode(text)
        chunks = [tokens[i:i+self.chunk_size] for i in range(0, len(tokens), self.chunk_size)]
        
        high_risk_chunks = 0
        for chunk in chunks:
            chunk_text = self.encoder.decode(chunk)
            if not re.search(r'(#+ |<h[1-6]>)', chunk_text):
                high_risk_chunks += 1
        
        penalty = min(40, high_risk_chunks * 10)
        return {
            "score_impact": -penalty,
            "status": "🚨 高风险" if high_risk_chunks > 0 else "✅ 已优化",
            "reason": f"发现 {high_risk_chunks} 个长文本块（>512 tokens）缺少标题结构。",
            "why": "AI RAG 系统通过切片索引内容。如果没有标题，AI 在检索时会丢失章节上下文（例如：不知道这段话对应哪个 API）。",
            "fix": "每隔 300-500 个 tokens 插入 Markdown 标题（###）以维持上下文连贯性。"
        }

class CodeAuditor:
    """
    检测代码块的 AI 可读性（注释、Import）。
    """
    def audit_code_blocks(self, soup: BeautifulSoup) -> dict:
        code_blocks = soup.find_all(['code', 'pre'])
        if not code_blocks:
            return {
                "score_impact": 0, 
                "status": "✅ 无代码", 
                "reason": "未检测到代码块。",
                "why": "不适用",
                "fix": "不适用"
            }
        
        penalty = 0
        total_blocks = len(code_blocks)
        bad_blocks = 0
        
        for block in code_blocks:
            text = block.get_text()
            lines = text.split('\n')
            if len(lines) > 5:
                has_comment = "#" in text or "//" in text or "/*" in text
                has_import = any(kw in text for kw in ["import ", "from ", "require(", "using "])
                
                if not has_comment or not has_import:
                    penalty += 5
                    bad_blocks += 1
        
        penalty = min(30, penalty)
        return {
            "score_impact": -penalty,
            "status": "⚠️ 缺少文档" if bad_blocks > 0 else "✅ AI 友好",
            "reason": f"发现 {bad_blocks}/{total_blocks} 个代码片段缺少注释或 import 语句。",
            "why": "如果 AI 看不到完整的依赖或逻辑注释，在生成代码时极易产生“幻觉”。",
            "fix": "确保每个代码片段都是自包含的，包含必要的库引用和简要逻辑注释。"
        }

class DocAuditor:
    """
    AI 文档审计核心类。
    """
    def __init__(self):
        self.context_auditor = ContextAuditor()
        self.code_auditor = CodeAuditor()

    def audit(self, html_content: str) -> dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        
        chunk_report = self.context_auditor.audit_chunking_risk(text)
        code_report = self.code_auditor.audit_code_blocks(soup)
        
        # 暂时模拟链接和元数据分数
        link_report = {
            "score_impact": 0, 
            "status": "✅ 链接健康", 
            "reason": "所有内外链均有效。",
            "why": "失效链接会导致 AI 在递归爬取时陷入死胡同，中断推理。",
            "fix": "不适用"
        }
        meta_report = {
            "score_impact": -5, 
            "status": "⚠️ 缺少元数据", 
            "reason": "缺少 Meta Description 或 Keywords 标签。",
            "why": "缺失元数据会降低模型在预处理阶段对站点的分类准确度。",
            "fix": "在 HTML 源码中添加 <meta name='description' content='...'>。"
        }
        
        total_score = 100 + chunk_report["score_impact"] + code_report["score_impact"] + link_report["score_impact"] + meta_report["score_impact"]
        total_score = max(0, min(100, total_score))
        
        return {
            "total_score": total_score,
            "metrics": {
                "Chunking Structure": chunk_report,
                "Code Snippets": code_report,
                "Link Health": link_report,
                "Metadata": meta_report
            }
        }
