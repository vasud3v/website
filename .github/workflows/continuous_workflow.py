#!/usr/bin/env python3
"""
Continuous Workflow for GitHub Actions
Orchestrates: Scraping → Downloading → Preview → Enrichment → Upload
- Processes videos SEQUENTIALLY (one by one)
- Downloads use PARALLEL CHUNKS (32 connections per video)
- Runs for specified duration
"""

import os
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "javmix"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "javdatabase"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "upload_pipeline"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools" / "preview_generator"))

# Thread-safe print
print_lock = threading.Lock()

def safe_print(msg):
    """Thread-safe print"""
    with print_lock:
        print(msg)
        sys.stdout.flush()


class ContinuousWorkflow:
    """Orchestrates the complete video processing workflow"""
    
    def __init__(self, max_runtime_minutes=290, max_workers=32, max_videos=0):
        self.max_runtime_minutes = max_runtime_minutes
        self.max_workers = max_workers
        self.max_videos = max_videos
        self.start_time = datetime.now()
        
        # Statistics
        self.stats = {
            'videos_processed': 0,
            'videos_downloaded': 0,
            'videos_enriched': 0,
            'videos_uploaded': 0,
            'previews_created': 0,
            'errors': 0,
            'start_time': self.start_time.isoformat(),
            'runtime_minutes': 0,
            'success_rate': 0
        }
        
        # Paths
        self.database_dir = Path("database")
        self.download_dir = Path("downloaded_files")
        self.combined_db = self.database_dir / "combined_videos.json"
        
        # Create directories
        self.database_dir.mkdir(exist_ok=True)
        self.download_dir.mkdir(exist_ok=True)
    
    def check_runtime(self):
        """Check if we should continue running"""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60
        return elapsed < self.max_runtime_minutes
    
    def load_combined_database(self):
        """Load combined database"""
        if self.combined_db.exists():
            with open(self.combined_db, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle legacy list format
                if isinstance(data, list):
                    return {"videos": data, "stats": {"total_videos": len(data)}}
                return data
        return {"videos": [], "stats": {"total_videos": 0}}
    
    def save_combined_database(self, data):
        """Save combined database"""
        with open(self.combined_db, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_sitemap_urls(self):
        """Load URLs from sitemap"""
        sitemap_file = Path("sitemap_videos.json")
        if sitemap_file.exists():
            with open(sitemap_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('urls', [])
        return []
    
    def get_pending_videos(self):
        """Get videos that need processing from sitemap"""
        # Load sitemap URLs
        sitemap_urls = self.load_sitemap_urls()
        safe_print(f"📋 Loaded {len(sitemap_urls)} URLs from sitemap")
        
        # Load combined database to check what's already processed
        db = self.load_combined_database()
        processed_urls = set()
        
        for video in db.get('videos', []):
            url = video.get('url', '')
            if url:
                processed_urls.add(url)
        
        safe_print(f"✅ Already processed: {len(processed_urls)} videos")
        
        # Find unprocessed URLs
        pending_urls = [url for url in sitemap_urls if url not in processed_urls]
        safe_print(f"📋 Pending: {len(pending_urls)} videos to process")
        
        # Convert URLs to video data format
        pending = []
        for url in pending_urls:
            pending.append({
                'url': url,
                'code': self.extract_code_from_url(url),
                'needs_scraping': True
            })
        
        return pending
    
    def extract_code_from_url(self, url):
        """Extract video code from URL with validation"""
        import re
        match = re.search(r'/(video|fc2ppv|xvideo)/([^/]+)', url)
        if match:
            code = match.group(2).upper()
            # Validate code format (alphanumeric, hyphens, underscores)
            if re.match(r'^[A-Z0-9_-]+$', code):
                return code
            else:
                safe_print(f"⚠️ Invalid code format extracted: {code}")
                return 'unknown'
        return 'unknown'
    
    def sanitize_code_for_filesystem(self, code):
        """Sanitize video code for safe filesystem use"""
        import re
        # Remove or replace unsafe characters
        safe_code = re.sub(r'[<>:"/\\|?*]', '_', code)
        # Limit length to avoid filesystem issues
        safe_code = safe_code[:200]
        # Remove leading/trailing dots and spaces
        safe_code = safe_code.strip('. ')
        return safe_code if safe_code else 'unknown'
    
    def scrape_video(self, video_url):
        """Scrape a single video with timeout"""
        scraped_file = None
        try:
            safe_print(f"🎬 Scraping: {video_url}")
            
            scraped_file = Path('database/scraped_video.json')
            
            result = subprocess.run(
                ['python', 'javmix/javmix_scraper.py', '--url', video_url, '--output', str(scraped_file)],
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes max for scraping
            )
            
            if result.returncode == 0:
                # Load scraped data
                if scraped_file.exists():
                    with open(scraped_file, 'r', encoding='utf-8') as f:
                        video_data = json.load(f)
                    
                    # Validate it's a dict
                    if not isinstance(video_data, dict):
                        safe_print(f"⚠️ Scraper returned invalid data type: {type(video_data).__name__}")
                        return None
                    
                    safe_print(f"✅ Scraped: {video_url}")
                    return video_data
                else:
                    safe_print(f"⚠️ Scraper succeeded but no output file: {video_url}")
            else:
                safe_print(f"❌ Scraper failed with code {result.returncode}: {video_url}")
                if result.stderr:
                    safe_print(f"   Error: {result.stderr[:200]}")
            
            return None
            
        except subprocess.TimeoutExpired:
            safe_print(f"⏰ Scraping timeout (120s): {video_url}")
            return None
        except Exception as e:
            safe_print(f"❌ Error scraping {video_url}: {e}")
            return None
        finally:
            # Cleanup temp file
            if scraped_file and scraped_file.exists():
                try:
                    scraped_file.unlink()
                except Exception as e:
                    safe_print(f"⚠️ Could not cleanup {scraped_file}: {e}")
    
    def download_video(self, video_data):
        """Download video with parallel chunks"""
        try:
            code = video_data.get('code', 'unknown')
            # Sanitize code for filesystem
            safe_code = self.sanitize_code_for_filesystem(code)
            safe_print(f"📥 Downloading: {code}")
            
            # Get best quality URL
            embed_urls = video_data.get('embed_urls', {})
            if not embed_urls:
                safe_print(f"⚠️ No embed URLs for {code}")
                return None
            
            # Validate embed_urls is a dict
            if not isinstance(embed_urls, dict):
                safe_print(f"⚠️ Invalid embed_urls type for {code}: {type(embed_urls).__name__}")
                return None
            
            # Priority: iplayerhls > streamtape > others
            download_url = None
            for host in ['iplayerhls', 'streamtape', 'doodstream']:
                if host in embed_urls:
                    download_url = embed_urls[host]
                    break
            
            if not download_url:
                # Get first available URL, but check if dict is not empty
                if len(embed_urls) > 0:
                    download_url = list(embed_urls.values())[0]
                else:
                    safe_print(f"⚠️ Empty embed_urls dict for {code}")
                    return None
            
            # Download using appropriate downloader
            output_file = self.download_dir / f"{safe_code}.mp4"
            
            safe_print(f"  🔗 URL: {download_url}")
            safe_print(f"  📦 Using {self.max_workers} parallel connections")
            
            # Try aria2c first (supports parallel chunk downloading)
            try:
                result = subprocess.run(
                    [
                        'aria2c',
                        '--max-connection-per-server=16',
                        '--split=16',
                        '--min-split-size=1M',
                        '--max-concurrent-downloads=1',
                        '--continue=true',
                        '--max-tries=5',
                        '--retry-wait=3',
                        '--timeout=60',
                        '--connect-timeout=30',
                        '--allow-overwrite=true',
                        '--auto-file-renaming=false',
                        '--console-log-level=warn',
                        '-o', str(output_file),
                        download_url
                    ],
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes max
                )
                
                if result.returncode == 0 and output_file.exists():
                    safe_print(f"✅ Downloaded with aria2c: {code} ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
                    return str(output_file)
            except FileNotFoundError:
                safe_print(f"  ⚠️ aria2c not found, falling back to yt-dlp")
            except Exception as e:
                safe_print(f"  ⚠️ aria2c failed: {e}, falling back to yt-dlp")
            
            # Fallback to yt-dlp with concurrent fragments
            result = subprocess.run(
                [
                    'yt-dlp',
                    '--concurrent-fragments', str(min(self.max_workers, 16)),
                    '--retries', '10',
                    '--fragment-retries', '10',
                    '--no-part',
                    '-o', str(output_file),
                    download_url
                ],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes max
            )
            
            if result.returncode == 0 and output_file.exists():
                safe_print(f"✅ Downloaded with yt-dlp: {code} ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
                return str(output_file)
            else:
                safe_print(f"❌ Failed to download: {code}")
                return None
                
        except Exception as e:
            safe_print(f"❌ Error downloading {code}: {e}")
            return None
    
    def create_preview(self, video_path):
        """Create preview video"""
        try:
            code = Path(video_path).stem
            safe_print(f"🎞️ Creating preview: {code}")
            
            result = subprocess.run(
                [
                    'python', 'tools/preview_generator/preview_generator.py',
                    video_path,
                    '--workers', str(self.max_workers),
                    '--resolution', '720',
                    '--crf', '23'
                ],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )
            
            if result.returncode == 0:
                preview_path = video_path.replace('.mp4', '_preview.mp4')
                if os.path.exists(preview_path):
                    safe_print(f"✅ Preview created: {code}")
                    return preview_path
            
            safe_print(f"⚠️ Preview creation failed: {code}")
            return None
            
        except Exception as e:
            safe_print(f"❌ Error creating preview {code}: {e}")
            return None
    
    def upload_preview_to_ia(self, preview_path, video_data):
        """Upload preview to Internet Archive"""
        try:
            code = video_data.get('code', 'unknown')
            safe_print(f"📤 Uploading preview to Internet Archive: {code}")
            
            # Import Internet Archive uploader
            sys.path.insert(0, 'upload_pipeline')
            from internet_archive_uploader import InternetArchiveUploader, save_to_database
            
            # Initialize uploader
            uploader = InternetArchiveUploader()
            
            # Prepare metadata
            metadata = {
                'title': video_data.get('title', ''),
                'actors': video_data.get('actors', []),
                'studio': video_data.get('studio', ''),
                'release_date': video_data.get('release_date', '')
            }
            
            # Upload
            result = uploader.upload_preview(preview_path, code, metadata=metadata)
            
            if result.get('success'):
                # Save to database
                save_to_database(code, result)
                
                safe_print(f"✅ Preview uploaded to IA: {code}")
                safe_print(f"   Direct MP4: {result['direct_mp4_link']}")
                return result
            else:
                safe_print(f"❌ IA upload failed: {code}")
                return None
                
        except Exception as e:
            safe_print(f"❌ Error uploading preview to IA {code}: {e}")
            return None
    
    def enrich_metadata(self, video_data):
        """Enrich with JAVDatabase metadata"""
        try:
            code = video_data.get('code', 'unknown')
            safe_print(f"📚 Enriching: {code}")
            
            # Import javdb integration
            from javdb_integration import enrich_with_javdb
            
            success = enrich_with_javdb(video_data, headless=True)
            
            if success:
                safe_print(f"✅ Enriched: {code}")
                return True
            else:
                safe_print(f"⚠️ Enrichment failed: {code}")
                return False
                
        except Exception as e:
            safe_print(f"❌ Error enriching {code}: {e}")
            return False
    
    def upload_video(self, video_path, video_data):
        """Upload video to all hosts"""
        try:
            code = video_data.get('code', 'unknown')
            title = video_data.get('title', code)
            safe_print(f"📤 Uploading: {code}")
            
            # Import uploader
            sys.path.insert(0, 'upload_pipeline')
            from upload_to_all_hosts import MultiHostUploader
            
            uploader = MultiHostUploader()
            results = uploader.upload_to_all(video_path, title, max_workers=5)
            
            # Collect successful uploads
            uploaded_hosts = {}
            for host, result in results.items():
                if result.get('success'):
                    uploaded_hosts[host] = result.get('result', {})
            
            if uploaded_hosts:
                safe_print(f"✅ Uploaded to {len(uploaded_hosts)} hosts: {code}")
                return uploaded_hosts
            else:
                safe_print(f"❌ Upload failed: {code}")
                return {}
                
        except Exception as e:
            safe_print(f"❌ Error uploading {code}: {e}")
            return {}
    
    def process_single_video(self, video_data):
        """Process a single video through the complete workflow"""
        url = video_data.get('url', '')
        code = video_data.get('code', 'unknown')
        
        try:
            safe_print(f"\n{'='*70}")
            safe_print(f"🎯 Processing: {code}")
            safe_print(f"{'='*70}")
            
            # Step 0: Scrape if needed
            if video_data.get('needs_scraping', False):
                scraped_data = self.scrape_video(url)
                if not scraped_data:
                    safe_print(f"⚠️ Skipping {code} - scraping failed")
                    self.stats['errors'] += 1
                    return False
                
                # Validate scraped data is a dict
                if not isinstance(scraped_data, dict):
                    safe_print(f"⚠️ Skipping {code} - scraped data is not a dict (got {type(scraped_data).__name__})")
                    self.stats['errors'] += 1
                    return False
                
                video_data = scraped_data
                code = video_data.get('code', code)  # Update code from scraped data
            
            # Step 1: Download
            video_path = self.download_video(video_data)
            if not video_path:
                safe_print(f"⚠️ Skipping {code} - download failed")
                self.stats['errors'] += 1
                return False
            
            self.stats['videos_downloaded'] += 1
            
            # Step 2: Create Preview
            preview_path = self.create_preview(video_path)
            ia_result = None
            if preview_path:
                self.stats['previews_created'] += 1
                
                # Step 2.5: Upload Preview to Internet Archive
                ia_result = self.upload_preview_to_ia(preview_path, video_data)
            
            # Step 3: Enrich Metadata
            enriched = self.enrich_metadata(video_data)
            if enriched:
                self.stats['videos_enriched'] += 1
            
            # Step 4: Upload to all hosts
            uploaded_hosts = self.upload_video(video_path, video_data)
            if uploaded_hosts:
                self.stats['videos_uploaded'] += 1
            
            # Step 5: Update combined database
            db = self.load_combined_database()
            
            # Add or update video
            video_entry = {
                'url': url,
                'code': code,
                **video_data,
                'downloaded': True,
                'download_path': video_path,
                'preview_path': preview_path,
                'enriched': enriched,
                'uploaded_hosts': uploaded_hosts,
                'processed_at': datetime.now().isoformat()
            }
            
            # Add Internet Archive preview info
            if ia_result:
                video_entry['preview_ia'] = {
                    'identifier': ia_result.get('identifier'),
                    'direct_mp4_link': ia_result.get('direct_mp4_link'),
                    'player_link': ia_result.get('player_link'),
                    'embed_code': ia_result.get('embed_code'),
                    'uploaded_at': ia_result.get('uploaded_at')
                }
            
            # Check if video already exists
            found = False
            for i, v in enumerate(db['videos']):
                if v.get('url') == url or v.get('code') == code:
                    db['videos'][i] = video_entry
                    found = True
                    break
            
            if not found:
                db['videos'].append(video_entry)
            
            # Update stats
            db['stats']['total_videos'] = len(db['videos'])
            
            self.save_combined_database(db)
            
            # Cleanup downloaded file to save space
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                    safe_print(f"🗑️ Cleaned up: {video_path}")
            except:
                pass
            
            self.stats['videos_processed'] += 1
            safe_print(f"✅ Completed: {code}")
            return True
            
        except Exception as e:
            safe_print(f"❌ Error processing {code}: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
            return False
    
    def run(self):
        """Main workflow execution"""
        safe_print("="*70)
        safe_print("🚀 CONTINUOUS WORKFLOW STARTED")
        safe_print("="*70)
        safe_print(f"Max Runtime: {self.max_runtime_minutes} minutes")
        safe_print(f"Max Workers (for downloads): {self.max_workers}")
        safe_print(f"Max Videos: {self.max_videos or 'Unlimited'}")
        safe_print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        safe_print(f"Processing Mode: Sequential (one video at a time)")
        safe_print("="*70)
        
        try:
            # Get pending videos
            pending = self.get_pending_videos()
            safe_print(f"\n📋 Found {len(pending)} videos to process")
            
            if self.max_videos > 0:
                pending = pending[:self.max_videos]
                safe_print(f"📋 Limited to {len(pending)} videos")
            
            # Process videos SEQUENTIALLY (one by one)
            for i, video in enumerate(pending, 1):
                if not self.check_runtime():
                    safe_print("\n⏰ Runtime limit reached, stopping...")
                    break
                
                safe_print(f"\n{'='*70}")
                safe_print(f"📹 Video {i}/{len(pending)}")
                safe_print(f"{'='*70}")
                
                # Process single video (downloads will use parallel chunks internally)
                self.process_single_video(video)
            
        except KeyboardInterrupt:
            safe_print("\n⚠️ Interrupted by user")
        except Exception as e:
            safe_print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Calculate final stats
            elapsed = (datetime.now() - self.start_time).total_seconds() / 60
            self.stats['runtime_minutes'] = round(elapsed, 2)
            
            if self.stats['videos_processed'] > 0:
                success = self.stats['videos_processed'] - self.stats['errors']
                self.stats['success_rate'] = round((success / self.stats['videos_processed']) * 100, 1)
            
            # Save stats
            with open('workflow_stats.json', 'w') as f:
                json.dump(self.stats, f, indent=2)
            
            # Print summary
            safe_print("\n" + "="*70)
            safe_print("📊 WORKFLOW SUMMARY")
            safe_print("="*70)
            safe_print(f"Runtime: {self.stats['runtime_minutes']:.1f} minutes")
            safe_print(f"Videos Processed: {self.stats['videos_processed']}")
            safe_print(f"Videos Downloaded: {self.stats['videos_downloaded']}")
            safe_print(f"Previews Created: {self.stats['previews_created']}")
            safe_print(f"Videos Enriched: {self.stats['videos_enriched']}")
            safe_print(f"Videos Uploaded: {self.stats['videos_uploaded']}")
            safe_print(f"Errors: {self.stats['errors']}")
            safe_print(f"Success Rate: {self.stats['success_rate']:.1f}%")
            safe_print("="*70)


def main():
    parser = argparse.ArgumentParser(description='Continuous Video Processing Workflow')
    parser.add_argument('--max-runtime', type=int, default=290,
                       help='Max runtime in minutes (default: 290)')
    parser.add_argument('--workers', type=int, default=32,
                       help='Number of parallel workers (default: 32)')
    parser.add_argument('--max-videos', type=int, default=0,
                       help='Max videos to process (default: 0 = unlimited)')
    
    args = parser.parse_args()
    
    workflow = ContinuousWorkflow(
        max_runtime_minutes=args.max_runtime,
        max_workers=args.workers,
        max_videos=args.max_videos
    )
    
    workflow.run()


if __name__ == "__main__":
    main()
