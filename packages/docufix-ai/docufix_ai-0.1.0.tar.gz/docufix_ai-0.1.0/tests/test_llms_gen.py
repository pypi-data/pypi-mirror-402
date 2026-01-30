from src.generator.llms_txt import generate_llms_txt

def test_llms_generation():
    url = "https://example.com/docs"
    html_content = """
    <html>
    <body>
        <h1>DocuFix Guide</h1>
        <p>DocuFix is a tool that audits and fixes AI documentation compatibility.</p>
        <p>It helps developers ensure their docs are RAG-friendly.</p>
        <h2>Installation</h2>
        <p>Use pip to install the package.</p>
        <pre><code>pip install docufix-cli</code></pre>
        <h2>Usage</h2>
        <ul>
            <li>Run <code>scan</code> to audit</li>
            <li>Run <code>fix</code> to patch</li>
        </ul>
    </body>
    </html>
    """
    
    print("Generating llms.txt...")
    llms_txt = generate_llms_txt(url, html_content)
    
    print("\n--- Generated llms.txt ---")
    print(llms_txt)
    print("--- End of File ---")
    
    # 简单验证
    assert "# DocuFix Guide" in llms_txt
    assert "> DocuFix is a tool" in llms_txt
    assert "## Installation" in llms_txt
    assert "```\npip install docufix-cli\n```" in llms_txt
    assert "- Run scan to audit" in llms_txt
    
    print("\n✅ Verification SUCCESS: llms.txt format is correct.")

if __name__ == "__main__":
    test_llms_generation()
