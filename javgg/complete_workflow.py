#!/usr/bin/env python3
"""
Complete JavaGG Workflow for GitHub Actions
1. Scrape new videos from JavaGG
2. Download video (try multiple servers)
3. Enrich with JAVDatabase
4. Generate preview
5. Upload to all hosting sites
6. Update metadata with URLs
7. Cleanup files
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from javgg_scraper import JavaGGScraper
from javdb_enrichment import enrich_with_javdb
from save_to_database import save_video_to_database
from database_manager import DatabaseManager

# Import preview generator
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools' / 'preview_generator'))
from preview_generator import PreviewGenerator

# Import upload pipeline
sys.path.insert(0, str(Path(__file__).parent.parent / 'upload_pipeline'))
from upload_to_all_hosts import MultiHostUploader


class WorkflowManager:
    """Manages the complete workflow"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.download_dir = self.base_dir / 'downloaded_files'
        self.database_dir = self.base_dir / 'database'
        self.db_manager = DatabaseManager()
        
        # Reusable browser instance (OPTIMIZATION)
        self.scraper = None
        
        # Create directories
        self.download_dir.mkdir(exist_ok=True)
        self.database_dir.mkdir(exist_ok=True)
        
        # Progress tracking
        self.progress_file = self.database_dir / 'workflow_progress.json'
        self.load_progress()
        
        # Ensure progress file exists immediately
        if not self.progress_file.exists():
            self.save_progress()
        
        # Verify dependencies early
        self.verify_dependencies()
    
    def get_scraper(self):
        """Get or create reusable scraper instance with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.scraper is None:
                    self.scraper = JavaGGScraper(headless=True)
                    self.scraper._init_driver()
                
                # Test if browser is still alive
                try:
                    _ = self.scraper.driver.title
                    return self.scraper
                except:
                    # Browser is dead, recreate
                    print(f"  ⚠️ Browser is unresponsive, recreating...")
                    self.cleanup_scraper()
                    self.scraper = None
                    
            except Exception as e:
                error_msg = str(e)[:200]
                print(f"  ⚠️ Failed to initialize browser (attempt {attempt+1}/{max_retries}): {error_msg}")
                self.cleanup_scraper()
                self.scraper = None
                
                if attempt < max_retries - 1:
                    print(f"  ⏳ Waiting 10 seconds before retry...")
                    time.sleep(10)
                else:
                    print(f"\n❌ CRITICAL: Cannot initialize browser after {max_retries} attempts")
                    print(f"   This usually means Chrome/Chromium is not properly installed")
                    print(f"   or there's a system-level issue in GitHub Actions")
                    raise Exception(f"Browser initialization failed: {error_msg}")
        
        return self.scraper
    
    def cleanup_scraper(self):
        """Cleanup scraper at end of workflow"""
        if self.scraper:
            try:
                self.scraper.close()
            except:
                pass
            self.scraper = None
    
    def verify_dependencies(self):
        """Verify all required dependencies are available"""
        print("\n🔍 Verifying dependencies...")
        
        missing = []
        
        # Check ffmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                print("  ✅ ffmpeg available")
            else:
                missing.append("ffmpeg")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            missing.append("ffmpeg")
            print("  ⚠️ ffmpeg not found")
        
        # Check ffprobe
        try:
            result = subprocess.run(['ffprobe', '-version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                print("  ✅ ffprobe available")
            else:
                missing.append("ffprobe")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            missing.append("ffprobe")
            print("  ⚠️ ffprobe not found")
        
        # Check yt-dlp
        try:
            result = subprocess.run(['yt-dlp', '--version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                print("  ✅ yt-dlp available")
            else:
                missing.append("yt-dlp")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            missing.append("yt-dlp")
            print("  ⚠️ yt-dlp not found")
        
        if missing:
            print(f"\n⚠️ WARNING: Missing dependencies: {', '.join(missing)}")
            print(f"   Some features may not work properly")
        else:
            print("\n✅ All dependencies available")
    
    def load_progress(self):
        """Load workflow progress"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                self.progress = json.load(f)
        else:
            self.progress = {
                'last_scraped_page': 1,
                'processed_videos': [],
                'failed_videos': [],
                'pending_enrichment': [],
                'last_run': None
            }
    
    def save_progress(self):
        """Save workflow progress with atomic write"""
        self.progress['last_run'] = datetime.now().isoformat()
        
        # Atomic write: write to temp file first, then rename
        temp_file = self.progress_file.with_suffix('.json.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self.progress_file)
        except Exception as e:
            print(f"  ⚠️ Failed to save progress: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def scrape_new_videos(self, max_videos: int = 0) -> List[str]:
        """
        Scrape new video URLs from JavaGG /new-post/ page
        max_videos: 0 = unlimited, otherwise limit to N videos
        Returns list of video URLs
        """
        print("\n" + "="*70)
        print("STEP 1: SCRAPING NEW VIDEOS FROM JAVGG")
        if max_videos == 0:
            print("MODE: UNLIMITED - Processing all new videos")
        else:
            print(f"MODE: LIMITED - Processing up to {max_videos} videos")
        print("="*70)
        
        print("\nInitializing scraper...")
        scraper = self.get_scraper()  # Reuse browser instance
        new_urls = []
        
        try:
            # Initialize driver
            scraper._init_driver()
            print("Browser driver ready!")
            
            # Get latest videos from /new-post/ page
            page = self.progress['last_scraped_page']
            max_pages = 10  # Limit to 10 pages per run to avoid timeout
            pages_scraped = 0
            
            # Keep scraping pages until we have enough videos or no more videos
            consecutive_empty_pages = 0
            max_empty_pages = 3  # Stop after 3 consecutive empty pages
            
            while pages_scraped < max_pages:
                pages_scraped += 1
                print(f"\n📄 Scraping page {page}... ({pages_scraped}/{max_pages})")
                
                # Navigate to JavaGG new-post page
                base_url = "https://javgg.net/new-post/"
                if page > 1:
                    base_url = f"https://javgg.net/new-post/page/{page}/"
                
                print(f"  Loading: {base_url}")
                
                # Try loading the page with retry on Cloudflare block
                max_retries = 3
                page_loaded = False
                
                for retry in range(max_retries):
                    if retry > 0:
                        print(f"  🔄 Retry {retry}/{max_retries-1}...")
                        time.sleep(5)  # Wait before retry
                    
                    try:
                        scraper.driver.get(base_url)
                    except Exception as e:
                        print(f"  ⚠️ Page load error: {str(e)[:100]}")
                    
                    # Wait for Cloudflare check to complete
                    print(f"  Waiting for Cloudflare check...")
                    max_wait = 30  # Increased back to 30 seconds for GitHub Actions
                    waited = 0
                    cloudflare_passed = False
                    
                    while waited < max_wait:
                        time.sleep(2)  # Check every 2 seconds instead of 1
                        waited += 2
                        
                        # Check multiple indicators that Cloudflare is done
                        try:
                            title = scraper.driver.title
                            url = scraper.driver.current_url
                            
                            # Check if Cloudflare challenge is gone
                            if "Just a moment" not in title and "Cloudflare" not in title:
                                # Also check if we're on the actual page
                                if "javgg.net" in url and "/new-post" in url:
                                    print(f"  ✅ Cloudflare check passed after {waited}s")
                                    cloudflare_passed = True
                                    page_loaded = True
                                    break
                        except:
                            pass
                        
                        if waited % 10 == 0:  # Print every 10 seconds
                            print(f"  ⏳ Still waiting for Cloudflare... ({waited}s)")
                    
                    if cloudflare_passed:
                        break
                    
                    if retry < max_retries - 1:
                        print(f"  ⚠️ Cloudflare check failed, will retry...")
                
                if not page_loaded:
                    print(f"  ❌ Failed to bypass Cloudflare after {max_retries} attempts")
                    break
                
                # Additional wait for page to fully load
                time.sleep(3)
                
                # Check if page loaded
                print(f"  Current URL: {scraper.driver.current_url}")
                print(f"  Page title: {scraper.driver.title}")
                
                # Check if still blocked by Cloudflare
                if "Just a moment" in scraper.driver.title or "Cloudflare" in scraper.driver.page_source:
                    print(f"  ❌ Still blocked by Cloudflare after all retries")
                    
                    # Save page source for debugging
                    debug_file = self.download_dir / f"cloudflare_blocked_page_{page}.html"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(scraper.driver.page_source)
                    print(f"  ⚠️ Saved blocked page to {debug_file} for debugging")
                    
                    # Cannot proceed
                    break
                
                # Scroll down to trigger lazy loading
                scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Reduced from 2 to 1
                
                # Scroll again to ensure all content loads
                scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Reduced from 2 to 1
                
                # Find all video links
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(scraper.driver.page_source, 'html.parser')
                
                # Debug: Save page source if no links found
                all_links = soup.find_all('a', href=True)
                print(f"  Debug: Total links on page: {len(all_links)}")
                
                # Look for links with /jav/ in them
                video_links = soup.find_all('a', href=lambda x: x and '/jav/' in x)
                
                print(f"  Found {len(video_links)} video links")
                
                # If no links found, save page source for debugging
                if len(video_links) == 0:
                    debug_file = self.download_dir / f"debug_page_{page}.html"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(scraper.driver.page_source)
                    print(f"  ⚠️ Saved page source to {debug_file} for debugging")
                    print(f"  Page title: {soup.find('title').text if soup.find('title') else 'N/A'}")
                    print(f"  Page URL: {scraper.driver.current_url}")
                    
                    # Check if still blocked by Cloudflare
                    if "Just a moment" in scraper.driver.title or "Cloudflare" in scraper.driver.page_source:
                        print(f"  ❌ Still blocked by Cloudflare - cannot proceed")
                        break
                
                if not video_links or len(video_links) == 0:
                    print(f"  ℹ️ No video links found on page {page}")
                    break
                
                page_new_count = 0
                seen_codes = set()  # Track codes we've already added from this page
                
                for link in video_links:
                    url = link.get('href')
                    if url:
                        # Make sure URL is absolute
                        if not url.startswith('http'):
                            url = 'https://javgg.net' + url if url.startswith('/') else 'https://javgg.net/' + url
                        
                        # Extract video code
                        code = url.rstrip('/').split('/')[-1].upper()
                        
                        # Skip duplicates from same page
                        if code in seen_codes:
                            continue
                        
                        # Skip if already processed
                        if code in self.progress['processed_videos']:
                            continue
                        
                        # Skip if in failed list
                        if code in self.progress['failed_videos']:
                            continue
                        
                        # Skip if already in new_urls (from previous pages)
                        if url in new_urls:
                            continue
                        
                        new_urls.append(url)
                        seen_codes.add(code)
                        page_new_count += 1
                        print(f"  ✅ Added: {code}")
                        
                        # Check if we've reached the limit (if set)
                        if max_videos > 0 and len(new_urls) >= max_videos:
                            break
                
                print(f"  ✅ Found {page_new_count} new videos on page {page}")
                
                # Track consecutive empty pages
                if page_new_count == 0:
                    consecutive_empty_pages += 1
                    print(f"  ⚠️ Empty page count: {consecutive_empty_pages}/{max_empty_pages}")
                else:
                    consecutive_empty_pages = 0  # Reset counter
                
                # Stop if too many consecutive empty pages
                if consecutive_empty_pages >= max_empty_pages:
                    print(f"  ℹ️ {max_empty_pages} consecutive empty pages - stopping scrape")
                    break
                
                # Check if we've reached the limit (if set)
                if max_videos > 0 and len(new_urls) >= max_videos:
                    # Don't increment page - we'll continue from here next time
                    print(f"  ℹ️ Reached max_videos limit, staying on page {page}")
                    break
                
                # If no new videos found on this page, we've caught up
                if page_new_count == 0:
                    print(f"  ℹ️ No new videos on page {page} - caught up!")
                    # Move to next page since this one is done
                    self.progress['last_scraped_page'] = page + 1
                    self.save_progress()
                    # Don't break yet - check a few more pages
                    page += 1
                    continue
                
                # All videos on this page were processed, move to next page
                self.progress['last_scraped_page'] = page + 1
                self.save_progress()
                
                # Move to next page
                page += 1
            
            print(f"\n✅ Total found: {len(new_urls)} new videos to process")
            print(f"   Scraped {pages_scraped} pages")
            
        except Exception as e:
            print(f"❌ Error scraping: {str(e)}")
            return []
        
        # Don't close scraper - reuse it
        return new_urls
    
    def validate_video_file(self, video_file: Path) -> bool:
        """
        Validate that a file is actually a video and not corrupted
        Returns True if valid, False otherwise
        """
        try:
            validate_cmd = [
                'ffprobe', '-v', 'error',
                '-show_format',
                '-show_streams',
                '-of', 'json',
                str(video_file)
            ]
            validate_result = subprocess.run(validate_cmd, capture_output=True, text=True, timeout=10)
            
            if validate_result.returncode != 0:
                print(f"  ⚠️ ffprobe failed to read file")
                return False
            
            validate_data = json.loads(validate_result.stdout)
            
            # Check format name - should be mp4, mov, avi, etc. NOT png_pipe
            format_name = validate_data.get('format', {}).get('format_name', '')
            if 'png' in format_name.lower() or 'image' in format_name.lower():
                print(f"  ⚠️ File is not a video (format: {format_name})")
                return False
            
            # Check if there's a video stream
            video_streams = [s for s in validate_data.get('streams', []) if s.get('codec_type') == 'video']
            if not video_streams:
                print(f"  ⚠️ No video stream found")
                return False
            
            # Check video codec - should be h264, hevc, etc. NOT png
            video_codec = video_streams[0].get('codec_name', '')
            if video_codec.lower() in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
                print(f"  ⚠️ File contains images, not video (codec: {video_codec})")
                return False
            
            print(f"  ✅ Video file is valid (format: {format_name}, codec: {video_codec})")
            return True
            
        except Exception as e:
            print(f"  ⚠️ Validation error: {str(e)[:100]}")
            return False
    
    def download_video(self, video_url: str, video_code: str) -> Optional[str]:
        """
        Download video trying multiple methods
        Returns path to downloaded video file
        """
        print(f"\n📥 Downloading video: {video_code}")
        
        scraper = self.get_scraper()  # Reuse browser instance
        
        try:
            # Scrape to get embed URLs
            video_data = scraper.scrape_video(video_url)
            
            if not video_data:
                print(f"❌ Failed to scrape video metadata")
                return None
            
            video_file = self.download_dir / f"{video_code}.mp4"
            
            # Skip download if file already exists and is large enough
            if video_file.exists() and video_file.stat().st_size > 10 * 1024 * 1024:  # > 10MB
                print(f"  ✅ Already downloaded: {video_file.name} ({video_file.stat().st_size / 1024 / 1024:.1f} MB)")
                return str(video_file)
            
            download_url = video_data.m3u8_url or video_data.embed_url
            print(f"  🔗 Download URL: {download_url[:60]}...")
            
            # Try HLS downloader first if we have M3U8 URL
            if video_data.m3u8_url and '.m3u8' in video_data.m3u8_url:
                print(f"  📥 Using HLS downloader...")
                try:
                    from hls_downloader import JavaGGHLSDownloader
                    hls_dl = JavaGGHLSDownloader(max_workers=16)
                    
                    # Download with timeout
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError("HLS download timeout")
                    
                    # Set 10 minute timeout (only on Unix)
                    if hasattr(signal, 'SIGALRM'):
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(600)  # 10 minutes
                    
                    try:
                        download_success = hls_dl.download(video_data.m3u8_url, str(video_file))
                    finally:
                        if hasattr(signal, 'SIGALRM'):
                            signal.alarm(0)  # Cancel alarm
                    
                    if download_success:
                        # Validate the downloaded file
                        if video_file.exists() and video_file.stat().st_size > 1024 * 1024:
                            print(f"  ✅ Downloaded: {video_file.name} ({video_file.stat().st_size / 1024 / 1024:.1f} MB)")
                            
                            # Validate format
                            if self.validate_video_file(video_file):
                                return str(video_file)
                            else:
                                print(f"  ⚠️ Video validation failed, will try yt-dlp...")
                                if video_file.exists():
                                    video_file.unlink()
                        else:
                            print(f"  ⚠️ Downloaded file too small or missing")
                    else:
                        print(f"  ⚠️ HLS download failed")
                        
                except TimeoutError:
                    print(f"  ⚠️ HLS download timeout (10 minutes)")
                    if video_file.exists():
                        video_file.unlink()
                except Exception as e:
                    print(f"  ⚠️ HLS downloader failed: {str(e)[:100]}")
                
                print(f"  ⏭️ Falling back to yt-dlp...")
            
            # Fallback to yt-dlp
            print(f"  📥 Attempting download with yt-dlp...")
            
            # Check if yt-dlp is available
            try:
                subprocess.run(['yt-dlp', '--version'], capture_output=True, timeout=5, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                print(f"  ⚠️ yt-dlp not available")
                print(f"  ⚠️ Cannot download video without yt-dlp")
                return None
            
            cmd = [
                'yt-dlp',
                '-o', str(video_file),
                '--no-warnings',
                '--no-check-certificate',
                '--concurrent-fragments', '16',
                '--retries', '3',  # Reduced from 5
                '--fragment-retries', '3',  # Reduced from 5
                '--socket-timeout', '30',  # Add socket timeout
                '--quiet',  # Suppress progress output
                '--progress-template', '%(progress.downloaded_bytes)s/%(progress.total_bytes)s',
                download_url
            ]
            
            # Run with progress bar and timeout
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Show visual progress bar
                print(f"     ", end='', flush=True)
                last_percent = 0
                bar_width = 50
                
                # Set timeout for the entire download (2 minutes for initial response)
                import time
                start_time = time.time()
                initial_timeout = 120  # 2 minutes to start
                download_timeout = 600  # 10 minutes total
                
                line_count = 0
                has_progress = False
                
                for line in process.stdout:
                    line_count += 1
                    elapsed = time.time() - start_time
                    
                    # Check if we got any progress
                    if '/' in line:
                        has_progress = True
                    
                    # If no progress after initial timeout, kill it
                    if not has_progress and elapsed > initial_timeout:
                        process.kill()
                        print(f"\n  ❌ No download started after {initial_timeout} seconds")
                        print(f"  ⚠️ This embed URL may not be supported by yt-dlp")
                        return None
                    
                    # Check total timeout
                    if elapsed > download_timeout:
                        process.kill()
                        print(f"\n  ❌ Download timeout ({download_timeout//60} minutes)")
                        return None
                    
                    line = line.strip()
                    if '/' in line:
                        try:
                            downloaded, total = line.split('/')
                            percent = int((int(downloaded) / int(total)) * 100)
                            
                            # Update progress bar every 2%
                            if percent >= last_percent + 2:
                                filled = int(bar_width * percent / 100)
                                bar = '█' * filled + '░' * (bar_width - filled)
                                print(f"\r     [{bar}] {percent}%", end='', flush=True)
                                last_percent = percent
                        except:
                            pass
                
                # Complete the progress bar
                bar = '█' * bar_width
                print(f"\r     [{bar}] 100%")
                
                process.wait(timeout=10)  # Wait up to 10 more seconds for process to finish
                result_code = process.returncode
                
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"\n  ❌ Download process timeout")
                return None
            except Exception as e:
                print(f"\n  ❌ Download error: {str(e)[:100]}")
                return None
            
            if result_code == 0 and video_file.exists() and video_file.stat().st_size > 1024 * 1024:
                print(f"  ✅ Downloaded: {video_file.name} ({video_file.stat().st_size / 1024 / 1024:.1f} MB)")
                
                # Validate the video file
                print(f"  🔍 Validating video file...")
                if self.validate_video_file(video_file):
                    return str(video_file)
                else:
                    print(f"  ⚠️ Downloaded file is corrupted or not a video")
                    print(f"  ⚠️ This usually means the stream is encrypted or protected")
                    print(f"  ⚠️ Deleting corrupted file...")
                    if video_file.exists():
                        video_file.unlink()
                    return None
            
            # If yt-dlp failed, log the error
            print(f"  ❌ yt-dlp failed")
            print(f"  ⚠️ Download not supported for this embed type")
            return None
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ Download timeout (10 minutes)")
            return None
        except Exception as e:
            print(f"  ❌ Error downloading: {str(e)}")
            return None
        
        # Don't close scraper - reuse it
    
    def enrich_and_save(self, video_url: str, video_code: str) -> Dict:
        """
        Scrape, enrich and save video metadata
        """
        print(f"\n📊 Enriching metadata: {video_code}")
        
        scraper = self.get_scraper()  # Reuse browser instance
        
        try:
            # Scrape JavaGG
            video_data = scraper.scrape_video(video_url)
            
            if not video_data:
                print(f"  ❌ Failed to scrape video")
                return None
            
            # Convert to dict
            video_dict = video_data.__dict__.copy()
            
            # Enrich with JAVDatabase
            enriched_data = enrich_with_javdb(video_dict, headless=True)
            
            # Check if JAVDatabase enrichment failed
            if not enriched_data.get('javdb_available'):
                print(f"  ⚠️ JAVDatabase not available - adding to retry queue")
                self.progress['pending_enrichment'].append({
                    'code': video_code,
                    'url': video_url,
                    'retry_after': (datetime.now().timestamp() + 2 * 24 * 3600)  # 2 days
                })
            
            # Save to database
            save_video_to_database(enriched_data, enriched=enriched_data.get('javdb_available', False))
            
            print(f"  ✅ Metadata saved to database")
            
            return enriched_data
        
        except Exception as e:
            print(f"  ❌ Error enriching: {str(e)}")
            return None
        
        # Don't close scraper - reuse it
    
    def generate_preview_video(self, video_file: str, video_code: str, file_size_mb: float) -> Optional[str]:
        """
        Generate preview video - OPTIONAL (skip for large files)
        """
        print(f"\n🎬 Generating preview: {video_code}")
        
        # Skip preview for very large files (> 2GB) to save time
        if file_size_mb > 2048:
            print(f"  ⏭️ Skipping preview for large file ({file_size_mb:.1f} MB)")
            return None
        
        try:
            preview_file = self.download_dir / f"{video_code}_preview.mp4"
            
            # Check if video file exists and is valid
            if not os.path.exists(video_file):
                print(f"  ❌ Video file not found: {video_file}")
                return None
            
            file_size = os.path.getsize(video_file)
            if file_size < 1024 * 1024:  # Less than 1MB
                print(f"  ❌ Video file too small ({file_size} bytes)")
                return None
            
            print(f"  📹 Video file: {file_size / 1024 / 1024:.1f} MB")
            
            # Check if ffprobe is available
            try:
                subprocess.run(['ffprobe', '-version'], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"  ⚠️ ffprobe not found - skipping preview generation")
                return None
            
            # Validate video file first
            print(f"  🔍 Validating video format...")
            try:
                validate_cmd = [
                    'ffprobe', '-v', 'error',
                    '-show_format',
                    '-show_streams',
                    '-of', 'json',
                    str(video_file)
                ]
                validate_result = subprocess.run(validate_cmd, capture_output=True, text=True, timeout=10)
                
                if validate_result.returncode != 0:
                    print(f"  ⚠️ Video validation failed - skipping preview")
                    return None
                
                validate_data = json.loads(validate_result.stdout)
                
                # Check format name - should be mp4, mov, avi, etc. NOT png_pipe
                format_name = validate_data.get('format', {}).get('format_name', '')
                if 'png' in format_name.lower() or 'image' in format_name.lower():
                    print(f"  ⚠️ File is not a video (detected as {format_name}) - skipping preview")
                    return None
                
                # Check if there's a video stream
                video_streams = [s for s in validate_data.get('streams', []) if s.get('codec_type') == 'video']
                if not video_streams:
                    print(f"  ⚠️ No video stream found - skipping preview")
                    return None
                
                # Check video codec - should be h264, hevc, etc. NOT png
                video_codec = video_streams[0].get('codec_name', '')
                if video_codec.lower() in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
                    print(f"  ⚠️ File contains images, not video (codec: {video_codec}) - skipping preview")
                    return None
                
                print(f"  ✅ Video format validated (format: {format_name}, codec: {video_codec})")
                
            except Exception as e:
                print(f"  ⚠️ Validation error: {str(e)} - skipping preview")
                return None
            
            # Generate preview with optimized settings
            print(f"  🎬 Starting preview generation...")
            generator = PreviewGenerator(video_file)
            result = generator.generate_preview(
                output_path=str(preview_file),
                target_duration=90,  # Reduced from 120 to 90 seconds
                clip_duration=2.0,  # Reduced from 2.5 to 2.0
                resolution="480",  # Reduced from 720 to 480 for speed
                crf=28,  # Increased from 23 to 28 (faster encoding)
                fps=24,  # Reduced from 30 to 24
                cleanup=True,
                parallel=True,
                max_workers=16  # Reduced from 32 to 16
            )
            
            if result.get('success') and preview_file.exists():
                print(f"  ✅ Preview generated: {preview_file.name} ({preview_file.stat().st_size / 1024 / 1024:.1f} MB)")
                return str(preview_file)
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"  ⚠️ Preview generation failed: {error_msg}")
                return None
                
        except Exception as e:
            print(f"  ⚠️ Error generating preview: {str(e)}")
            return None
    
    def upload_videos(self, video_file: str, preview_file: str, video_code: str) -> Dict:
        """
        Upload full video to all hosts and preview to Internet Archive
        Returns dict with all URLs
        """
        print(f"\n☁️ Uploading videos: {video_code}")
        
        urls = {}
        
        try:
            # Upload full video to all hosting sites
            print(f"\n  📤 Uploading full video to hosting sites...")
            print(f"     File: {os.path.basename(video_file)}")
            print(f"     Size: {os.path.getsize(video_file) / 1024 / 1024:.1f} MB")
            
            uploader = MultiHostUploader()
            
            # Show which hosts are configured
            if uploader.uploaders:
                print(f"     Hosts: {', '.join(uploader.uploaders.keys())}")
            else:
                print(f"     ⚠️ No upload hosts configured (check .env file)")
            
            results = uploader.upload_to_all(video_file, title=video_code)
            
            # Extract URLs from results
            hosting_urls = {}
            for host, result in results.items():
                if result.get('success'):
                    print(f"     ✅ {host}: Success")
                    hosting_urls[host] = {
                        'embed_url': result.get('embed_url', ''),
                        'download_url': result.get('download_url', ''),
                        'file_code': result.get('file_code', '')
                    }
                else:
                    print(f"     ❌ {host}: Failed")
            
            urls['hosting'] = hosting_urls
            print(f"  ✅ Uploaded to {len(hosting_urls)} hosting sites")
            
            # For preview, we'll skip Internet Archive for now (can add later)
            # Internet Archive upload is complex and may not be needed
            if preview_file:
                print(f"\n  ℹ️ Preview saved locally: {preview_file}")
                urls['preview_file'] = preview_file
            
            print(f"\n  ✅ Uploads complete")
            print(f"     - Hosting sites: {len(hosting_urls)} URLs")
            
            return urls
            
        except Exception as e:
            print(f"  ❌ Error uploading: {str(e)}")
            return urls
    
    def update_metadata_with_urls(self, video_code: str, urls: Dict):
        """
        Update video metadata in database with hosting URLs
        """
        print(f"\n💾 Updating metadata with URLs: {video_code}")
        
        try:
            # Load current database
            db_file = self.database_dir / 'combined_videos.json'
            with open(db_file, 'r', encoding='utf-8') as f:
                db = json.load(f)
            
            # Find video
            for video in db['videos']:
                if video['code'] == video_code:
                    video['hosting_urls'] = urls.get('hosting', {})
                    video['preview_url'] = urls.get('internet_archive', '')
                    video['uploaded_at'] = datetime.now().isoformat()
                    break
            
            # Save database
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Metadata updated")
            
        except Exception as e:
            print(f"  ❌ Error updating metadata: {str(e)}")
    
    def cleanup_files(self, video_code: str):
        """
        Delete video files and temporary JSON files
        """
        print(f"\n🗑️ Cleaning up files: {video_code}")
        
        try:
            # Delete video file
            video_file = self.download_dir / f"{video_code}.mp4"
            if video_file.exists():
                video_file.unlink()
                print(f"  ✅ Deleted: {video_file.name}")
            
            # Delete preview file
            preview_file = self.download_dir / f"{video_code}_preview.mp4"
            if preview_file.exists():
                preview_file.unlink()
                print(f"  ✅ Deleted: {preview_file.name}")
            
            # Delete JSON files
            for json_file in self.download_dir.glob(f"{video_code}*.json"):
                json_file.unlink()
                print(f"  ✅ Deleted: {json_file.name}")
            
        except Exception as e:
            print(f"  ⚠️ Cleanup error: {str(e)}")
    
    def commit_and_push_changes(self, video_code: str):
        """
        Commit and push database changes to GitHub with retry logic
        This ensures we don't lose data if workflow times out
        """
        if not os.getenv('GITHUB_ACTIONS'):
            print(f"  ℹ️ Not in GitHub Actions, skipping git commit")
            return
        
        print(f"\n💾 Committing changes for {video_code}...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Add database files
                subprocess.run(['git', 'add', 'database/combined_videos.json'], check=True, timeout=30)
                subprocess.run(['git', 'add', 'database/workflow_progress.json'], check=True, timeout=30)
                subprocess.run(['git', 'add', 'database/stats.json'], check=True, stderr=subprocess.DEVNULL, timeout=30)
                subprocess.run(['git', 'add', 'database/progress_tracking.json'], check=True, stderr=subprocess.DEVNULL, timeout=30)
                
                # Check if there are changes
                result = subprocess.run(['git', 'diff', '--staged', '--quiet'], capture_output=True, timeout=30)
                
                if result.returncode != 0:  # There are changes
                    # Commit
                    commit_msg = f"Update database: {video_code} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    subprocess.run(['git', 'commit', '-m', commit_msg], check=True, timeout=30)
                    
                    # Push with retry
                    push_success = False
                    for push_attempt in range(3):
                        try:
                            subprocess.run(['git', 'push'], check=True, timeout=60)
                            push_success = True
                            break
                        except subprocess.TimeoutExpired:
                            print(f"  ⚠️ Push timeout (attempt {push_attempt+1}/3)")
                            if push_attempt < 2:
                                time.sleep(5)
                        except subprocess.CalledProcessError as e:
                            print(f"  ⚠️ Push failed (attempt {push_attempt+1}/3): {e}")
                            if push_attempt < 2:
                                # Pull first in case of conflicts
                                try:
                                    subprocess.run(['git', 'pull', '--rebase'], check=True, timeout=60)
                                except:
                                    pass
                                time.sleep(5)
                    
                    if push_success:
                        print(f"  ✅ Changes committed and pushed")
                    else:
                        print(f"  ⚠️ Push failed after 3 attempts")
                else:
                    print(f"  ℹ️ No changes to commit")
                
                return  # Success, exit retry loop
                    
            except subprocess.TimeoutExpired:
                print(f"  ⚠️ Git operation timeout (attempt {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(5)
            except Exception as e:
                print(f"  ⚠️ Git commit failed (attempt {attempt+1}/{max_retries}): {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(5)
        
        print(f"  ⚠️ Git operations failed after {max_retries} attempts")
        # Don't fail the workflow if git commit fails
    
    def process_video(self, video_url: str) -> bool:
        """
        Process a single video through the complete workflow with error recovery
        """
        video_code = video_url.rstrip('/').split('/')[-1].upper()
        
        print("\n" + "="*70)
        print(f"PROCESSING VIDEO: {video_code}")
        print("="*70)
        
        video_file = None
        metadata = None
        
        try:
            # Step 1: Download video
            try:
                video_file = self.download_video(video_url, video_code)
            except Exception as e:
                print(f"  ❌ Download error: {str(e)[:100]}")
                # Try to recover browser if it crashed
                if "browser" in str(e).lower() or "driver" in str(e).lower():
                    print(f"  🔄 Browser crashed, recreating...")
                    self.cleanup_scraper()
            
            # Step 2: Enrich and save metadata (even if download failed)
            try:
                metadata = self.enrich_and_save(video_url, video_code)
            except Exception as e:
                print(f"  ❌ Enrichment error: {str(e)[:100]}")
                # Try to recover browser if it crashed
                if "browser" in str(e).lower() or "driver" in str(e).lower():
                    print(f"  🔄 Browser crashed, recreating...")
                    self.cleanup_scraper()
            
            if not metadata:
                print(f"  ❌ Enrichment failed, marking as failed")
                if video_file and os.path.exists(video_file):
                    self.cleanup_files(video_code)
                if video_code not in self.progress['failed_videos']:
                    self.progress['failed_videos'].append(video_code)
                self.save_progress()
                return False
            
            # If we have metadata but no video, save metadata only
            if not video_file:
                print(f"  ℹ️ Video download failed, but metadata saved")
                print(f"  ℹ️ Skipping preview, upload, and cleanup")
                
                # Mark as processed (metadata saved)
                if video_code not in self.progress['processed_videos']:
                    self.progress['processed_videos'].append(video_code)
                self.save_progress()
                
                # Commit changes
                if len(self.progress['processed_videos']) % 5 == 0:
                    try:
                        self.commit_and_push_changes(f"Batch update: {len(self.progress['processed_videos'])} videos")
                    except Exception as e:
                        print(f"  ⚠️ Git commit error: {str(e)[:100]}")
                
                print(f"\n✅ Metadata saved for: {video_code} (no video file)")
                return True
            
            # Step 3: Generate preview (with file size for optimization)
            preview_file = None
            try:
                if video_file and os.path.exists(video_file):
                    file_size_mb = os.path.getsize(video_file) / 1024 / 1024
                    preview_file = self.generate_preview_video(video_file, video_code, file_size_mb)
                else:
                    print(f"  ⚠️ Video file not found, skipping preview")
            except Exception as e:
                print(f"  ⚠️ Preview generation error: {str(e)[:100]}")
                # Preview is optional, continue anyway
            
            # Step 4: Upload videos
            urls = {}
            try:
                urls = self.upload_videos(video_file, preview_file, video_code)
            except Exception as e:
                print(f"  ⚠️ Upload error: {str(e)[:100]}")
                # Continue anyway, we can retry uploads later
            
            # Step 5: Update metadata with URLs
            try:
                self.update_metadata_with_urls(video_code, urls)
            except Exception as e:
                print(f"  ⚠️ Metadata update error: {str(e)[:100]}")
            
            # Step 6: Cleanup files
            try:
                self.cleanup_files(video_code)
            except Exception as e:
                print(f"  ⚠️ Cleanup error: {str(e)[:100]}")
            
            # Mark as processed
            if video_code not in self.progress['processed_videos']:
                self.progress['processed_videos'].append(video_code)
            self.save_progress()
            
            # Commit and push changes (batched every 5 videos for speed)
            if len(self.progress['processed_videos']) % 5 == 0:
                try:
                    self.commit_and_push_changes(f"Batch update: {len(self.progress['processed_videos'])} videos")
                except Exception as e:
                    print(f"  ⚠️ Git commit error: {str(e)[:100]}")
            
            print(f"\n✅ Successfully processed: {video_code}")
            return True
            
        except Exception as e:
            print(f"\n❌ Unexpected error processing {video_code}: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            
            # Try to recover browser if it crashed
            if "browser" in str(e).lower() or "driver" in str(e).lower():
                print(f"  🔄 Browser may have crashed, recreating...")
                self.cleanup_scraper()
            
            # Mark as failed
            if video_code not in self.progress['failed_videos']:
                self.progress['failed_videos'].append(video_code)
            self.save_progress()
            return False
    
    def retry_pending_enrichments(self):
        """
        Retry videos that failed JAVDatabase enrichment
        """
        print("\n" + "="*70)
        print("RETRYING PENDING ENRICHMENTS")
        print("="*70)
        
        current_time = datetime.now().timestamp()
        still_pending = []
        
        for item in self.progress['pending_enrichment']:
            if current_time >= item['retry_after']:
                print(f"\n🔄 Retrying: {item['code']}")
                
                # Try to enrich again
                metadata = self.enrich_and_save(item['url'], item['code'])
                
                if metadata and metadata.get('javdb_available'):
                    print(f"  ✅ Enrichment successful")
                else:
                    # Add back to pending with new retry time
                    item['retry_after'] = current_time + 2 * 24 * 3600
                    still_pending.append(item)
            else:
                still_pending.append(item)
        
        self.progress['pending_enrichment'] = still_pending
        self.save_progress()
    
    def run(self, max_videos: int = 0):
        """
        Run the complete workflow - processes videos one at a time
        max_videos: 0 = unlimited, otherwise limit to N videos
        """
        print("\n" + "="*70)
        print("JAVGG COMPLETE WORKFLOW")
        print("="*70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if max_videos == 0:
            print("Mode: UNLIMITED - Processing videos one by one until done or timeout")
        else:
            print(f"Mode: LIMITED - Processing up to {max_videos} videos one by one")
        
        print("\nChecking pending enrichments...")
        # Retry pending enrichments first
        if self.progress['pending_enrichment']:
            self.retry_pending_enrichments()
        else:
            print("  No pending enrichments")
        
        print("\nStarting video processing (one at a time)...")
        
        # Process videos one at a time
        success_count = 0
        total_processed = 0
        
        # Keep processing until we hit the limit or run out of videos
        while True:
            # Check if we've reached the limit
            if max_videos > 0 and total_processed >= max_videos:
                print(f"\n✅ Reached max_videos limit ({max_videos})")
                break
            
            # Scrape just 1 video at a time
            print(f"\n{'='*70}")
            print(f"LOOKING FOR NEXT VIDEO (Processed: {total_processed}/{max_videos if max_videos > 0 else '∞'})")
            print(f"{'='*70}")
            
            video_urls = self.scrape_new_videos(max_videos=1)
            
            if not video_urls:
                print("\n✅ No more new videos to process")
                break
            
            # Process the single video
            video_url = video_urls[0]
            total_processed += 1
            
            print(f"\n{'='*70}")
            print(f"VIDEO {total_processed}/{max_videos if max_videos > 0 else '∞'}")
            print(f"{'='*70}")
            
            if self.process_video(video_url):
                success_count += 1
        
        # Summary
        print("\n" + "="*70)
        print("WORKFLOW COMPLETE")
        print("="*70)
        print(f"✅ Successfully processed: {success_count}/{total_processed}")
        print(f"❌ Failed: {total_processed - success_count}")
        print(f"⏳ Pending enrichment: {len(self.progress['pending_enrichment'])}")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Final commit for remaining videos
        if success_count > 0:
            self.commit_and_push_changes(f"Final update: {success_count} videos")
        
        # Cleanup browser
        self.cleanup_scraper()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='JavaGG Complete Workflow')
    parser.add_argument('--max-videos', type=int, default=0, help='Maximum videos to process (0 = unlimited)')
    parser.add_argument('--base-dir', type=str, default=None, help='Base directory')
    
    args = parser.parse_args()
    
    workflow = WorkflowManager(base_dir=args.base_dir)
    workflow.run(max_videos=args.max_videos)
