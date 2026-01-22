"""
GitHub Actions Runner
Optimized for 6-hour time limit and limited disk space
"""
import os
import sys
import json
import time
import shutil
import traceback
from datetime import datetime

# Load .env file if running locally
if os.path.exists('.env') and not os.getenv('GITHUB_ACTIONS'):
    from load_env import load_env
    load_env()

from jable_scraper import JableScraper
from download_with_decrypt_v2 import HLSDownloaderV2 as HLSDownloader
from upload_all_hosts import upload_all
from auto_download import convert_to_mp4
from utils import (
    sanitize_filename, validate_url, load_json_safe, 
    save_json_safe, check_disk_space, verify_video_file,
    cleanup_temp_files, rate_limit
)

# Configuration
MAX_WORKERS = 32
TEMP_DIR = "temp_downloads"
DB_DIR = "database"
DB_FILE = f"{DB_DIR}/videos.json"
COMPLETE_FILE = "videos_complete.json"

# Get max videos from environment (unlimited by default)
# Note: GitHub Actions has 6-hour timeout, so unlimited may not finish all videos
MAX_VIDEOS_PER_RUN = int(os.getenv('MAX_VIDEOS', '999999'))  # Effectively unlimited

# Time limit (5 hours 15 minutes - 45min gap before workflow timeout)
TIME_LIMIT_SECONDS = 5.25 * 3600

def log(msg, end='\n'):
    """Simple logging"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}", end=end, flush=True)

def check_disk_space_wrapper():
    """Check available disk space"""
    has_space, free_gb, required_gb = check_disk_space(min_free_gb=3)
    log(f"💾 Free disk space: {free_gb:.2f} GB")
    return has_space

def emergency_cleanup():
    """Emergency cleanup if disk space is low"""
    log("🚨 Emergency cleanup - removing all temp files...")
    try:
        if os.path.exists(TEMP_DIR):
            for item in os.listdir(TEMP_DIR):
                item_path = os.path.join(TEMP_DIR, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except:
                    pass
        log("✅ Emergency cleanup complete")
        check_disk_space()
    except Exception as e:
        log(f"❌ Emergency cleanup failed: {e}")

# Use cleanup_temp_files from utils module

def save_to_database(video_data, upload_results):
    """Save to JSON database with safe locking"""
    try:
        # Load existing with safe method
        all_videos = load_json_safe(COMPLETE_FILE, [])
        
        # Create entry
        video_entry = {
            'code': video_data.code,
            'title': video_data.title,
            'thumbnail_url': video_data.thumbnail_url,
            'duration': video_data.duration,
            'views': video_data.views,
            'likes': video_data.likes,
            'release_date': video_data.release_date,
            'upload_time': video_data.upload_time,
            'hd_quality': video_data.hd_quality,
            'categories': video_data.categories,
            'models': video_data.models,
            'tags': video_data.tags,
            'preview_images': video_data.preview_images,
            'source_url': video_data.source_url,
            'scraped_at': video_data.scraped_at,
            'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'hosting': {}
        }
        
        # Add hosting links
        for result in upload_results['successful']:
            service = result['service'].lower()
            video_entry['hosting'][service] = {
                'filecode': result.get('filecode'),
                'embed_url': result.get('embed_url'),
                'watch_url': result.get('watch_url'),
            }
        
        # Update or add
        existing_index = None
        for i, v in enumerate(all_videos):
            if v.get('code') == video_data.code:
                existing_index = i
                break
        
        if existing_index is not None:
            all_videos[existing_index] = video_entry
        else:
            all_videos.append(video_entry)
        
        # Save with safe method (atomic write + locking)
        return save_json_safe(COMPLETE_FILE, all_videos, use_lock=True)
    except Exception as e:
        log(f"❌ Database save error: {e}")
        return False

def discover_videos(scraper):
    """Quick discovery - just new releases"""
    log("="*60)
    log("DISCOVERING NEW VIDEOS")
    log("="*60)
    
    discovered = set()
    
    # Load existing
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                videos = json.load(f)
                for v in videos:
                    if 'source_url' in v:
                        discovered.add(v['source_url'])
        except:
            pass
    
    initial = len(discovered)
    log(f"Existing videos: {initial}")
    
    # Discover from new releases (first 10 pages only for speed)
    log("\nScanning new releases...")
    pages_scanned = 0
    for page in range(1, 11):
        try:
            if page == 1:
                url = "https://jable.tv/new/"
            else:
                url = f"https://jable.tv/new/{page}/"
            
            # Use print instead of log with end parameter to avoid issues
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}]   Page {page}... ", end='', flush=True)
            
            try:
                links = scraper.get_video_links_from_page(url)
            except Exception as e:
                print(f"error: {e}")
                log(f"   Error details: {str(e)[:200]}")
                import traceback
                traceback.print_exc()
                break
            
            if not links:
                print("no videos")
                break
            
            before = len(discovered)
            discovered.update(links)
            after = len(discovered)
            print(f"{len(links)} videos ({after - before} new)")
            
            pages_scanned += 1
            time.sleep(2)
        except Exception as e:
            log(f"   Page {page} error: {e}")
            import traceback
            traceback.print_exc()
            break
    
    if pages_scanned == 0:
        log("⚠️ Failed to scan any pages!")
        return 0
    
    # Save
    videos = [{'source_url': url, 'discovered_at': time.strftime('%Y-%m-%d %H:%M:%S')} 
              for url in discovered]
    
    os.makedirs(DB_DIR, exist_ok=True)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)
    
    new_count = len(discovered) - initial
    log(f"\n✅ Discovery complete: {new_count} new, {len(discovered)} total")
    return len(discovered)

def process_video(scraper, video_url, index, total):
    """Process one video"""
    log(f"\n{'='*60}")
    log(f"VIDEO {index}/{total}")
    log(f"{'='*60}")
    log(f"URL: {video_url}")
    
    try:
        # Validate URL
        if not validate_url(video_url):
            log(f"❌ Invalid URL: {video_url}")
            return False
        
        # Check disk space
        if not check_disk_space_wrapper():
            log("❌ Low disk space!")
            emergency_cleanup()
            if not check_disk_space_wrapper():
                log("❌ Still low disk space after cleanup")
                return False
        
        # Scrape
        log("\n📋 Scraping metadata...")
        video_data = scraper.scrape_video(video_url)
        if not video_data:
            log("❌ Scraping failed")
            return False
        
        log(f"✅ {video_data.code} - {video_data.title[:50]}...")
        
        # Download
        log("\n📥 Downloading...")
        safe_code = sanitize_filename(video_data.code)
        output_ts = f"{TEMP_DIR}/{safe_code}.ts"
        output_mp4 = f"{TEMP_DIR}/{safe_code}.mp4"
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        downloader = HLSDownloader(MAX_WORKERS)
        if not downloader.download(video_data.m3u8_url, output_ts, safe_code):
            log("❌ Download failed")
            cleanup_temp_files(safe_code, TEMP_DIR)
            return False
        
        # Verify downloaded file
        if not verify_video_file(output_ts, min_size_mb=10):
            log("❌ Downloaded file is invalid or too small")
            cleanup_temp_files(safe_code, TEMP_DIR)
            return False
        
        size_gb = os.path.getsize(output_ts) / (1024**3)
        log(f"✅ Downloaded: {size_gb:.2f} GB")
        
        # Check segment folder
        segment_folder = f"{output_ts}_segments"
        if os.path.exists(segment_folder):
            segment_count = len(os.listdir(segment_folder))
            log(f"   📁 Segment folder: {segment_count} files")
        
        # Check disk space after download
        check_disk_space_wrapper()
        
        # Convert
        log("\n🔄 Converting to MP4...")
        if not convert_to_mp4(output_ts, output_mp4):
            log("❌ Conversion failed")
            cleanup_temp_files(safe_code, TEMP_DIR)
            return False
        
        # Verify converted file
        if not verify_video_file(output_mp4, min_size_mb=10):
            log("❌ Converted file is invalid or too small")
            cleanup_temp_files(safe_code, TEMP_DIR)
            return False
        
        log(f"✅ Converted")
        
        # Upload
        log("\n📤 Uploading to all hosts...")
        upload_results = upload_all(output_mp4, video_data.code, video_data.title)
        
        if not upload_results or not upload_results.get('successful'):
            log("❌ Upload failed")
            cleanup_temp_files(safe_code, TEMP_DIR)
            return False
        
        log(f"✅ Uploaded to {len(upload_results['successful'])} host(s)")
        
        # Save
        log("\n💾 Saving to database...")
        save_to_database(video_data, upload_results)
        
        # Cleanup
        log("\n🗑️ Cleaning up...")
        cleanup_temp_files(safe_code, TEMP_DIR)
        
        log(f"\n✅ VIDEO {index}/{total} COMPLETE!")
        return True
        
    except Exception as e:
        log(f"❌ Error: {e}")
        traceback.print_exc()
        return False

def main():
    log("""
╔══════════════════════════════════════════════════════════╗
║        GITHUB ACTIONS PIPELINE - 6 HOUR CONTINUOUS RUN  ║
╚══════════════════════════════════════════════════════════╝
""")
    
    log(f"Max videos per run: {MAX_VIDEOS_PER_RUN}")
    log(f"Time limit: {TIME_LIMIT_SECONDS/3600:.1f} hours")
    log(f"Mode: CONTINUOUS - Will process videos until time limit")
    
    # Verify environment variables
    log("\n🔍 Checking environment variables...")
    required_vars = ['STREAMTAPE_LOGIN', 'STREAMTAPE_API_KEY', 'LULUSTREAM_API_KEY', 'STREAMWISH_API_KEY']
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            log(f"   ✅ {var} is set")
        else:
            log(f"   ❌ {var} is NOT set")
            missing.append(var)
    
    if missing:
        log(f"\n⚠️ WARNING: {len(missing)} API keys are missing!")
        log(f"   The scraper will run but uploads may fail.")
        log(f"   Add these secrets in GitHub repository settings.")
    else:
        log(f"\n✅ All API keys are configured!")
    
    start_time = time.time()
    total_successful = 0
    total_failed = 0
    
    # Initial Discovery
    log("\n" + "="*60)
    log("INITIAL DISCOVERY")
    log("="*60)
    scraper = JableScraper(headless=True)
    try:
        discover_videos(scraper)
    except Exception as e:
        log(f"Discovery error: {e}")
    finally:
        scraper.close()
    
    time.sleep(5)
    
    # CONTINUOUS PROCESSING LOOP
    log("\n" + "="*60)
    log("STARTING CONTINUOUS PROCESSING")
    log("="*60)
    log("Will process videos until 6-hour time limit...")
    
    cycle = 0
    while True:
        cycle += 1
        elapsed = time.time() - start_time
        remaining = TIME_LIMIT_SECONDS - elapsed
        
        # Check if we're out of time
        if elapsed > TIME_LIMIT_SECONDS:
            log(f"\n⏰ Time limit reached! Stopping.")
            break
        
        log(f"\n{'#'*60}")
        log(f"CYCLE {cycle} - Time remaining: {remaining/3600:.1f}h ({remaining/60:.0f} min)")
        log(f"{'#'*60}")
        
        # Load videos
        if not os.path.exists(DB_FILE):
            log("❌ No videos database found")
            break
        
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        # Get processed codes
        processed = set()
        if os.path.exists(COMPLETE_FILE):
            with open(COMPLETE_FILE, 'r', encoding='utf-8') as f:
                completed = json.load(f)
                for v in completed:
                    if 'code' in v and 'hosting' in v and v['hosting']:
                        processed.add(v.get('code'))
                    # Also track by source URL to avoid reprocessing
                    if 'source_url' in v:
                        processed.add(v.get('source_url'))
        
        # Filter unprocessed (check by source_url since code isn't available yet)
        # IMPORTANT: Deduplicate to avoid processing same URL multiple times
        seen_urls = set()
        to_process = []
        for v in videos:
            url = v.get('source_url')
            if url and url not in processed and url not in seen_urls:
                to_process.append(v)
                seen_urls.add(url)
        
        log(f"   Filtered: {len(videos)} total → {len(to_process)} unique unprocessed")
        
        if not to_process:
            log("✅ All discovered videos processed!")
            
            # Check if we have time for more discovery
            elapsed = time.time() - start_time
            if elapsed > TIME_LIMIT_SECONDS:
                log("⏰ Time limit reached, stopping.")
                break
            
            log("   Discovering more videos...")
            
            # Discover more videos
            scraper = JableScraper(headless=True)
            try:
                new_count = discover_videos(scraper)
                if new_count == 0:
                    log("⚠️ No new videos discovered. Stopping to avoid infinite loop.")
                    break
            except Exception as e:
                log(f"Discovery error: {e}")
                log("⚠️ Discovery failed. Stopping to avoid infinite loop.")
                break
            finally:
                scraper.close()
            
            time.sleep(5)
            continue
        
        log(f"\n📹 Found {len(to_process)} unprocessed video(s)")
        log(f"   Total processed so far: {total_successful} successful, {total_failed} failed")
        
        # Process videos
        scraper = JableScraper(headless=True)
        successful = 0
        failed = 0
        
        try:
            for i, video in enumerate(to_process, 1):
                # Check time limit before starting each video
                elapsed = time.time() - start_time
                remaining = TIME_LIMIT_SECONDS - elapsed
                
                if elapsed > TIME_LIMIT_SECONDS:
                    log(f"\n⏰ Time limit reached ({elapsed/3600:.1f}h)")
                    break
                
                log(f"\n⏱️ Time remaining: {remaining/3600:.1f}h ({remaining/60:.0f} minutes)")
                
                video_url = video.get('source_url')
                if not video_url:
                    log(f"   ⚠️ Video {i} has no source_url, skipping")
                    continue
                
                try:
                    if process_video(scraper, video_url, i, len(to_process)):
                        successful += 1
                        total_successful += 1
                    else:
                        failed += 1
                        total_failed += 1
                except Exception as e:
                    log(f"   ❌ Error processing video {i}: {e}")
                    failed += 1
                    total_failed += 1
                
                # Small delay between videos
                time.sleep(5)
        
        finally:
            scraper.close()
        
        log(f"\n{'='*60}")
        log(f"CYCLE {cycle} COMPLETE")
        log(f"{'='*60}")
        log(f"✅ Success this cycle: {successful}")
        log(f"❌ Failed this cycle: {failed}")
        log(f"📊 Total: {total_successful} successful, {total_failed} failed")
        
        # Check if we should continue
        elapsed = time.time() - start_time
        if elapsed > TIME_LIMIT_SECONDS:
            log(f"\n⏰ Time limit reached! Stopping.")
            break
        
        # Small delay before next cycle
        time.sleep(10)
    
    # Summary
    log(f"\n{'='*60}")
    
    # Final Summary
    log(f"\n{'='*60}")
    log(f"PIPELINE COMPLETE - 6 HOUR RUN FINISHED")
    log(f"{'='*60}")
    log(f"✅ Total Success: {total_successful}")
    log(f"❌ Total Failed: {total_failed}")
    log(f"⏱️ Total Time: {(time.time() - start_time)/3600:.2f} hours")
    if total_successful > 0:
        log(f"📊 Average: {(time.time() - start_time)/total_successful/60:.1f} min/video")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
