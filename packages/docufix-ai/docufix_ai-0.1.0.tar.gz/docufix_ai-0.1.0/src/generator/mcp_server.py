import json
import os
import sys

def generate_mcp_config(url: str, title: str) -> dict:
    """
    生成 Model Context Protocol (MCP) 服务器配置文件。
    """
    project_root = os.getcwd()
    config = {
        "mcpServers": {
            "docufix-server": {
                "command": sys.executable,
                "args": [
                    "-m",
                    "src.server"
                ],
                "env": {
                    "PYTHONPATH": project_root
                },
                "tools": [
                    {
                        "name": "search_documentation",
                        "description": f"在 {title} 文档中搜索相关信息。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "要查询的关键词或主题。"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_doc_patch",
                        "description": "获取该文档的 AI 增强 llms.txt 补丁。",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        }
    }
    return config
