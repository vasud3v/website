#!/usr/bin/env python3
"""
Continuous Workflow for GitHub Actions
Orchestrates: Scraping → Downloading → Preview → Enrichment → Upload
Runs for specified duration with 32 parallel workers
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
                return json.load(f)
        return {"videos": [], "stats": {"total_videos": 0}}
    
    def save_combined_database(self, data):
        """Save combined database"""
        with open(self.combined_db, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_pending_videos(self):
        """Get videos that need processing"""
        db = self.load_combined_database()
        
        # Find videos without download or upload info
        pending = []
        for video in db.get('videos', []):
            # Check if video needs processing
            needs_download = not video.get('downloaded', False)
            needs_upload = not video.get('uploaded_hosts', {})
            
            if needs_download or needs_upload:
                pending.append(video)
        
        return pending
    
    def scrape_video(self, video_url):
        """Scrape a single video"""
        try:
            safe_print(f"🎬 Scraping: {video_url}")
            
            result = subprocess.run(
                ['python', 'javmix/javmix_scraper.py', '--url', video_url],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                safe_print(f"✅ Scraped: {video_url}")
                return True
            else:
                safe_print(f"❌ Failed to scrape: {video_url}")
                return False
        except Exception as e:
            safe_print(f"❌ Error scraping {video_url}: {e}")
            return False
    
    def download_video(self, video_data):
        """Download video with best quality"""
        try:
            code = video_data.get('code', 'unknown')
            safe_print(f"📥 Downloading: {code}")
            
            # Get best quality URL
            embed_urls = video_data.get('embed_urls', {})
            if not embed_urls:
                safe_print(f"⚠️ No embed URLs for {code}")
                return None
            
            # Priority: iplayerhls > streamtape > others
            download_url = None
            for host in ['iplayerhls', 'streamtape', 'doodstream']:
                if host in embed_urls:
                    download_url = embed_urls[host]
                    break
            
            if not download_url:
                download_url = list(embed_urls.values())[0]
            
            # Download using appropriate downloader
            output_file = self.download_dir / f"{code}.mp4"
            
            # Use yt-dlp or custom downloader
            result = subprocess.run(
                ['yt-dlp', '-o', str(output_file), download_url],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes max
            )
            
            if result.returncode == 0 and output_file.exists():
                safe_print(f"✅ Downloaded: {code} ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
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
        code = video_data.get('code', 'unknown')
        
        try:
            safe_print(f"\n{'='*70}")
            safe_print(f"🎯 Processing: {code}")
            safe_print(f"{'='*70}")
            
            # Step 1: Download
            video_path = self.download_video(video_data)
            if not video_path:
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
            
            # Find and update video
            for i, v in enumerate(db['videos']):
                if v.get('code') == code:
                    db['videos'][i]['downloaded'] = True
                    db['videos'][i]['download_path'] = video_path
                    db['videos'][i]['preview_path'] = preview_path
                    db['videos'][i]['enriched'] = enriched
                    db['videos'][i]['uploaded_hosts'] = uploaded_hosts
                    db['videos'][i]['processed_at'] = datetime.now().isoformat()
                    
                    # Add Internet Archive preview info
                    if ia_result:
                        db['videos'][i]['preview_ia'] = {
                            'identifier': ia_result.get('identifier'),
                            'direct_mp4_link': ia_result.get('direct_mp4_link'),
                            'player_link': ia_result.get('player_link'),
                            'embed_code': ia_result.get('embed_code'),
                            'uploaded_at': ia_result.get('uploaded_at')
                        }
                    break
            
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
            self.stats['errors'] += 1
            return False
    
    def run(self):
        """Main workflow execution"""
        safe_print("="*70)
        safe_print("🚀 CONTINUOUS WORKFLOW STARTED")
        safe_print("="*70)
        safe_print(f"Max Runtime: {self.max_runtime_minutes} minutes")
        safe_print(f"Max Workers: {self.max_workers}")
        safe_print(f"Max Videos: {self.max_videos or 'Unlimited'}")
        safe_print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        safe_print("="*70)
        
        try:
            # Get pending videos
            pending = self.get_pending_videos()
            safe_print(f"\n📋 Found {len(pending)} videos to process")
            
            if self.max_videos > 0:
                pending = pending[:self.max_videos]
                safe_print(f"📋 Limited to {len(pending)} videos")
            
            # Process videos with parallel workers
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for video in pending:
                    if not self.check_runtime():
                        safe_print("\n⏰ Runtime limit reached, stopping...")
                        break
                    
                    future = executor.submit(self.process_single_video, video)
                    futures.append(future)
                    
                    # Limit concurrent tasks
                    if len(futures) >= self.max_workers:
                        # Wait for at least one to complete
                        done, futures = futures[:1], futures[1:]
                        for f in done:
                            f.result()
                
                # Wait for remaining tasks
                for future in as_completed(futures):
                    if not self.check_runtime():
                        safe_print("\n⏰ Runtime limit reached, cancelling remaining tasks...")
                        break
                    future.result()
            
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
