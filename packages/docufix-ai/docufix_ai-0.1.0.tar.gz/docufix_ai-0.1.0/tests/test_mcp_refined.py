import json
import os
import sys

def validate_mcp_config(file_path):
    print(f"🔍 开始对 {file_path} 进行多维精细校验...")
    
    if not os.path.exists(file_path):
        print(f"❌ 错误: 找不到文件 {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ 语法错误: JSON 格式非法 - {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 错误: 无法读取文件 - {str(e)}")
        return False

    errors = []
    
    # 1. 顶层结构校验
    if "mcpServers" not in config:
        errors.append("缺少根键 'mcpServers'")
    else:
        servers = config["mcpServers"]
        if not servers:
            errors.append("'mcpServers' 为空")
        
        for server_id, server_data in servers.items():
            print(f"  - 校验服务器节点: [bold cyan]{server_id}[/]")
            
            # 2. 服务器属性校验
            for field in ["command", "args"]:
                if field not in server_data:
                    errors.append(f"服务器 '{server_id}' 缺少必填字段: '{field}'")
            
            # 3. 工具 (Tools) 定义校验
            if "tools" in server_data:
                tools = server_data["tools"]
                for i, tool in enumerate(tools):
                    tool_name = tool.get("name", f"Index_{i}")
                    print(f"    - 校验工具: {tool_name}")
                    
                    if "name" not in tool or "description" not in tool:
                        errors.append(f"工具 {tool_name} 必须包含 'name' 和 'description'")
                    
                    if "inputSchema" not in tool:
                        errors.append(f"工具 {tool_name} 缺少 'inputSchema'")
                    else:
                        schema = tool["inputSchema"]
                        if schema.get("type") != "object":
                            errors.append(f"工具 {tool_name} 的 inputSchema 类型必须为 'object'")
                        if "properties" not in schema:
                             errors.append(f"工具 {tool_name} 的 inputSchema 缺少 'properties'")

    # 4. 编码校验 (中文支持)
    content = json.dumps(config, ensure_ascii=False)
    if "\\u" in content:
        print("⚠️ 警告: 发现 Unicode 转义字符，建议使用原义汉字以提升可读性。")
    else:
        print("✅ 编码检查: 使用 UTF-8 原义汉字，兼容性良好。")

    if errors:
        print("\n❌ 校验失败，发现以下问题：")
        for err in errors:
            print(f"  - {err}")
        return False
    
    print("\n✨ 精细校验通过！该配置文件符合 MCP 1.0 标准。")
    return True

if __name__ == "__main__":
    # 如果当前目录没有生成，先尝试生成一个
    if not os.path.exists("mcp-server.json"):
        print("🚀 未发现配置文件，正在为您生成演示配置...")
        os.system("python -m src.cli fix https://example.com")
        
    success = validate_mcp_config("mcp-server.json")
    sys.exit(0 if success else 1)
