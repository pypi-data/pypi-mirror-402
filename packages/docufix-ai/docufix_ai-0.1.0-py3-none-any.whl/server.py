import asyncio
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio
import sys

# 创建 MCP 服务器
server = Server("docufix-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    列出可用的工具。
    """
    return [
        Tool(
            name="search_documentation",
            description="在文档中搜索相关信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_doc_patch",
            description="获取该文档的 AI 增强 llms.txt 补丁。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[TextContent]:
    """
    处理工具调用。
    """
    if name == "search_documentation":
        query = arguments.get("query", "")
        # 这里集成实际的搜索逻辑，暂时返回模拟结果
        return [TextContent(type="text", text=f"正在搜索关于 '{query}' 的内容...目前该工具已连接至 DocuFix 核心。")]
    
    if name == "get_doc_patch":
        # 返回已生成的 llms.txt 内容（如果存在）
        try:
            with open("llms.txt", "r", encoding="utf-8") as f:
                content = f.read()
            return [TextContent(type="text", text=content)]
        except:
            return [TextContent(type="text", text="未找到 llms.txt。请先运行 docufix fix <url>。")]
            
    raise ValueError(f"Unknown tool: {name}")

async def main():
    # 使用 stdio 传输运行服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="docufix-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
