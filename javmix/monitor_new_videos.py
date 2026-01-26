#!/usr/bin/env python3
"""
Monitor Javmix.TV for New Videos
Continuously checks for new videos and tracks them in database
Uses multiple sources: RSS, homepage, sitemap updates
"""

import requests
import xml.etree.ElementTree as ET
import json
import time
import os
from datetime import datetime
from typing import Set, List, Dict
from bs4 import BeautifulSoup
import re


class NewVideoMonitor:
    """Monitor for new videos on Javmix.TV"""
    
    BASE_URL = "https://javmix.tv"
    
    def __init__(self, known_urls_file="sitemap_videos.json", new_urls_file="javmix/new_videos.json"):
        self.known_urls_file = known_urls_file
        self.new_urls_file = new_urls_file
        self.known_urls = self._load_known_urls()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _load_known_urls(self) -> Set[str]:
        """Load known URLs from sitemap file"""
        known = set()
        
        if os.path.exists(self.known_urls_file):
            try:
                with open(self.known_urls_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    urls = data.get('urls', [])
                    known = set(self._normalize_url(url) for url in urls)
                    print(f"✓ Loaded {len(known):,} known URLs from {self.known_urls_file}")
            except Exception as e:
                print(f"⚠️ Could not load known URLs: {e}")
        
        return known
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        if not url:
            return ""
        url = url.lower().strip()
        url = url.replace('http://', 'https://')
        url = url.replace('https://www.', 'https://')
        if '?' in url:
            url = url.split('?')[0]
        if '#' in url:
            url = url.split('#')[0]
        url = url.rstrip('/')
        return url
    
    def _is_new_url(self, url: str) -> bool:
        """Check if URL is new"""
        normalized = self._normalize_url(url)
        return normalized not in self.known_urls
    
    def _add_to_known(self, url: str):
        """Add URL to known set"""
        normalized = self._normalize_url(url)
        self.known_urls.add(normalized)
    
    def _save_new_videos(self, new_videos: List[Dict]):
        """Save new videos to file"""
        try:
            # Load existing new videos
            existing = []
            if os.path.exists(self.new_urls_file):
                with open(self.new_urls_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    existing = data.get('videos', [])
            
            # Add new ones
            existing.extend(new_videos)
            
            # Remove duplicates
            seen = set()
            unique = []
            for video in existing:
                url = video.get('url')
                if url and url not in seen:
                    seen.add(url)
                    unique.append(video)
            
            # Sort by discovered_at (newest first)
            unique.sort(key=lambda x: x.get('discovered_at', ''), reverse=True)
            
            # Save
            data = {
                'total_new': len(unique),
                'last_check': datetime.now().isoformat(),
                'videos': unique
            }
            
            with open(self.new_urls_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved {len(new_videos)} new videos to {self.new_urls_file}")
            
        except Exception as e:
            print(f"❌ Error saving new videos: {e}")
    
    def check_rss_feeds(self) -> List[Dict]:
        """Check RSS feeds for new videos"""
        print("\n📡 Checking RSS feeds...")
        
        rss_urls = [
            f"{self.BASE_URL}/feed/",
            f"{self.BASE_URL}/?feed=rss2",
            f"{self.BASE_URL}/?feed=rss",
        ]
        
        new_videos = []
        
        for rss_url in rss_urls:
            try:
                response = self.session.get(rss_url, timeout=10)
                
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    
                    # Parse RSS items
                    for item in root.findall('.//item'):
                        link_elem = item.find('link')
                        title_elem = item.find('title')
                        pubdate_elem = item.find('pubDate')
                        
                        if link_elem is not None and link_elem.text:
                            url = link_elem.text
                            
                            # Check if it's a video URL
                            if '/video/' in url or '/fc2ppv/' in url or '/xvideo/' in url:
                                if self._is_new_url(url):
                                    video = {
                                        'url': url,
                                        'title': title_elem.text if title_elem is not None else '',
                                        'published': pubdate_elem.text if pubdate_elem is not None else '',
                                        'discovered_at': datetime.now().isoformat(),
                                        'source': 'rss'
                                    }
                                    new_videos.append(video)
                                    self._add_to_known(url)
                                    
                                    # Extract code
                                    code_match = re.search(r'/(video|fc2ppv|xvideo)/([^/]+)', url)
                                    code = code_match.group(2).upper() if code_match else 'unknown'
                                    print(f"  🆕 NEW: {code}")
                    
                    if new_videos:
                        print(f"  ✅ Found {len(new_videos)} new videos in RSS")
                    
            except Exception as e:
                print(f"  ⚠️ Error checking {rss_url}: {str(e)[:50]}")
        
        return new_videos
    
    def check_homepage(self, num_pages=3) -> List[Dict]:
        """Check homepage for new videos"""
        print(f"\n🏠 Checking homepage ({num_pages} pages)...")
        
        new_videos = []
        
        for page in range(1, num_pages + 1):
            try:
                if page == 1:
                    url = self.BASE_URL
                else:
                    url = f"{self.BASE_URL}/page/{page}/"
                
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all video links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        
                        if '/video/' in href or '/fc2ppv/' in href or '/xvideo/' in href:
                            # Normalize URL
                            if href.startswith('http'):
                                full_url = href
                            elif href.startswith('/'):
                                full_url = f"{self.BASE_URL}{href}"
                            else:
                                full_url = f"{self.BASE_URL}/{href}"
                            
                            if self._is_new_url(full_url):
                                video = {
                                    'url': full_url,
                                    'title': link.get_text(strip=True),
                                    'discovered_at': datetime.now().isoformat(),
                                    'source': f'homepage_page_{page}'
                                }
                                new_videos.append(video)
                                self._add_to_known(full_url)
                                
                                # Extract code
                                code_match = re.search(r'/(video|fc2ppv|xvideo)/([^/]+)', full_url)
                                code = code_match.group(2).upper() if code_match else 'unknown'
                                print(f"  🆕 NEW: {code}")
                
                time.sleep(1)  # Be polite
                
            except Exception as e:
                print(f"  ⚠️ Error checking page {page}: {str(e)[:50]}")
        
        if new_videos:
            print(f"  ✅ Found {len(new_videos)} new videos on homepage")
        
        return new_videos
    
    def check_sitemap_updates(self) -> List[Dict]:
        """Check sitemap for new entries"""
        print("\n🗺️  Checking sitemap for updates...")
        
        new_videos = []
        
        try:
            # Check main sitemap index
            sitemap_url = f"{self.BASE_URL}/sitemap.xml"
            response = self.session.get(sitemap_url, timeout=30)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                
                # Get all sub-sitemaps
                sitemaps = root.findall('.//ns:sitemap/ns:loc', namespace)
                
                if sitemaps:
                    # Check only the FIRST sitemap (most recent)
                    # This is much faster than checking all 363 sitemaps
                    recent_sitemap = sitemaps[0].text
                    print(f"  📥 Checking most recent sitemap: {recent_sitemap.split('/')[-1]}")
                    
                    sub_response = self.session.get(recent_sitemap, timeout=30)
                    if sub_response.status_code == 200:
                        sub_root = ET.fromstring(sub_response.content)
                        urls = sub_root.findall('.//ns:url/ns:loc', namespace)
                        
                        for url_elem in urls:
                            url = url_elem.text
                            
                            if url and ('/video/' in url or '/fc2ppv/' in url or '/xvideo/' in url):
                                if self._is_new_url(url):
                                    video = {
                                        'url': url,
                                        'discovered_at': datetime.now().isoformat(),
                                        'source': 'sitemap_update'
                                    }
                                    new_videos.append(video)
                                    self._add_to_known(url)
                                    
                                    # Extract code
                                    code_match = re.search(r'/(video|fc2ppv|xvideo)/([^/]+)', url)
                                    code = code_match.group(2).upper() if code_match else 'unknown'
                                    print(f"  🆕 NEW: {code}")
                        
                        if new_videos:
                            print(f"  ✅ Found {len(new_videos)} new videos in sitemap")
                
        except Exception as e:
            print(f"  ⚠️ Error checking sitemap: {str(e)[:50]}")
        
        return new_videos
    
    def check_all_sources(self) -> List[Dict]:
        """Check all sources for new videos"""
        print("="*70)
        print("🔍 CHECKING FOR NEW VIDEOS")
        print("="*70)
        print(f"Known videos: {len(self.known_urls):,}")
        print(f"Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_new = []
        
        # 1. RSS feeds (fastest, most reliable for latest videos)
        rss_new = self.check_rss_feeds()
        all_new.extend(rss_new)
        
        # 2. Homepage (recent videos)
        homepage_new = self.check_homepage(num_pages=3)
        all_new.extend(homepage_new)
        
        # 3. Sitemap updates (optional, slower)
        # sitemap_new = self.check_sitemap_updates()
        # all_new.extend(sitemap_new)
        
        # Remove duplicates
        seen = set()
        unique_new = []
        for video in all_new:
            url = video.get('url')
            if url and url not in seen:
                seen.add(url)
                unique_new.append(video)
        
        print("\n" + "="*70)
        print(f"✅ FOUND {len(unique_new)} NEW VIDEOS")
        print("="*70)
        
        if unique_new:
            # Save to file
            self._save_new_videos(unique_new)
            
            # Update known URLs file
            self._update_known_urls_file()
            
            # Show summary
            print(f"\nBreakdown by source:")
            sources = {}
            for video in unique_new:
                source = video.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            for source, count in sources.items():
                print(f"  - {source}: {count}")
            
            print(f"\n💾 New videos saved to: {self.new_urls_file}")
            print(f"📋 Total known videos: {len(self.known_urls):,}")
        else:
            print("\n✓ No new videos found (all up to date)")
        
        return unique_new
    
    def _update_known_urls_file(self):
        """Update the known URLs file with new URLs"""
        try:
            # Load current data
            with open(self.known_urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update URLs list
            data['urls'] = sorted(list(self.known_urls))
            data['total'] = len(self.known_urls)
            data['last_updated'] = datetime.now().isoformat()
            
            # Save
            with open(self.known_urls_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Updated {self.known_urls_file} with {len(self.known_urls):,} URLs")
            
        except Exception as e:
            print(f"⚠️ Could not update known URLs file: {e}")
    
    def monitor_continuously(self, interval_minutes=30):
        """Monitor continuously at specified interval"""
        print("="*70)
        print("🔄 CONTINUOUS MONITORING MODE")
        print("="*70)
        print(f"Check interval: {interval_minutes} minutes")
        print(f"Press Ctrl+C to stop")
        print("="*70)
        
        check_count = 0
        total_new = 0
        
        try:
            while True:
                check_count += 1
                print(f"\n\n{'='*70}")
                print(f"CHECK #{check_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*70}")
                
                new_videos = self.check_all_sources()
                total_new += len(new_videos)
                
                print(f"\n📊 Session Summary:")
                print(f"   Total checks: {check_count}")
                print(f"   Total new videos found: {total_new}")
                print(f"   Average per check: {total_new/check_count:.1f}")
                
                # Wait for next check
                next_check = datetime.now().timestamp() + (interval_minutes * 60)
                next_check_time = datetime.fromtimestamp(next_check).strftime('%H:%M:%S')
                print(f"\n⏰ Next check at: {next_check_time} ({interval_minutes} minutes)")
                print(f"💤 Sleeping...")
                
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n" + "="*70)
            print("🛑 MONITORING STOPPED")
            print("="*70)
            print(f"Total checks: {check_count}")
            print(f"Total new videos found: {total_new}")
            print("="*70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor Javmix.TV for new videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single check
  python monitor_new_videos.py
  
  # Continuous monitoring (every 30 minutes)
  python monitor_new_videos.py --continuous --interval 30
  
  # Quick check (RSS only)
  python monitor_new_videos.py --rss-only
        """
    )
    
    parser.add_argument('--continuous', action='store_true', help='Monitor continuously')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in minutes (default: 30)')
    parser.add_argument('--rss-only', action='store_true', help='Check RSS feeds only (fastest)')
    parser.add_argument('--known-urls', default='sitemap_videos.json', help='Known URLs file')
    parser.add_argument('--output', default='javmix/new_videos.json', help='Output file for new videos')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = NewVideoMonitor(
        known_urls_file=args.known_urls,
        new_urls_file=args.output
    )
    
    if args.continuous:
        # Continuous monitoring
        monitor.monitor_continuously(interval_minutes=args.interval)
    elif args.rss_only:
        # Quick RSS check
        print("="*70)
        print("📡 RSS QUICK CHECK")
        print("="*70)
        new_videos = monitor.check_rss_feeds()
        if new_videos:
            monitor._save_new_videos(new_videos)
            print(f"\n✅ Found {len(new_videos)} new videos")
        else:
            print("\n✓ No new videos")
    else:
        # Single check all sources
        monitor.check_all_sources()


if __name__ == "__main__":
    main()
