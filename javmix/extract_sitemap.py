#!/usr/bin/env python3
"""
Extract video URLs from Javmix.TV sitemap - OPTIMIZED VERSION
Fast concurrent loading with streaming and early termination
"""

import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def fetch_sitemap_fast(url, timeout=30, max_size_mb=20):
    """Fetch sitemap with optimized settings for slow servers"""
    try:
        # Use streaming to avoid loading entire file into memory
        # Increased timeout for slow servers
        response = requests.get(
            url, 
            timeout=timeout,
            stream=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        )
        
        if response.status_code == 200:
            # Read content in chunks with progress
            content = b''
            max_size = max_size_mb * 1024 * 1024
            chunk_count = 0
            
            for chunk in response.iter_content(chunk_size=16384):  # Larger chunks
                if chunk:
                    content += chunk
                    chunk_count += 1
                    
                    # Show progress every 100 chunks (~1.6MB)
                    if chunk_count % 100 == 0:
                        size_mb = len(content) / (1024 * 1024)
                        print(f"      📥 Downloaded: {size_mb:.1f}MB...", end='\r')
                    
                    # Early termination if too large
                    if len(content) > max_size:
                        print(f"      ⚠️ Size limit reached ({max_size_mb}MB), stopping...")
                        break
            
            if content:
                size_mb = len(content) / (1024 * 1024)
                print(f"      ✅ Downloaded: {size_mb:.1f}MB" + " " * 20)
            
            return content
        return None
    except requests.exceptions.Timeout:
        print(f"      ⏱️ Timeout after {timeout}s")
        return None
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:50]}")
        return None

def extract_sitemap_urls(base_url="https://javmix.tv", max_urls=None, max_workers=32, timeout=30):
    """Extract video URLs from sitemap with parallel processing"""
    
    print("🔍 Searching for sitemap (parallel processing)...")
    print(f"⚙️  Settings: timeout={timeout}s, workers={max_workers}, max_urls={max_urls or 'ALL (complete extraction)'}")
    
    # Common sitemap locations (prioritized by likelihood)
    sitemap_urls = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/post-sitemap.xml",
        f"{base_url}/sitemap_index.xml",
        f"{base_url}/wp-sitemap.xml",
        f"{base_url}/video-sitemap.xml",
        f"{base_url}/sitemap-videos.xml",
    ]
    
    all_video_urls = []
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    # Try sitemaps sequentially to find the index
    print(f"\n📥 Checking sitemap locations...")
    
    for url in sitemap_urls:
        print(f"\n  🔍 Trying: {url}")
        content = fetch_sitemap_fast(url, timeout=timeout)
        
        if content:
            try:
                print(f"      📊 Parsing XML...")
                root = ET.fromstring(content)
                
                # Check if it's a sitemap index
                sitemaps = root.findall('.//ns:sitemap/ns:loc', namespace)
                
                if sitemaps:
                    print(f"      📋 Sitemap index with {len(sitemaps)} sub-sitemaps")
                    
                    # Get all sub-sitemap URLs
                    sub_sitemap_urls = [s.text for s in sitemaps]
                    
                    if max_urls:
                        # Estimate: ~1000 URLs per sitemap, so limit accordingly
                        estimated_per_sitemap = 1000
                        max_sitemaps = max(1, (max_urls // estimated_per_sitemap) + 1)
                        if len(sub_sitemap_urls) > max_sitemaps:
                            print(f"      ⚡ Limiting to first {max_sitemaps} sitemaps (to reach ~{max_urls} URLs)")
                            sub_sitemap_urls = sub_sitemap_urls[:max_sitemaps]
                    else:
                        print(f"      🌐 Processing ALL {len(sub_sitemap_urls)} sitemaps (complete extraction)")
                        print(f"      ⚡ Using {max_workers} parallel workers")
                        print(f"      ⏱️  Estimated time: {len(sub_sitemap_urls) * 40 / max_workers / 60:.0f}-{len(sub_sitemap_urls) * 50 / max_workers / 60:.0f} minutes")
                    
                    # Process sub-sitemaps in parallel
                    start_time = time.time()
                    processed = 0
                    
                    print(f"\n🚀 Starting parallel extraction with {max_workers} workers...")
                    
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # Submit all tasks
                        future_to_url = {
                            executor.submit(fetch_and_parse_sitemap, sub_url, timeout, namespace): sub_url 
                            for sub_url in sub_sitemap_urls
                        }
                        
                        # Process results as they complete
                        for future in as_completed(future_to_url):
                            sub_url = future_to_url[future]
                            processed += 1
                            
                            try:
                                video_urls = future.result()
                                
                                if video_urls:
                                    all_video_urls.extend(video_urls)
                                    
                                # Progress update
                                elapsed = time.time() - start_time
                                rate = len(all_video_urls) / elapsed if elapsed > 0 else 0
                                remaining = (len(sub_sitemap_urls) - processed) * (elapsed / processed) if processed > 0 else 0
                                
                                print(f"    [{processed}/{len(sub_sitemap_urls)}] {sub_url.split('/')[-1]}: {len(video_urls) if video_urls else 0} URLs | Total: {len(all_video_urls):,} | ETA: {remaining/60:.1f}min | {rate:.1f} URLs/sec")
                                
                                # Early termination if we have a limit AND reached it
                                if max_urls and len(all_video_urls) >= max_urls:
                                    print(f"\n      🎯 Reached target of {max_urls:,} URLs, stopping...")
                                    # Cancel remaining futures
                                    for f in future_to_url:
                                        f.cancel()
                                    break
                                    
                            except Exception as e:
                                print(f"    [{processed}/{len(sub_sitemap_urls)}] {sub_url.split('/')[-1]}: ❌ Error - {str(e)[:50]}")
                            
                            # Progress summary every 50 sitemaps
                            if processed % 50 == 0:
                                elapsed_min = elapsed / 60
                                print(f"\n      📊 Progress: {processed}/{len(sub_sitemap_urls)} sitemaps | {len(all_video_urls):,} URLs | {elapsed_min:.1f}min | {rate:.1f} URLs/sec\n")
                    
                    # After processing all sub-sitemaps (or reaching limit), stop checking other sitemap locations
                    if all_video_urls:
                        print(f"\n  ✅ Processed sitemap index")
                        break
                else:
                    # Regular sitemap
                    print(f"      📊 Parsing URLs...")
                    urls = root.findall('.//ns:url/ns:loc', namespace)
                    video_urls = [u.text for u in urls 
                                if '/video/' in u.text or '/fc2ppv/' in u.text or '/xvideo/' in u.text]
                    
                    if video_urls:
                        all_video_urls.extend(video_urls)
                        print(f"      ✅ Found {len(video_urls)} video URLs")
                    
                    # After processing regular sitemap, stop checking other sitemap locations
                    if all_video_urls:
                        print(f"\n  ✅ Processed regular sitemap")
                        break
                    
            except ET.ParseError as e:
                print(f"      ❌ XML parse error: {str(e)[:50]}")
    
    # Remove duplicates
    print(f"\n  🔄 Removing duplicates...")
    unique_urls = list(set(all_video_urls))
    duplicates = len(all_video_urls) - len(unique_urls)
    if duplicates > 0:
        print(f"  ✅ Removed {duplicates:,} duplicates")
    
    return unique_urls


def fetch_and_parse_sitemap(url, timeout, namespace):
    """Fetch and parse a single sitemap (for parallel processing)"""
    try:
        content = fetch_sitemap_fast(url, timeout=timeout, max_size_mb=50)
        if content:
            root = ET.fromstring(content)
            urls = root.findall('.//ns:url/ns:loc', namespace)
            
            # Filter video URLs
            video_urls = [u.text for u in urls 
                        if '/video/' in u.text or '/fc2ppv/' in u.text or '/xvideo/' in u.text]
            
            return video_urls
        return []
    except Exception as e:
        return []


def extract_from_robots_txt(base_url="https://javmix.tv"):
    """Extract sitemap URLs from robots.txt - FAST"""
    
    print("\n🤖 Checking robots.txt...")
    
    try:
        robots_url = f"{base_url}/robots.txt"
        response = requests.get(robots_url, timeout=3)  # Reduced timeout
        
        if response.status_code == 200:
            print("  ✅ Found robots.txt")
            
            # Find sitemap URLs
            sitemap_urls = []
            for line in response.text.split('\n'):
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    sitemap_urls.append(sitemap_url)
                    print(f"    📍 Sitemap: {sitemap_url}")
            
            return sitemap_urls
        else:
            print("  ❌ robots.txt not found")
            return []
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:30]}")
        return []


def get_random_videos(video_urls, count=10):
    """Get random video URLs"""
    import random
    
    if len(video_urls) <= count:
        return video_urls
    
    return random.sample(video_urls, count)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Javmix.TV Sitemap Extractor - Parallel Processing')
    parser.add_argument('--limit', type=int, help='Limit number of URLs to extract (optional)')
    parser.add_argument('--timeout', type=int, default=60, help='Request timeout in seconds (default: 60)')
    parser.add_argument('--workers', type=int, default=32, help='Number of parallel workers (default: 32)')
    parser.add_argument('--sample', type=int, default=20, help='Number of random samples to show (default: 20)')
    
    args = parser.parse_args()
    
    print("="*70)
    print("🗺️  JAVMIX.TV SITEMAP EXTRACTOR - PARALLEL PROCESSING")
    print("="*70)
    print(f"⚙️  Configuration:")
    print(f"   - Timeout: {args.timeout}s per request")
    print(f"   - Workers: {args.workers} parallel threads")
    print(f"   - URL limit: {args.limit or 'ALL (complete extraction)'}")
    print(f"   - Progress tracking: enabled")
    print("="*70)
    
    start_time = time.time()
    
    # Check robots.txt first (fast)
    sitemap_urls = extract_from_robots_txt()
    
    # Extract video URLs with parallel processing
    video_urls = extract_sitemap_urls(
        max_urls=args.limit,
        max_workers=args.workers,
        timeout=args.timeout
    )
    
    elapsed = time.time() - start_time
    
    if video_urls:
        print(f"\n{'='*70}")
        print(f"✅ SUCCESS")
        print(f"{'='*70}")
        print(f"Total video URLs found: {len(video_urls):,}")
        print(f"⏱️  Time taken: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        
        if len(video_urls) > 0:
            print(f"⚡ Speed: {len(video_urls)/elapsed:.1f} URLs/sec")
        
        # Categorize by type
        regular_videos = [url for url in video_urls if '/video/' in url]
        fc2ppv_videos = [url for url in video_urls if '/fc2ppv/' in url]
        xvideo_videos = [url for url in video_urls if '/xvideo/' in url]
        
        print(f"\nBreakdown:")
        print(f"  - Regular videos (/video/): {len(regular_videos):,}")
        print(f"  - FC2PPV videos (/fc2ppv/): {len(fc2ppv_videos):,}")
        print(f"  - XVideo videos (/xvideo/): {len(xvideo_videos):,}")
        
        # Save to file
        output_file = "sitemap_videos.json"
        print(f"\n💾 Saving to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total': len(video_urls),
                'regular': len(regular_videos),
                'fc2ppv': len(fc2ppv_videos),
                'xvideo': len(xvideo_videos),
                'extraction_time': f"{elapsed:.1f}s",
                'extraction_time_minutes': f"{elapsed/60:.1f}min",
                'workers': args.workers,
                'urls': video_urls
            }, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Saved!")
        
        # Show random samples
        print(f"\n📋 Random samples ({args.sample}):")
        random_urls = get_random_videos(video_urls, args.sample)
        for i, url in enumerate(random_urls, 1):
            # Extract code
            code_match = re.search(r'/(video|fc2ppv|xvideo)/([^/]+)', url)
            if code_match:
                code = code_match.group(2).upper()
                print(f"  {i:2d}. {code}")
            else:
                print(f"  {i:2d}. {url}")
        
        # Save random samples for testing
        test_file = "sitemap_test_urls.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            for url in random_urls:
                f.write(url + '\n')
        
        print(f"\n💾 Random test URLs saved to: {test_file}")
        
        # Performance summary
        print(f"\n📊 Performance Summary:")
        print(f"   ✅ Extracted {len(video_urls):,} URLs in {elapsed/60:.1f} minutes")
        print(f"   ⚡ Speed: {len(video_urls)/elapsed:.1f} URLs/sec")
        print(f"   🚀 Workers: {args.workers} parallel threads")
        
        if not args.limit:
            print(f"\n🎉 Complete extraction finished!")
            print(f"   Total archive: {len(video_urls):,} videos")
        
    else:
        print(f"\n{'='*70}")
        print(f"❌ NO VIDEO URLS FOUND")
        print(f"{'='*70}")
        print(f"⏱️  Time taken: {elapsed:.1f}s")
        print("Sitemap may not be available or accessible")
        print("\n💡 Alternative (faster):")
        print("   python collect_video_urls.py --homepage 5")


if __name__ == "__main__":
    main()
