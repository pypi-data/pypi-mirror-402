from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def fetch_clean_content(url: str) -> str:
    """
    使用 Playwright 强制抓取页面内容，并清理不必要的 HTML 标签。
    支持 SPA (如 Docusaurus) 和传统文档框架。
    """
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 访问 URL，直到网络闲置（适用于单页应用）
            page.goto(url, wait_until="networkidle")
            
            # 获取完整页面内容
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. 尝试精确定位主体内容 (Docusaurus/MkDocs/Sphinx 通用)
            main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
            
            if not main_content:
                # 如果没找到特定容器，退而求其次使用 body
                main_content = soup.find('body')
            
            # 2. 清理噪音 (导航、页脚、脚本等)
            for noise in main_content.find_all(['nav', 'footer', 'header', 'script', 'style', 'aside']):
                noise.decompose()
                
            return str(main_content)
            
        except Exception as e:
            return f"无法获取 URL {url}: {str(e)}"
        finally:
            browser.close()
