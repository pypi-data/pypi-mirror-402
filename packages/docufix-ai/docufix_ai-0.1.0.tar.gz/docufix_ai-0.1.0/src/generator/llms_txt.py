from bs4 import BeautifulSoup
import re

def generate_llms_txt(url: str, html_content: str) -> str:
    """
    将 HTML 内容转换为 llms.txt 格式 (Markdown)。
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取标题
    title = soup.find(['h1', 'title'])
    title_text = title.get_text().strip() if title else "文档索引"
    
    # 提取摘要 (前几个段落)
    paragraphs = soup.find_all('p')
    summary = " ".join([p.get_text().strip() for p in paragraphs[:3]])
    
    # 开始构建 Markdown
    lines = []
    lines.append(f"# {title_text}")
    lines.append(f"\n> {summary}\n")
    lines.append(f"来源: {url}\n")
    lines.append("## 文档正文\n")
    
    # 遍历核心内容并转为 Markdown
    for element in soup.find_all(['h2', 'h3', 'p', 'pre', 'ul', 'ol']):
        if element.name in ['h2', 'h3']:
            prefix = "## " if element.name == 'h2' else "### "
            lines.append(f"{prefix}{element.get_text().strip()}")
        elif element.name == 'p':
            lines.append(element.get_text().strip())
        elif element.name == 'pre':
            code = element.get_text().strip()
            lines.append(f"```\n{code}\n```")
        elif element.name in ['ul', 'ol']:
            for li in element.find_all('li'):
                lines.append(f"- {li.get_text().strip()}")
        lines.append("") # 空行分隔
        
    return "\n".join(lines)
