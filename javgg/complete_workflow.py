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
        self.db_manager = DatabaseManager()  # DatabaseManager doesn't take arguments
        
        # Create directories
        self.download_dir.mkdir(exist_ok=True)
        self.database_dir.mkdir(exist_ok=True)
        
        # Progress tracking
        self.progress_file = self.database_dir / 'workflow_progress.json'
        self.load_progress()
        
        # Ensure progress file exists immediately
        if not self.progress_file.exists():
            self.save_progress()
    
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
        """Save workflow progress"""
        self.progress['last_run'] = datetime.now().isoformat()
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)
    
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
        scraper = JavaGGScraper(headless=True)
        new_urls = []
        
        try:
            print("Initializing browser driver...")
            # Initialize driver
            scraper._init_driver()
            print("Browser driver ready!")
            
            # Get latest videos from /new-post/ page
            page = self.progress['last_scraped_page']
            max_pages = 10  # Limit to 10 pages per run to avoid timeout
            pages_scraped = 0
            
            # Keep scraping pages until we have enough videos or no more videos
            while pages_scraped < max_pages:
                pages_scraped += 1
                print(f"\n📄 Scraping page {page}... ({pages_scraped}/{max_pages})")
                
                # Navigate to JavaGG new-post page
                base_url = "https://javgg.net/new-post/"
                if page > 1:
                    base_url = f"https://javgg.net/new-post/page/{page}/"
                
                print(f"  Loading: {base_url}")
                scraper.driver.get(base_url)
                
                # Wait for Cloudflare check to complete
                print(f"  Waiting for Cloudflare check...")
                max_wait = 30  # Maximum 30 seconds
                waited = 0
                while waited < max_wait:
                    time.sleep(2)
                    waited += 2
                    
                    # Check if Cloudflare challenge is still showing
                    if "Just a moment" not in scraper.driver.title:
                        print(f"  ✅ Cloudflare check passed after {waited}s")
                        break
                    
                    print(f"  ⏳ Still waiting for Cloudflare... ({waited}s)")
                
                # Additional wait for page to fully load
                time.sleep(3)
                
                # Check if page loaded
                print(f"  Current URL: {scraper.driver.current_url}")
                print(f"  Page title: {scraper.driver.title}")
                
                # Scroll down to trigger lazy loading
                scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Increased wait time for lazy loading
                
                # Scroll again to ensure all content loads
                scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
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
                    break
                
                # All videos on this page were processed, move to next page
                self.progress['last_scraped_page'] = page + 1
                self.save_progress()
                
                # Move to next page
                page += 1
            
            print(f"\n✅ Total found: {len(new_urls)} new videos to process")
            print(f"   Scraped {pages_scraped} pages")
            
        finally:
            scraper.close()
        
        return new_urls
    
    def download_video(self, video_url: str, video_code: str) -> Optional[str]:
        """
        Download video trying multiple methods
        Returns path to downloaded video file
        """
        print(f"\n📥 Downloading video: {video_code}")
        
        scraper = JavaGGScraper(headless=True)
        
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
            
            # Try yt-dlp with stream URL
            print(f"  📥 Attempting download with yt-dlp...")
            cmd = [
                'yt-dlp',
                '-o', str(video_file),
                '--no-warnings',
                '--no-check-certificate',
                '--concurrent-fragments', '16',
                '--retries', '5',
                '--fragment-retries', '5',
                '--quiet',  # Suppress progress output
                '--progress-template', '%(progress.downloaded_bytes)s/%(progress.total_bytes)s',
                download_url
            ]
            
            # Run with progress bar
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
            
            for line in process.stdout:
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
            
            process.wait()
            result_code = process.returncode
            
            if result_code == 0 and video_file.exists() and video_file.stat().st_size > 1024 * 1024:
                print(f"  ✅ Downloaded: {video_file.name} ({video_file.stat().st_size / 1024 / 1024:.1f} MB)")
                
                # Validate the video file
                print(f"  🔍 Validating video file...")
                try:
                    validate_cmd = [
                        'ffprobe', '-v', 'error',
                        '-select_streams', 'v:0',
                        '-show_entries', 'stream=codec_type',
                        '-of', 'default=noprint_wrappers=1:nokey=1',
                        str(video_file)
                    ]
                    validate_result = subprocess.run(validate_cmd, capture_output=True, text=True, timeout=10)
                    
                    if validate_result.returncode == 0 and 'video' in validate_result.stdout:
                        print(f"  ✅ Video file is valid")
                        return str(video_file)
                    else:
                        print(f"  ⚠️ Video file may be corrupted, attempting to fix...")
                        
                        # Try to re-encode the file
                        fixed_file = self.download_dir / f"{video_code}_fixed.mp4"
                        fix_cmd = [
                            'ffmpeg', '-i', str(video_file),
                            '-c', 'copy',
                            '-movflags', '+faststart',
                            '-y',
                            str(fixed_file)
                        ]
                        
                        fix_result = subprocess.run(fix_cmd, capture_output=True, text=True, timeout=300)
                        
                        if fix_result.returncode == 0 and fixed_file.exists():
                            # Replace original with fixed version
                            video_file.unlink()
                            fixed_file.rename(video_file)
                            print(f"  ✅ Video file fixed and validated")
                            return str(video_file)
                        else:
                            print(f"  ⚠️ Could not fix video file, using as-is")
                            return str(video_file)
                            
                except Exception as e:
                    print(f"  ⚠️ Validation error: {str(e)}, using file as-is")
                    return str(video_file)
                
                return str(video_file)
            
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
        finally:
            scraper.close()
    
    def enrich_and_save(self, video_url: str, video_code: str) -> Dict:
        """
        Scrape, enrich and save video metadata
        """
        print(f"\n📊 Enriching metadata: {video_code}")
        
        scraper = JavaGGScraper(headless=True)
        
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
            
        finally:
            scraper.close()
    
    def generate_preview_video(self, video_file: str, video_code: str) -> Optional[str]:
        """
        Generate preview video - REQUIRED step
        """
        print(f"\n🎬 Generating preview: {video_code}")
        
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
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=codec_name,codec_type',
                    '-of', 'json',
                    str(video_file)
                ]
                validate_result = subprocess.run(validate_cmd, capture_output=True, text=True, timeout=10)
                
                if validate_result.returncode != 0:
                    print(f"  ⚠️ Video validation failed - skipping preview")
                    return None
                
                validate_data = json.loads(validate_result.stdout)
                if not validate_data.get('streams') or validate_data['streams'][0].get('codec_type') != 'video':
                    print(f"  ⚠️ File is not a valid video - skipping preview")
                    print(f"     Detected format: {validate_data.get('streams', [{}])[0].get('codec_name', 'unknown')}")
                    return None
                
                print(f"  ✅ Video format validated")
                
            except Exception as e:
                print(f"  ⚠️ Validation error: {str(e)} - skipping preview")
                return None
            
            # Generate 2-minute preview using PreviewGenerator
            print(f"  🎬 Starting preview generation...")
            generator = PreviewGenerator(video_file)
            result = generator.generate_preview(
                output_path=str(preview_file),
                target_duration=120,  # 2 minutes
                clip_duration=2.5,
                resolution="720",
                crf=23,
                fps=30,
                cleanup=True,
                parallel=True,
                max_workers=32
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
        Commit and push database changes to GitHub after each video
        This ensures we don't lose data if workflow times out
        """
        try:
            import subprocess
            
            # Check if running in GitHub Actions
            if not os.getenv('GITHUB_ACTIONS'):
                print(f"  ℹ️ Not in GitHub Actions, skipping git commit")
                return
            
            print(f"\n💾 Committing changes for {video_code}...")
            
            # Add database files
            subprocess.run(['git', 'add', 'database/combined_videos.json'], check=True)
            subprocess.run(['git', 'add', 'database/workflow_progress.json'], check=True)
            subprocess.run(['git', 'add', 'database/stats.json'], check=True, stderr=subprocess.DEVNULL)
            subprocess.run(['git', 'add', 'database/progress_tracking.json'], check=True, stderr=subprocess.DEVNULL)
            
            # Check if there are changes
            result = subprocess.run(['git', 'diff', '--staged', '--quiet'], capture_output=True)
            
            if result.returncode != 0:  # There are changes
                # Commit
                commit_msg = f"Update database: {video_code} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
                
                # Push
                subprocess.run(['git', 'push'], check=True)
                print(f"  ✅ Changes committed and pushed")
            else:
                print(f"  ℹ️ No changes to commit")
                
        except Exception as e:
            print(f"  ⚠️ Git commit failed: {str(e)}")
            # Don't fail the workflow if git commit fails
    
    def process_video(self, video_url: str) -> bool:
        """
        Process a single video through the complete workflow
        """
        video_code = video_url.rstrip('/').split('/')[-1].upper()
        
        print("\n" + "="*70)
        print(f"PROCESSING VIDEO: {video_code}")
        print("="*70)
        
        try:
            # Step 1: Download video
            video_file = self.download_video(video_url, video_code)
            if not video_file:
                self.progress['failed_videos'].append(video_code)
                self.save_progress()
                return False
            
            # Step 2: Enrich and save metadata
            metadata = self.enrich_and_save(video_url, video_code)
            if not metadata:
                self.cleanup_files(video_code)
                self.progress['failed_videos'].append(video_code)
                self.save_progress()
                return False
            
            # Step 3: Generate preview
            preview_file = self.generate_preview_video(video_file, video_code)
            
            # Step 4: Upload videos
            urls = self.upload_videos(video_file, preview_file, video_code)
            
            # Step 5: Update metadata with URLs
            self.update_metadata_with_urls(video_code, urls)
            
            # Step 6: Cleanup files
            self.cleanup_files(video_code)
            
            # Mark as processed
            self.progress['processed_videos'].append(video_code)
            self.save_progress()
            
            # Commit and push changes after each video (important for GitHub Actions)
            self.commit_and_push_changes(video_code)
            
            print(f"\n✅ Successfully processed: {video_code}")
            return True
            
        except Exception as e:
            print(f"\n❌ Error processing {video_code}: {str(e)}")
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


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='JavaGG Complete Workflow')
    parser.add_argument('--max-videos', type=int, default=0, help='Maximum videos to process (0 = unlimited)')
    parser.add_argument('--base-dir', type=str, default=None, help='Base directory')
    
    args = parser.parse_args()
    
    workflow = WorkflowManager(base_dir=args.base_dir)
    workflow.run(max_videos=args.max_videos)
