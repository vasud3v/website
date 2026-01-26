#!/usr/bin/env python3
"""
Test deleted video detection
"""

import sys
sys.path.insert(0, '..')

from javmix_scraper import JavmixScraper

# Test URLs
test_urls = [
    "https://javmix.tv/video/aukg-603/",  # Should work
    "https://javmix.tv/video/fake-deleted-123/",  # Should be 404
]

scraper = JavmixScraper(headless=True)

for url in test_urls:
    print(f"\n{'='*70}")
    print(f"Testing: {url}")
    print(f"{'='*70}")
    
    result = scraper.scrape_video(url)
    
    if result:
        print(f"✅ SUCCESS - Video scraped")
        print(f"   Code: {result.code}")
        print(f"   Title: {result.title[:50]}...")
        print(f"   Video URLs: {len(result.embed_urls)}")
    else:
        print(f"❌ FAILED - Video not available or deleted")

scraper.close()
