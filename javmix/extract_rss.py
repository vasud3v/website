#!/usr/bin/env python3
"""
Extract video URLs from Javmix.TV RSS feeds
"""

import requests
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime

def find_rss_feeds(base_url="https://javmix.tv"):
    """Find RSS feed URLs"""
    
    print("🔍 Searching for RSS feeds...")
    
    # Common RSS feed locations
    rss_urls = [
        f"{base_url}/feed/",
        f"{base_url}/rss/",
        f"{base_url}/feed.xml",
        f"{base_url}/rss.xml",
        f"{base_url}/index.xml",
        f"{base_url}/atom.xml",
        f"{base_url}/wp-rss.php",
        f"{base_url}/?feed=rss",
        f"{base_url}/?feed=rss2",
        f"{base_url}/?feed=atom",
    ]
    
    found_feeds = []
    
    for rss_url in rss_urls:
        try:
            print(f"\n📥 Trying: {rss_url}")
            response = requests.get(rss_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                # Check if it's XML
                if 'xml' in response.headers.get('Content-Type', '').lower() or response.text.strip().startswith('<?xml'):
                    print(f"  ✅ Found RSS feed!")
                    found_feeds.append(rss_url)
                else:
                    print(f"  ⚠️ Not XML content")
            else:
                print(f"  ❌ Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error: {str(e)[:50]}")
    
    return found_feeds


def parse_rss_feed(rss_url):
    """Parse RSS feed and extract video URLs"""
    
    print(f"\n📖 Parsing RSS feed: {rss_url}")
    
    try:
        response = requests.get(rss_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code != 200:
            print(f"  ❌ Failed to fetch: {response.status_code}")
            return []
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        videos = []
        
        # Try RSS 2.0 format
        items = root.findall('.//item')
        if items:
            print(f"  📋 Found {len(items)} items (RSS 2.0)")
            
            for item in items:
                try:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    pub_date_elem = item.find('pubDate')
                    description_elem = item.find('description')
                    
                    if link_elem is not None and link_elem.text:
                        link = link_elem.text.strip()
                        
                        # Check if it's a video URL
                        if '/video/' in link or '/fc2ppv/' in link or '/xvideo/' in link:
                            video = {
                                'url': link,
                                'title': title_elem.text.strip() if title_elem is not None else '',
                                'pub_date': pub_date_elem.text.strip() if pub_date_elem is not None else '',
                                'description': description_elem.text.strip() if description_elem is not None else ''
                            }
                            videos.append(video)
                except Exception as e:
                    print(f"    ⚠️ Error parsing item: {str(e)[:50]}")
        
        # Try Atom format
        if not videos:
            # Atom namespace
            atom_ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('.//atom:entry', atom_ns)
            
            if entries:
                print(f"  📋 Found {len(entries)} entries (Atom)")
                
                for entry in entries:
                    try:
                        title_elem = entry.find('atom:title', atom_ns)
                        link_elem = entry.find('atom:link[@rel="alternate"]', atom_ns)
                        if link_elem is None:
                            link_elem = entry.find('atom:link', atom_ns)
                        updated_elem = entry.find('atom:updated', atom_ns)
                        summary_elem = entry.find('atom:summary', atom_ns)
                        
                        if link_elem is not None:
                            link = link_elem.get('href', '')
                            
                            if '/video/' in link or '/fc2ppv/' in link or '/xvideo/' in link:
                                video = {
                                    'url': link,
                                    'title': title_elem.text.strip() if title_elem is not None else '',
                                    'pub_date': updated_elem.text.strip() if updated_elem is not None else '',
                                    'description': summary_elem.text.strip() if summary_elem is not None else ''
                                }
                                videos.append(video)
                    except Exception as e:
                        print(f"    ⚠️ Error parsing entry: {str(e)[:50]}")
        
        print(f"  ✅ Extracted {len(videos)} video URLs")
        return videos
        
    except ET.ParseError as e:
        print(f"  ❌ XML parse error: {str(e)[:50]}")
        return []
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        return []


def check_html_for_rss_links(base_url="https://javmix.tv"):
    """Check HTML page for RSS feed links"""
    
    print(f"\n🔍 Checking HTML for RSS links...")
    
    try:
        response = requests.get(base_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            html = response.text
            
            # Look for RSS links in HTML
            rss_patterns = [
                r'<link[^>]*type=["\']application/rss\+xml["\'][^>]*href=["\']([^"\']+)["\']',
                r'<link[^>]*href=["\']([^"\']+)["\'][^>]*type=["\']application/rss\+xml["\']',
                r'<link[^>]*type=["\']application/atom\+xml["\'][^>]*href=["\']([^"\']+)["\']',
                r'<a[^>]*href=["\']([^"\']*feed[^"\']*)["\']',
                r'<a[^>]*href=["\']([^"\']*rss[^"\']*)["\']',
            ]
            
            found_feeds = []
            for pattern in rss_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    # Make absolute URL
                    if match.startswith('http'):
                        feed_url = match
                    elif match.startswith('/'):
                        feed_url = f"{base_url}{match}"
                    else:
                        feed_url = f"{base_url}/{match}"
                    
                    if feed_url not in found_feeds:
                        found_feeds.append(feed_url)
                        print(f"  📍 Found: {feed_url}")
            
            return found_feeds
        else:
            print(f"  ❌ Failed to fetch homepage: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        return []


def main():
    print("="*60)
    print("📡 JAVMIX.TV RSS FEED EXTRACTOR")
    print("="*60)
    
    base_url = "https://javmix.tv"
    
    # Method 1: Check HTML for RSS links
    html_feeds = check_html_for_rss_links(base_url)
    
    # Method 2: Try common RSS URLs
    common_feeds = find_rss_feeds(base_url)
    
    # Combine and deduplicate
    all_feeds = list(set(html_feeds + common_feeds))
    
    if not all_feeds:
        print(f"\n{'='*60}")
        print(f"❌ NO RSS FEEDS FOUND")
        print(f"{'='*60}")
        print("RSS feeds may not be available or accessible")
        return
    
    print(f"\n{'='*60}")
    print(f"✅ Found {len(all_feeds)} RSS feed(s)")
    print(f"{'='*60}")
    
    # Parse each feed
    all_videos = []
    for feed_url in all_feeds:
        videos = parse_rss_feed(feed_url)
        all_videos.extend(videos)
    
    # Remove duplicates by URL
    unique_videos = {}
    for video in all_videos:
        if video['url'] not in unique_videos:
            unique_videos[video['url']] = video
    
    all_videos = list(unique_videos.values())
    
    if all_videos:
        print(f"\n{'='*60}")
        print(f"✅ TOTAL: {len(all_videos)} unique videos")
        print(f"{'='*60}")
        
        # Categorize
        regular = [v for v in all_videos if '/video/' in v['url']]
        fc2ppv = [v for v in all_videos if '/fc2ppv/' in v['url']]
        xvideo = [v for v in all_videos if '/xvideo/' in v['url']]
        
        print(f"\nBreakdown:")
        print(f"  - Regular (/video/): {len(regular)}")
        print(f"  - FC2PPV (/fc2ppv/): {len(fc2ppv)}")
        print(f"  - XVideo (/xvideo/): {len(xvideo)}")
        
        # Save to file
        output_file = "rss_videos.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total': len(all_videos),
                'regular': len(regular),
                'fc2ppv': len(fc2ppv),
                'xvideo': len(xvideo),
                'feeds': all_feeds,
                'videos': all_videos
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved to: {output_file}")
        
        # Show samples
        print(f"\n📋 Latest videos (first 10):")
        for i, video in enumerate(all_videos[:10], 1):
            print(f"\n  {i}. {video['title'][:60]}...")
            print(f"     URL: {video['url']}")
            print(f"     Date: {video['pub_date']}")
        
        # Save URLs for testing
        test_file = "rss_test_urls.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            for video in all_videos[:20]:  # First 20 for testing
                f.write(video['url'] + '\n')
        
        print(f"\n💾 Test URLs saved to: {test_file}")
        
    else:
        print(f"\n{'='*60}")
        print(f"⚠️ No video URLs found in RSS feeds")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
