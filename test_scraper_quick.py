"""
Quick test script to verify scraper can load pages and find video links
"""
import sys
sys.path.insert(0, 'jable')

from jable_scraper import JableScraper

def test_scraper():
    scraper = JableScraper(headless=True)
    
    try:
        print("\n" + "="*60)
        print("QUICK SCRAPER TEST - LINK DISCOVERY ONLY")
        print("="*60)
        
        # Test homepage link discovery
        print("\nTesting homepage...")
        links = scraper.get_video_links_from_page("https://jable.tv/")
        
        print(f"\n{'='*60}")
        print(f"RESULT")
        print('='*60)
        print(f"✅ Found {len(links)} video links")
        
        if links:
            print(f"\nFirst 5 links:")
            for i, link in enumerate(links[:5], 1):
                print(f"  {i}. {link}")
        
        return len(links) > 0
        
    finally:
        scraper.close()

if __name__ == "__main__":
    success = test_scraper()
    sys.exit(0 if success else 1)
