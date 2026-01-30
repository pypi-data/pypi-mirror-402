from src.audit.scorer import DocAuditor

def test_audit_scenarios():
    auditor = DocAuditor()
    
    # 场景 1: "好"文档 (结构清晰, 代码有注释)
    good_doc = """
    <html>
    <body>
        <article>
            <h1>Getting Started</h1>
            <p>This is a great tool for AI documentation.</p>
            <h2>Installation</h2>
            <p>Run the following command to install.</p>
            <pre><code>
            # Import the necessary library
            import docufix
            
            # Initialize the auditor
            auditor = docufix.DocAuditor()
            </code></pre>
        </article>
    </body>
    </html>
    """
    
    # 场景 2: "坏"文档 (一大堆文字没标题, 代码没注释没 import)
    bad_doc = "<html><body><main>" + "A long sentence about nothing helpful. " * 100 + """
    <pre><code>
    x = 10
    y = 20
    print(x + y)
    print("No context here")
    print("Still no context")
    print("Where am I?")
    </code></pre>
    </main></body></html>
    """
    
    print("Testing 'Good' Document...")
    report_good = auditor.audit(good_doc)
    print(f"Score: {report_good['total_score']}")
    for m, d in report_good['metrics'].items():
        print(f"  - {m}: {d['status']} ({d['score_impact']})")
        
    print("\nTesting 'Bad' Document...")
    report_bad = auditor.audit(bad_doc)
    print(f"Score: {report_bad['total_score']}")
    for m, d in report_bad['metrics'].items():
        print(f"  - {m}: {d['status']} ({d['score_impact']})")

    # 断言
    assert report_good['total_score'] > report_bad['total_score']
    print("\n✅ Verification SUCCESS: 'Good' doc scored higher than 'Bad' doc.")

if __name__ == "__main__":
    test_audit_scenarios()
