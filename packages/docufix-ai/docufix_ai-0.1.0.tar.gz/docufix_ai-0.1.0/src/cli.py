import typer
from rich.console import Console
from rich.table import Table
from .audit.scorer import DocAuditor
from .parser.web import fetch_clean_content

app = typer.Typer(help="DocuFix: AI 文档审计与改造的“灯塔”工具。")
console = Console()

from rich.panel import Panel
from rich.align import Align
from rich.text import Text

from rich.tree import Tree
import time

DOCUFIX_BANNER = """
[bold cyan]
██████╗  ██████╗  ██████╗██╗   ██╗███████╗██╗██╗  ██╗
██╔══██╗██╔═══██╗██╔════╝██║   ██║██╔════╝██║╚██╗██╔╝
██║  ██║██║   ██║██║     ██║   ██║█████╗  ██║ ╚███╔╝ 
██║  ██║██║   ██║██║     ██║   ██║██╔══╝  ██║ ██╔██╗ 
██████╔╝╚██████╔╝╚██████╗╚██████╔╝██║     ██║██╔╝ ██╗
╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝
[/bold cyan]
[dim]AI Documentation Auditor & Fixer v1.0[/dim]
"""

@app.command()
def scan(url: str = typer.Argument(..., help="要审计的文档 URL")):
    """
    运行 AI 兼容性审计 (AI Readability / GEO Scan)
    """
    console.print(DOCUFIX_BANNER)
    
    # --- 1. 颗粒度进度反馈 (Granular Progress) ---
    with console.status("[bold blue]正在初始化...", spinner="dots") as status:
        # Step 1: Connect
        status.update(f"[bold blue]正在连接目标站点: {url}...")
        time.sleep(0.5) # 模拟一点延迟，增加真实感
        console.print(f"[green]✓[/] 已连接: [underline]{url}[/]")
        
        # Step 2: Fetch & Clean
        status.update("[bold blue]正在抓取并清洗 HTML 噪音...")
        content = fetch_clean_content(url)
        console.print(f"[green]✓[/] 内容已净化 ({len(content)} 字符)")
        
        # Step 3: Audit Model
        status.update("[bold blue]正在运行 GEO 审计模型...")
        auditor = DocAuditor()
        report = auditor.audit(content)
        console.print("[green]✓[/] 审计模型推理完成")

    score = report["total_score"]
    
    # --- 2. 文档骨架可视化 (Document Tree) ---
    soup = BeautifulSoup(content, 'html.parser')
    title = soup.find(['h1', 'title'])
    title_text = title.get_text().strip() if title else "Document Root"
    
    tree = Tree(f"[bold white]📄 {title_text}[/]")
    
    # 构建简单的 H2/H3 树
    current_h2 = None
    h2_count = 0
    h3_count = 0
    
    for tag in soup.find_all(['h2', 'h3']):
        text = tag.get_text().strip()[:50] # 截断避免太长
        if tag.name == 'h2':
            current_h2 = tree.add(f"[bold cyan]{text}[/]")
            h2_count += 1
        elif tag.name == 'h3':
            if current_h2:
                current_h2.add(f"[dim]{text}[/]")
            else:
                tree.add(f"[dim]{text}[/]")
            h3_count += 1
            
    # 只显示前 5 个 H2 分支，避免刷屏
    if h2_count > 5:
        tree.add(f"[italic dim]... 以及其他 {h2_count - 5} 个章节[/]")
        
    console.print("\n[bold white]🧠 AI 视角 - 文档结构骨架:[/]")
    console.print(tree)
    console.print(f"[dim]检测到 {h2_count} 个主章节, {h3_count} 个子节点[/]")

    # --- 3. 大部头分数显示 (灯塔效应) ---
    color = "green" if score >= 85 else "yellow" if score >= 60 else "red"
    status_text = "极佳" if score >= 85 else "待改进" if score >= 60 else "较差"
    score_text = Text(f"{score}", style=f"bold {color}", justify="center")
    score_text.append("/100", style="dim")
    
    console.print("\n")
    console.print(Panel(
        Align.center(score_text),
        title=f"[bold white]GEO 评分报告: {url}[/]",
        subtitle=f"[bold {color}]AI 可读性: {status_text}[/]",
        border_style=color,
        padding=(1, 10)
    ))
    
    # --- 2. 详细指标分析 (可解释性) ---
    table = Table(title="诊断详情", box=None, show_header=True, header_style="bold cyan")
    table.add_column("评估维度", style="bold", width=20)
    table.add_column("状态", width=15)
    table.add_column("扣分", style="red", justify="right", width=8)
    table.add_column("原因与修复建议", style="dim")
    
    # 指标映射
    metric_map = {
        "Chunking Structure": "分块健康度",
        "Code Snippets": "代码片段质量",
        "Link Health": "链接健康度",
        "Metadata": "元数据完善度"
    }
    
    for metric_name, data in report["metrics"].items():
        impact = str(data["score_impact"]) if data["score_impact"] != 0 else "0"
        display_name = metric_map.get(metric_name, metric_name)
        
        explanation = f"[bold white]原因:[/] {data['why']}\n[bold green]修复:[/] {data['fix']}"
        table.add_row(
            display_name, 
            data["status"], 
            impact,
            explanation
        )
        table.add_section()
    
    console.print(table)
    
    # --- 3. 激励交互 ---
    if score < 100:
        improvement = 100 - score
        console.print(f"\n[bold yellow]💡 小贴士:[/] 运行 [bold green]docufix fix {url}[/] 即可立即获得 [bold green]+{improvement} 分[/]！")
    else:
        console.print("\n[bold green]🌟 完美![/] 您的文档已 100% 准备好迎接 AI。快去分享您的分数吧！")
        
    # --- 4. 展示 Badge (Social Sharing) ---
    badge_color = "red" if score < 60 else "yellow" if score < 85 else "brightgreen"
    badge_url = f"https://img.shields.io/badge/GEO_Score-{score}/100-{badge_color}"
    console.print(f"\n[bold blue]🏷️  GEO Score Badge (可加入 README):[/]")
    console.print(f"[dim]![DocuFix GEO Score]({badge_url})[/dim]")

from .generator.llms_txt import generate_llms_txt
from .generator.mcp_server import generate_mcp_config
from bs4 import BeautifulSoup
import os
import json

@app.command()
def fix(url: str):
    """
    生成 AI 增强补丁 (llms.txt & MCP Server)
    """
    with console.status(f"[bold green]DocuFix[/] 正在为 {url} 生成 AI 增强补丁...", spinner="earth"):
        content = fetch_clean_content(url)
        soup = BeautifulSoup(content, 'html.parser')
        title = soup.find(['h1', 'title'])
        title_text = title.get_text().strip() if title else "文档索引"
        
        # 1. 生成 llms.txt
        llms_content = generate_llms_txt(url, content)
        with open("llms.txt", "w", encoding="utf-8") as f:
            f.write(llms_content)
            
        # 2. 生成 MCP Server
        mcp_config = generate_mcp_config(url, title_text)
        with open("mcp-server.json", "w", encoding="utf-8") as f:
            json.dump(mcp_config, f, indent=2, ensure_ascii=False)
            
    console.print(f"\n[bold green]成功![/] AI 增强补丁已生成在当前目录：")
    console.print(f"  - [bold yellow]llms.txt[/] ({os.path.getsize('llms.txt')} 字节)")
    console.print(f"  - [bold blue]mcp-server.json[/] (MCP 规范 v1.0)")

if __name__ == "__main__":
    app()
