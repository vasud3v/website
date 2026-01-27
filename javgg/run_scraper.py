#!/usr/bin/env python3
"""
Run the scraper with test URLs
"""

from javgg_scraper import JavaGGScraper
import time

# Test URLs
video_urls = [
    "https://javgg.net/jav/start-508/",
]

print("="*70)
print("  JAVGG.NET SCRAPER - AUTO RUN")
print("="*70)
print(f"\n📊 Processing {len(video_urls)} videos...")

scraper = JavaGGScraper(headless=False)

try:
    success = 0
    failed = 0
    
    for i, url in enumerate(video_urls, 1):
        print(f"\n{'='*70}")
        print(f"Video {i}/{len(video_urls)}")
        print(f"{'='*70}")
        
        if scraper.scrape_and_download(url):
            success += 1
        else:
            failed += 1
        
        time.sleep(2)
    
    print(f"\n{'='*70}")
    print("COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Files: {scraper.download_dir}")
    print(f"{'='*70}")
    
finally:
    scraper.close()
