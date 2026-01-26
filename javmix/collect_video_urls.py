#!/usr/bin/env python3
"""
Comprehensive Video URL Collector for Javmix.TV
Combines multiple sources: RSS feeds, homepage, category pages
FAST and RELIABLE alternative to slow sitemaps
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Dict, Set
import xml.etree.ElementTree as ET


class VideoURLCollector:
    """Fast video URL collector using multiple sources"""
    
    BASE_URL = "https://javmix.tv"
    
    def __init__(self, timeout=5, max_workers=5):
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url):
        """Fetch page with timeout"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return response.text
        except:
            pass
        return None
    
    def extract_from_rss(self) -> Set[str]:
        """Extract URLs from RSS feeds (FAST - usually works)"""
        print("\n📡 Extracting from RSS feeds...")
        
        rss_feeds = [
            f"{self.BASE_URL}/feed/",
            f"{self.BASE_URL}/rss/",
            f"{self.BASE_URL}/?feed=rss2",
            f"{self.BASE_URL}/?feed=rss",
            f"{self.BASE_URL}/?feed=atom",
        ]
        
        video_urls = set()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_feed = {executor.submit(self.fetch_page, feed): feed for feed in rss_feeds}
            
            for future in as_completed(future_to_feed):
                feed_url = future_to_feed[future]
                content = future.result()
                
                if content:
                    try:
                        # Parse RSS/Atom XML
                        root = ET.fromstring(content)
                        
                        # Try RSS format
                        for item in root.findall('.//item/link'):
                            url = item.text
                            if url and ('/video/' in url or '/fc2ppv/' in url or '/xvideo/' in url):
                                video_urls.add(url)
                        
                        # Try Atom format
                        for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}link'):
                            url = entry.get('href')
                            if url and ('/video/' in url or '/fc2ppv/' in url or '/xvideo/' in url):
                                video_urls.add(url)
                        
                        if video_urls:
                            print(f"  ✅ {feed_url.split('/')[-2] or 'feed'}: {len(video_urls)} URLs")
                    except:
                        pass
        
        print(f"  📊 Total from RSS: {len(video_urls)} URLs")
        return video_urls
    
    def extract_from_page(self, page_url) -> Set[str]:
        """Extract video URLs from a single page"""
        video_urls = set()
        
        content = self.fetch_page(page_url)
        if not content:
            return video_urls
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all video links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Match video URLs
            if re.search(r'/(video|fc2ppv|xvideo)/[^/]+/?$', href):
                # Normalize URL
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = f"{self.BASE_URL}{href}"
                else:
                    full_url = f"{self.BASE_URL}/{href}"
                
                video_urls.add(full_url)
        
        return video_urls
    
    def extract_from_homepage(self, num_pages=3) -> Set[str]:
        """Extract URLs from homepage pages (FAST)"""
        print(f"\n🏠 Extracting from homepage ({num_pages} pages)...")
        
        page_urls = [self.BASE_URL]
        page_urls.extend([f"{self.BASE_URL}/page/{i}/" for i in range(2, num_pages + 1)])
        
        all_video_urls = set()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {executor.submit(self.extract_from_page, url): url for url in page_urls}
            
            for future in as_completed(future_to_page):
                page_url = future_to_page[future]
                video_urls = future.result()
                
                if video_urls:
                    all_video_urls.update(video_urls)
                    page_num = page_url.split('/')[-2] if '/page/' in page_url else '1'
                    print(f"  ✅ Page {page_num}: {len(video_urls)} URLs")
        
        print(f"  📊 Total from homepage: {len(all_video_urls)} URLs")
        return all_video_urls
    
    def extract_from_category(self, category, num_pages=2) -> Set[str]:
        """Extract URLs from category pages"""
        print(f"\n📂 Extracting from category: {category} ({num_pages} pages)...")
        
        page_urls = [f"{self.BASE_URL}/{category}/"]
        page_urls.extend([f"{self.BASE_URL}/{category}/page/{i}/" for i in range(2, num_pages + 1)])
        
        all_video_urls = set()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {executor.submit(self.extract_from_page, url): url for url in page_urls}
            
            for future in as_completed(future_to_page):
                page_url = future_to_page[future]
                video_urls = future.result()
                
                if video_urls:
                    all_video_urls.update(video_urls)
                    page_num = page_url.split('/')[-2] if '/page/' in page_url else '1'
                    print(f"  ✅ Page {page_num}: {len(video_urls)} URLs")
        
        print(f"  📊 Total from {category}: {len(all_video_urls)} URLs")
        return all_video_urls
    
    def collect_all(self, homepage_pages=3, categories=None, category_pages=2) -> Dict:
        """Collect URLs from all sources"""
        
        all_urls = set()
        sources = {}
        
        # 1. RSS feeds (fastest, most reliable)
        rss_urls = self.extract_from_rss()
        all_urls.update(rss_urls)
        sources['rss'] = len(rss_urls)
        
        # 2. Homepage
        homepage_urls = self.extract_from_homepage(num_pages=homepage_pages)
        all_urls.update(homepage_urls)
        sources['homepage'] = len(homepage_urls)
        
        # 3. Categories (optional)
        if categories:
            for category in categories:
                cat_urls = self.extract_from_category(category, num_pages=category_pages)
                all_urls.update(cat_urls)
                sources[f'category_{category}'] = len(cat_urls)
        
        # Categorize by type
        regular = [url for url in all_urls if '/video/' in url]
        fc2ppv = [url for url in all_urls if '/fc2ppv/' in url]
        xvideo = [url for url in all_urls if '/xvideo/' in url]
        
        return {
            'total': len(all_urls),
            'regular': len(regular),
            'fc2ppv': len(fc2ppv),
            'xvideo': len(xvideo),
            'sources': sources,
            'urls': {
                'all': sorted(list(all_urls)),
                'regular': sorted(regular),
                'fc2ppv': sorted(fc2ppv),
                'xvideo': sorted(xvideo)
            }
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fast Video URL Collector for Javmix.TV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick collection (RSS + 3 homepage pages)
  python collect_video_urls.py
  
  # More URLs (RSS + 5 homepage pages)
  python collect_video_urls.py --homepage 5
  
  # Include categories
  python collect_video_urls.py --homepage 3 --categories fc2ppv xvideo --category-pages 2
  
  # Maximum speed
  python collect_video_urls.py --homepage 10 --workers 10
        """
    )
    
    parser.add_argument('--homepage', type=int, default=3, help='Number of homepage pages (default: 3)')
    parser.add_argument('--categories', nargs='+', help='Categories to scrape (e.g., fc2ppv xvideo)')
    parser.add_argument('--category-pages', type=int, default=2, help='Pages per category (default: 2)')
    parser.add_argument('--workers', type=int, default=5, help='Concurrent workers (default: 5)')
    parser.add_argument('--timeout', type=int, default=5, help='Request timeout in seconds (default: 5)')
    parser.add_argument('--output', default='collected_urls.json', help='Output file (default: collected_urls.json)')
    parser.add_argument('--sample', type=int, default=20, help='Number of random samples (default: 20)')
    
    args = parser.parse_args()
    
    print("="*70)
    print("🚀 JAVMIX.TV VIDEO URL COLLECTOR - FAST & RELIABLE")
    print("="*70)
    print(f"Configuration:")
    print(f"  - Homepage pages: {args.homepage}")
    print(f"  - Categories: {args.categories or 'None'}")
    print(f"  - Category pages: {args.category_pages if args.categories else 'N/A'}")
    print(f"  - Workers: {args.workers}")
    print(f"  - Timeout: {args.timeout}s")
    print("="*70)
    
    start_time = time.time()
    
    # Collect URLs
    collector = VideoURLCollector(timeout=args.timeout, max_workers=args.workers)
    result = collector.collect_all(
        homepage_pages=args.homepage,
        categories=args.categories,
        category_pages=args.category_pages
    )
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*70}")
    print(f"✅ COLLECTION COMPLETE")
    print(f"{'='*70}")
    print(f"Total unique URLs: {result['total']}")
    print(f"⚡ Time taken: {elapsed:.1f}s")
    print(f"⚡ Speed: {result['total']/elapsed:.1f} URLs/sec")
    
    print(f"\nBreakdown by type:")
    print(f"  - Regular videos (/video/): {result['regular']}")
    print(f"  - FC2PPV videos (/fc2ppv/): {result['fc2ppv']}")
    print(f"  - XVideo videos (/xvideo/): {result['xvideo']}")
    
    print(f"\nBreakdown by source:")
    for source, count in result['sources'].items():
        print(f"  - {source}: {count} URLs")
    
    # Save to file
    result['collection_time'] = f"{elapsed:.1f}s"
    result['collection_speed'] = f"{result['total']/elapsed:.1f} URLs/sec"
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to: {args.output}")
    
    # Show random samples
    import random
    all_urls = result['urls']['all']
    sample_size = min(args.sample, len(all_urls))
    samples = random.sample(all_urls, sample_size)
    
    print(f"\n📋 Random samples ({sample_size}):")
    for i, url in enumerate(samples, 1):
        # Extract code from URL
        code_match = re.search(r'/(video|fc2ppv|xvideo)/([^/]+)', url)
        if code_match:
            code = code_match.group(2).upper()
            print(f"  {i:2d}. {code:20s} {url}")
        else:
            print(f"  {i:2d}. {url}")
    
    # Save samples for testing
    test_file = "collected_test_urls.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        for url in samples:
            f.write(url + '\n')
    
    print(f"\n💾 Test URLs saved to: {test_file}")
    
    # Performance summary
    print(f"\n📊 Performance Summary:")
    print(f"  ✅ Fast: {elapsed:.1f}s for {result['total']} URLs")
    print(f"  ✅ Reliable: Multiple sources (RSS + homepage + categories)")
    print(f"  ✅ Concurrent: {args.workers} parallel workers")
    
    if elapsed < 30:
        print(f"\n🎉 Excellent speed! Collection completed in under 30 seconds.")
    
    print(f"\n💡 Next steps:")
    print(f"  1. Use collected URLs with scraper:")
    print(f"     python javmix_scraper.py --url <URL> --output video.json")
    print(f"  2. Batch scrape from test file:")
    print(f"     for url in $(cat {test_file}); do python javmix_scraper.py --url $url; done")


if __name__ == "__main__":
    main()
