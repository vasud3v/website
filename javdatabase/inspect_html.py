"""
Inspect HTML structure of JAVDatabase video pages
"""

from seleniumbase import Driver
import time

def inspect_video_page(video_code: str):
    """Fetch and save HTML of video page"""
    driver = Driver(uc=True, headless=False)
    
    try:
        url = f"https://www.javdatabase.com/movies/{video_code.lower()}/"
        print(f"Fetching: {url}")
        
        driver.get(url)
        time.sleep(3)
        
        # Save HTML
        html_file = f"database/{video_code}_page.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        print(f"Saved to: {html_file}")
        
        # Keep browser open for manual inspection
        input("\nPress Enter to close browser...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "MIDA-486"
    inspect_video_page(code)
