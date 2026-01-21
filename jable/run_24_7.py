"""
BULLETPROOF 24/7 AUTOMATIC PIPELINE
Handles all edge cases, errors, and can run indefinitely

Features:
- Automatic retry on failures
- Browser crash recovery
- Network error handling
- Disk space monitoring
- Memory leak prevention
- Continuous discovery of new videos
- Resume from where it left off
- Detailed logging
"""
import os
import sys
import json
import time
import shutil
import traceback
from datetime import datetime
from pathlib import Path

# Load .env file if exists
if os.path.exists('.env'):
    from load_env import load_env
    load_env()

# Import our modules
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
STATS_FILE = f"{DB_DIR}/discovery_stats.json"
LOG_FILE = "pipeline_24_7.log"
ERROR_LOG = "pipeline_errors.log"

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds
DISCOVERY_INTERVAL = 3600  # Re-discover every 1 hour (3600 seconds)

# Disk space check (minimum 5GB free)
MIN_FREE_SPACE_GB = 5

class Logger:
    """Simple logger that writes to both console and file"""
    def __init__(self, log_file):
        self.log_file = log_file
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] [{level}] {message}"
        print(log_msg)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_msg + '\n')
        except:
            pass
    
    def info(self, msg):
        self.log(msg, "INFO")
    
    def error(self, msg):
        self.log(msg, "ERROR")
        try:
            with open(ERROR_LOG, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] {msg}\n")
        except:
            pass
    
    def warning(self, msg):
        self.log(msg, "WARN")

logger = Logger(LOG_FILE)

def check_disk_space_wrapper():
    """Check if enough disk space is available"""
    has_space, free_gb, required_gb = check_disk_space(min_free_gb=MIN_FREE_SPACE_GB)
    if not has_space:
        logger.error(f"Low disk space: {free_gb:.2f} GB free (minimum {required_gb:.2f} GB required)")
    return has_space

def ensure_directories():
    """Create necessary directories"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)

def initialize_database():
    """Initialize database files if they don't exist - Creates empty databases"""
    import json
    
    # Ensure database directory exists
    db_dir = os.path.dirname(DB_FILE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"   Created directory: {db_dir}")
    
    # Check if database file exists
    if os.path.exists(DB_FILE):
        print("✓ Database file already exists")
        return
    
    print(f"⚠️ Database file missing: {DB_FILE}")
    print("   Initializing database...")
    
    # Create empty database
    print("   Creating empty database...")
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2)
    print("   ✓ Database initialized")
    print("   Database will be populated as videos are scraped with full metadata")

# Remove old functions - now using utils module
# load_json_safe, save_json_safe, cleanup_temp_files moved to utils.py

def get_processed_codes():
    """Get set of already processed video codes"""
    processed = set()
    try:
        completed = load_json_safe(COMPLETE_FILE, [])
        for v in completed:
            if 'code' in v and 'hosting' in v and v['hosting']:
                processed.add(v['code'])
    except:
        pass
    return processed

def save_to_database(video_data, upload_results):
    """Save video metadata and hosting links to JSON database"""
    try:
        all_videos = load_json_safe(COMPLETE_FILE, [])
        
        # Create video entry
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
                'upload_time': result.get('time', 0)
            }
        
        # Check if video already exists
        existing_index = None
        for i, v in enumerate(all_videos):
            if v.get('code') == video_data.code:
                existing_index = i
                break
        
        if existing_index is not None:
            all_videos[existing_index] = video_entry
        else:
            all_videos.append(video_entry)
        
        # Save database
        return save_json_safe(COMPLETE_FILE, all_videos)
        
    except Exception as e:
        logger.error(f"Database save failed: {e}")
        return False

def discover_videos(scraper):
    """Discover new videos from website"""
    logger.info("="*60)
    logger.info("STARTING VIDEO DISCOVERY")
    logger.info("="*60)
    
    discovered_urls = set()
    
    # Load existing URLs
    try:
        videos = load_json_safe(DB_FILE, [])
        for video in videos:
            if 'source_url' in video:
                discovered_urls.add(video['source_url'])
        logger.info(f"Loaded {len(discovered_urls)} existing URLs")
    except:
        pass
    
    initial_count = len(discovered_urls)
    
    # Discover from multiple sections
    sections = [
        ("Homepage", f"https://jable.tv/", 20),
        ("New Releases", f"https://jable.tv/new/", 30),
        ("Hot/Trending", f"https://jable.tv/hot/", 15),
    ]
    
    for section_name, base_url, max_pages in sections:
        logger.info(f"\nDiscovering: {section_name}")
        
        for page in range(1, max_pages + 1):
            try:
                if page == 1:
                    url = base_url
                else:
                    url = f"{base_url.rstrip('/')}/{page}/"
                
                logger.info(f"  Page {page}...")
                
                video_links = scraper.get_video_links_from_page(url)
                
                if not video_links:
                    logger.info(f"  No videos found, stopping {section_name}")
                    break
                
                before = len(discovered_urls)
                discovered_urls.update(video_links)
                after = len(discovered_urls)
                new_count = after - before
                
                logger.info(f"  Found {len(video_links)} videos ({new_count} new)")
                
                time.sleep(2)  # Be nice to server
                
            except Exception as e:
                logger.error(f"  Error on page {page}: {e}")
                break
    
    # Save discovered URLs
    videos = [{'source_url': url, 'discovered_at': time.strftime('%Y-%m-%d %H:%M:%S')} 
              for url in discovered_urls]
    
    if save_json_safe(DB_FILE, videos):
        new_discovered = len(discovered_urls) - initial_count
        logger.info(f"\n✅ Discovery complete: {new_discovered} new videos found")
        logger.info(f"   Total unique videos: {len(discovered_urls)}")
        return len(discovered_urls)
    else:
        logger.error("Failed to save discovered videos")
        return 0

def process_video(scraper, video_url, video_index, total_videos):
    """Process a single video through the complete pipeline"""
    logger.info(f"\n{'='*60}")
    logger.info(f"VIDEO {video_index}/{total_videos}")
    logger.info(f"{'='*60}")
    logger.info(f"URL: {video_url}")
    
    # Validate URL
    if not validate_url(video_url):
        logger.error(f"❌ Invalid URL format")
        return False
    
    video_data = None
    output_ts = None
    output_mp4 = None
    safe_code = None
    
    try:
        # Step 1: Scrape metadata
        logger.info(f"\n📋 STEP 1: SCRAPING METADATA")
        
        for attempt in range(MAX_RETRIES):
            try:
                video_data = scraper.scrape_video(video_url)
                if video_data:
                    break
                logger.warning(f"Scraping returned None, attempt {attempt+1}/{MAX_RETRIES}")
            except Exception as e:
                logger.error(f"Scraping error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        
        if not video_data:
            logger.error("❌ Scraping failed after all retries")
            return False
        
        logger.info(f"✅ Scraped: {video_data.code} - {video_data.title[:50]}...")
        
        # Sanitize code for filesystem
        safe_code = sanitize_filename(video_data.code)
        
        # Check disk space
        if not check_disk_space_wrapper():
            logger.error("❌ Insufficient disk space")
            return False
        
        # Step 2: Download & decrypt
        logger.info(f"\n📥 STEP 2: DOWNLOADING & DECRYPTING")
        
        output_ts = f"{TEMP_DIR}/{safe_code}.ts"
        output_mp4 = f"{TEMP_DIR}/{safe_code}.mp4"
        
        download_success = False
        for attempt in range(MAX_RETRIES):
            try:
                downloader = HLSDownloader(MAX_WORKERS)
                if downloader.download(video_data.m3u8_url, output_ts, safe_code):
                    download_success = True
                    break
                logger.warning(f"Download failed, attempt {attempt+1}/{MAX_RETRIES}")
            except Exception as e:
                logger.error(f"Download error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        
        if not download_success or not verify_video_file(output_ts, min_size_mb=10):
            logger.error("❌ Download failed or file invalid after all retries")
            cleanup_temp_files(safe_code, TEMP_DIR)
            return False
        
        file_size_gb = os.path.getsize(output_ts) / (1024**3)
        logger.info(f"✅ Downloaded: {file_size_gb:.2f} GB")
        
        # Step 3: Convert to MP4
        logger.info(f"\n🔄 STEP 3: CONVERTING TO MP4")
        
        convert_success = False
        for attempt in range(MAX_RETRIES):
            try:
                if convert_to_mp4(output_ts, output_mp4):
                    convert_success = True
                    break
                logger.warning(f"Conversion failed, attempt {attempt+1}/{MAX_RETRIES}")
            except Exception as e:
                logger.error(f"Conversion error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        
        if not convert_success or not verify_video_file(output_mp4, min_size_mb=10):
            logger.error("❌ Conversion failed or file invalid after all retries")
            cleanup_temp_files(safe_code, TEMP_DIR)
            return False
        
        mp4_size_gb = os.path.getsize(output_mp4) / (1024**3)
        logger.info(f"✅ Converted: {mp4_size_gb:.2f} GB")
        
        # Step 4: Upload to all hosting services
        logger.info(f"\n📤 STEP 4: UPLOADING TO ALL HOSTS")
        
        upload_results = None
        for attempt in range(MAX_RETRIES):
            try:
                upload_results = upload_all(output_mp4, video_data.code, video_data.title)
                if upload_results and upload_results.get('successful'):
                    break
                logger.warning(f"Upload failed, attempt {attempt+1}/{MAX_RETRIES}")
            except Exception as e:
                logger.error(f"Upload error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
        
        if not upload_results or not upload_results.get('successful'):
            logger.error("❌ All uploads failed after all retries")
            cleanup_temp_files(safe_code, TEMP_DIR)
            return False
        
        logger.info(f"✅ Uploaded to {len(upload_results['successful'])} service(s)")
        
        # Step 5: Save to database
        logger.info(f"\n💾 STEP 5: SAVING TO DATABASE")
        
        if not save_to_database(video_data, upload_results):
            logger.warning("⚠️ Database save failed, but continuing...")
        else:
            logger.info("✅ Saved to database")
        
        # Step 6: Cleanup temp files
        logger.info(f"\n🗑️ STEP 6: CLEANING UP")
        cleanup_temp_files(safe_code, TEMP_DIR)
        logger.info("✅ Cleanup complete")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ VIDEO {video_index}/{total_videos} COMPLETE!")
        logger.info(f"{'='*60}")
        
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error processing video: {e}")
        logger.error(traceback.format_exc())
        if safe_code:
            cleanup_temp_files(safe_code, TEMP_DIR)
        return False

def main_loop():
    """Main 24/7 loop"""
    logger.info("""
╔══════════════════════════════════════════════════════════╗
║        24/7 AUTOMATIC JABLE.TV PIPELINE                  ║
╚══════════════════════════════════════════════════════════╝

Features:
✓ Automatic retry on failures
✓ Browser crash recovery
✓ Network error handling
✓ Disk space monitoring
✓ Continuous discovery of new videos
✓ Resume from where it left off
✓ Detailed logging

Starting in 5 seconds... (Ctrl+C to stop)
""")
    
    time.sleep(5)
    
    # Clean up caches and temporary files at startup
    print("🧹 Cleaning up caches and temporary files...")
    try:
        import shutil
        
        # Clear Python cache
        if os.path.exists('__pycache__'):
            shutil.rmtree('__pycache__')
            print("   ✓ Cleared __pycache__")
        
        # Clear temp downloads folder
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
            print(f"   ✓ Cleared {TEMP_DIR}")
        
        # Clear any .lock files
        for file in os.listdir('.'):
            if file.endswith('.lock'):
                try:
                    os.remove(file)
                    print(f"   ✓ Removed {file}")
                except:
                    pass
        
        print("✓ Cleanup complete")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    ensure_directories()
    initialize_database()
    
    last_discovery_time = 0
    cycle_count = 0
    total_successful = 0
    total_failed = 0
    
    while True:
        try:
            cycle_count += 1
            logger.info(f"\n{'#'*60}")
            logger.info(f"CYCLE {cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Total processed: {total_successful} success, {total_failed} failed")
            logger.info(f"{'#'*60}")
            
            # Check if we need to discover new videos
            current_time = time.time()
            if current_time - last_discovery_time > DISCOVERY_INTERVAL:
                logger.info("\n🔍 Time for new discovery cycle...")
                
                scraper = None
                try:
                    scraper = JableScraper(headless=True)
                    discover_videos(scraper)
                    last_discovery_time = current_time
                except Exception as e:
                    logger.error(f"Discovery error: {e}")
                    logger.error(traceback.format_exc())
                finally:
                    if scraper:
                        try:
                            scraper.close()
                        except:
                            pass
                
                time.sleep(10)
            
            # Load videos to process
            videos = load_json_safe(DB_FILE, [])
            if not videos:
                logger.warning("No videos in database, waiting 60 seconds...")
                time.sleep(60)
                continue
            
            # Get already processed videos
            processed_codes = get_processed_codes()
            
            # Filter unprocessed videos
            videos_to_process = [v for v in videos if v.get('code') not in processed_codes]
            
            if not videos_to_process:
                logger.info(f"\n✅ All {len(videos)} videos processed!")
                logger.info("Waiting 1 hour before next discovery cycle...")
                time.sleep(3600)
                last_discovery_time = 0  # Force discovery on next cycle
                continue
            
            logger.info(f"\n📹 Videos remaining: {len(videos_to_process)}/{len(videos)}")
            
            # Process videos one by one
            scraper = None
            try:
                scraper = JableScraper(headless=True)
                
                for i, video in enumerate(videos_to_process, 1):
                    video_url = video.get('source_url')
                    
                    if not video_url:
                        logger.warning(f"Video {i} has no source_url, skipping")
                        continue
                    
                    # Check disk space before each video
                    if not check_disk_space_wrapper():
                        logger.error("Low disk space, pausing for 5 minutes...")
                        time.sleep(300)
                        continue
                    
                    try:
                        if process_video(scraper, video_url, i, len(videos_to_process)):
                            total_successful += 1
                        else:
                            total_failed += 1
                    except Exception as e:
                        logger.error(f"Error processing video {i}: {e}")
                        logger.error(traceback.format_exc())
                        total_failed += 1
                    
                    # Delay between videos
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"Scraper error: {e}")
                logger.error(traceback.format_exc())
            finally:
                if scraper:
                    try:
                        scraper.close()
                    except:
                        pass
            
            # Small delay before next cycle
            logger.info("\n⏳ Cycle complete, waiting 30 seconds before next cycle...")
            time.sleep(30)
            
        except KeyboardInterrupt:
            logger.info("\n\n⚠️ Pipeline stopped by user")
            break
        except Exception as e:
            logger.error(f"\n\n❌ Unexpected error in main loop: {e}")
            logger.error(traceback.format_exc())
            logger.info("Waiting 60 seconds before retry...")
            time.sleep(60)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Pipeline stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
