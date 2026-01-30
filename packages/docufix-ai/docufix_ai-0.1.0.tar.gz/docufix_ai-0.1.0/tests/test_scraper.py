from src.parser.web import fetch_clean_content

def test_scraper():
    url = "https://docs.python.org/3/"
    print(f"Testing scraper with {url}...")
    content = fetch_clean_content(url)
    
    # 打印前 500 个字符进行验证
    print("\n--- Extracted Content (First 500 chars) ---")
    print(content[:500])
    print("\n--- End of Preview ---")
    
    # 简单断言
    if "Python 3.13.1 documentation" in content or "Python" in content:
        print("\n✅ Verification SUCCESS: Found expected keywords.")
    else:
        print("\n❌ Verification FAILED: Keywords not found.")
        
    if "<nav" in content or "<footer>" in content:
        print("⚠️ Warning: Noise (nav/footer) might still be present.")
    else:
        print("✅ Noise reduction seems effective.")

if __name__ == "__main__":
    test_scraper()
