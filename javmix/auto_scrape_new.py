#!/usr/bin/env python3
"""
Automated New Video Scraper
Monitors for new videos and automatically scrapes them
"""

import os
import sys
import json
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor_new_videos import NewVideoMonitor


def load_new_videos(new_videos_file="javmix/new_videos.json"):
    """Load new videos from file"""
    if not os.path.exists(new_videos_file):
        return []
    
    try:
        with open(new_videos_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('videos', [])
    except:
        return []


def mark_as_scraped(video_url, new_videos_file="javmix/new_videos.json"):
    """Mark video as scraped"""
    try:
        with open(new_videos_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add scraped flag
        for video in data.get('videos', []):
            if video.get('url') == video_url:
                video['scraped'] = True
                video['scraped_at'] = datetime.now().isoformat()
        
        with open(new_videos_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    except:
        return False


def scrape_video(video_url):
    """Scrape a single video using javmix_scraper.py"""
    import subprocess
    
    print(f"\n{'='*70}")
    print(f"🎬 SCRAPING: {video_url}")
    print(f"{'='*70}")
    
    try:
        # Run scraper
        result = subprocess.run(
            ['python', 'javmix/javmix_scraper.py', '--url', video_url],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully scraped: {video_url}")
            return True
        else:
            print(f"❌ Failed to scrape: {video_url}")
            print(f"Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout scraping: {video_url}")
        return False
    except Exception as e:
        print(f"❌ Error scraping: {e}")
        return False


def auto_scrape_new_videos(check_interval=60, max_videos_per_check=10):
    """
    Automatically monitor and scrape new videos
    
    Args:
        check_interval: Minutes between checks
        max_videos_per_check: Maximum videos to scrape per check
    """
    print("="*70)
    print("🤖 AUTOMATED NEW VIDEO SCRAPER")
    print("="*70)
    print(f"Check interval: {check_interval} minutes")
    print(f"Max videos per check: {max_videos_per_check}")
    print(f"Press Ctrl+C to stop")
    print("="*70)
    
    monitor = NewVideoMonitor()
    check_count = 0
    total_scraped = 0
    
    try:
        while True:
            check_count += 1
            print(f"\n\n{'='*70}")
            print(f"CHECK #{check_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}")
            
            # 1. Check for new videos
            print("\n🔍 Step 1: Checking for new videos...")
            new_videos = monitor.check_all_sources()
            
            if new_videos:
                print(f"\n✅ Found {len(new_videos)} new videos")
                
                # 2. Scrape new videos (limit to max_videos_per_check)
                videos_to_scrape = new_videos[:max_videos_per_check]
                
                if len(new_videos) > max_videos_per_check:
                    print(f"⚠️ Limiting to {max_videos_per_check} videos (will scrape rest next time)")
                
                print(f"\n🎬 Step 2: Scraping {len(videos_to_scrape)} videos...")
                
                scraped_count = 0
                failed_count = 0
                
                for i, video in enumerate(videos_to_scrape, 1):
                    url = video.get('url')
                    print(f"\n[{i}/{len(videos_to_scrape)}] {url}")
                    
                    if scrape_video(url):
                        mark_as_scraped(url)
                        scraped_count += 1
                        total_scraped += 1
                    else:
                        failed_count += 1
                    
                    # Delay between videos
                    if i < len(videos_to_scrape):
                        print(f"⏳ Waiting 10 seconds before next video...")
                        time.sleep(10)
                
                print(f"\n📊 Scraping Summary:")
                print(f"   Successful: {scraped_count}")
                print(f"   Failed: {failed_count}")
                
            else:
                print("\n✓ No new videos found")
            
            # Session summary
            print(f"\n📊 Session Summary:")
            print(f"   Total checks: {check_count}")
            print(f"   Total videos scraped: {total_scraped}")
            
            # Wait for next check
            next_check = datetime.now().timestamp() + (check_interval * 60)
            next_check_time = datetime.fromtimestamp(next_check).strftime('%H:%M:%S')
            print(f"\n⏰ Next check at: {next_check_time} ({check_interval} minutes)")
            print(f"💤 Sleeping...")
            
            time.sleep(check_interval * 60)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("🛑 AUTOMATED SCRAPER STOPPED")
        print("="*70)
        print(f"Total checks: {check_count}")
        print(f"Total videos scraped: {total_scraped}")
        print("="*70)


def scrape_pending_new_videos():
    """Scrape all pending new videos (one-time)"""
    print("="*70)
    print("🎬 SCRAPING PENDING NEW VIDEOS")
    print("="*70)
    
    new_videos = load_new_videos()
    
    if not new_videos:
        print("✓ No new videos to scrape")
        return
    
    # Filter unscraped videos
    pending = [v for v in new_videos if not v.get('scraped')]
    
    if not pending:
        print("✓ All new videos already scraped")
        return
    
    print(f"Found {len(pending)} pending videos to scrape")
    
    scraped_count = 0
    failed_count = 0
    
    for i, video in enumerate(pending, 1):
        url = video.get('url')
        print(f"\n[{i}/{len(pending)}] {url}")
        
        if scrape_video(url):
            mark_as_scraped(url)
            scraped_count += 1
        else:
            failed_count += 1
        
        # Delay between videos
        if i < len(pending):
            print(f"⏳ Waiting 10 seconds before next video...")
            time.sleep(10)
    
    print(f"\n{'='*70}")
    print(f"📊 SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Successful: {scraped_count}")
    print(f"Failed: {failed_count}")
    print(f"{'='*70}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Automated new video scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape pending new videos (one-time)
  python auto_scrape_new.py --scrape-pending
  
  # Automated monitoring + scraping (every hour)
  python auto_scrape_new.py --auto --interval 60
  
  # Automated with limit (max 5 videos per check)
  python auto_scrape_new.py --auto --interval 30 --max-videos 5
        """
    )
    
    parser.add_argument('--auto', action='store_true', help='Automated monitoring + scraping')
    parser.add_argument('--scrape-pending', action='store_true', help='Scrape pending new videos')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in minutes (default: 60)')
    parser.add_argument('--max-videos', type=int, default=10, help='Max videos per check (default: 10)')
    
    args = parser.parse_args()
    
    if args.auto:
        # Automated mode
        auto_scrape_new_videos(
            check_interval=args.interval,
            max_videos_per_check=args.max_videos
        )
    elif args.scrape_pending:
        # Scrape pending
        scrape_pending_new_videos()
    else:
        # Default: show help
        parser.print_help()


if __name__ == "__main__":
    main()
