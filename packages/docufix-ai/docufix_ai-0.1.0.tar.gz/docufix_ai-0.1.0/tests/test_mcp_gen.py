from src.generator.mcp_server import generate_mcp_config
import json

def test_mcp_generation():
    url = "https://example.com/api"
    title = "Example API Docs"
    
    print("Generating MCP config...")
    config = generate_mcp_config(url, title)
    
    print("\n--- Generated mcp-server.json ---")
    print(json.dumps(config, indent=2))
    print("--- End of File ---")
    
    # 验证结构
    assert "mcpServers" in config
    assert "docufix-server" in config["mcpServers"]
    server = config["mcpServers"]["docufix-server"]
    assert server["command"] == "npx"
    assert url in server["args"]
    
    # 验证 Tools
    tools = server["tools"]
    tool_names = [t["name"] for t in tools]
    assert "search_documentation" in tool_names
    assert "get_doc_patch" in tool_names
    
    print("\n✅ Verification SUCCESS: MCP configuration is valid.")

if __name__ == "__main__":
    test_mcp_generation()
