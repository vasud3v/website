"""
Single video scraper for JAVDatabase with comprehensive error handling
Called by Jable scraper after each video is processed
"""

import json
import time
import sys
from pathlib import Path
from dataclasses import asdict
from scrape_clean import CleanJAVDBScraper


class SingleVideoScraper:
    """Scrape single video with robust error handling"""
    
    def __init__(self, headless=True, timeout=300):
        self.headless = headless
        self.timeout = timeout
        self.scraper = None
        self.max_retries = 3
        self.retry_delay = 10
    
    def scrape(self, video_code: str) -> dict:
        """
        Scrape single video with comprehensive error handling
        
        Returns:
            dict: Video metadata or None if failed
        """
        print(f"\n{'='*60}")
        print(f"JAVDatabase: Scraping {video_code}")
        print(f"{'='*60}")
        
        # Normalize code
        video_code = video_code.upper().strip()
        
        # Try scraping with retries
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    print(f"  Retry attempt {attempt + 1}/{self.max_retries}")
                    time.sleep(self.retry_delay * attempt)  # Exponential backoff
                
                # Initialize scraper if needed
                if self.scraper is None:
                    self.scraper = CleanJAVDBScraper(headless=self.headless)
                    self.scraper._init_driver()
                
                # Set timeout
                self.scraper.driver.set_page_load_timeout(self.timeout)
                
                # Scrape video
                video_data = self.scraper.scrape_video_by_code(video_code)
                
                if video_data:
                    print(f"  ✅ Successfully scraped {video_code}")
                    return asdict(video_data)
                else:
                    print(f"  ⚠️ Video not found on JAVDatabase")
                    return None
                    
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ Error: {error_msg}")
                
                # Handle specific errors
                if "timeout" in error_msg.lower():
                    print(f"  ⏱️ Timeout occurred, will retry...")
                elif "connection" in error_msg.lower():
                    print(f"  🔌 Connection error, will retry...")
                elif "rate limit" in error_msg.lower():
                    print(f"  🚦 Rate limited, waiting longer...")
                    time.sleep(30)
                else:
                    print(f"  🐛 Unexpected error: {error_msg}")
                
                # Restart browser on last attempt
                if attempt == self.max_retries - 1:
                    print(f"  🔄 Final attempt, restarting browser...")
                    self.close()
                    self.scraper = None
        
        print(f"  ❌ Failed to scrape {video_code} after {self.max_retries} attempts")
        return None
    
    def close(self):
        """Close scraper safely"""
        if self.scraper:
            try:
                self.scraper.close()
            except:
                pass
            self.scraper = None


def scrape_single_video(video_code: str, headless: bool = True) -> dict:
    """
    Main function to scrape single video
    
    Args:
        video_code: Video code like "MIDA-486"
        headless: Run browser in headless mode
    
    Returns:
        dict: Video metadata or None if failed
    """
    scraper = SingleVideoScraper(headless=headless)
    
    try:
        result = scraper.scrape(video_code)
        return result
    finally:
        scraper.close()


if __name__ == "__main__":
    # Test mode
    if len(sys.argv) < 2:
        print("Usage: python scrape_single.py <video_code>")
        print("Example: python scrape_single.py MIDA-486")
        sys.exit(1)
    
    code = sys.argv[1]
    result = scrape_single_video(code, headless=True)
    
    if result:
        print(f"\n✅ Success!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ Failed to scrape {code}")
        sys.exit(1)
