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
from preview_generator import generate_preview

# Import upload pipeline
sys.path.insert(0, str(Path(__file__).parent.parent / 'upload_pipeline'))
from upload_to_all_hosts import upload_to_all_hosts
from internet_archive_uploader import upload_to_internet_archive


class WorkflowManager:
    """Manages the complete workflow"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.download_dir = self.base_dir / 'downloaded_files'
        self.database_dir = self.base_dir / 'database'
        self.db_manager = DatabaseManager(str(self.database_dir))
        
        # Create directories
        self.download_dir.mkdir(exist_ok=True)
        self.database_dir.mkdir(exist_ok=True)
        
        # Progress tracking
        self.progress_file = self.database_dir / 'workflow_progress.json'
        self.load_progress()
    
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
    
    def scrape_new_videos(self, max_videos: int = 10) -> List[str]:
        """
        Scrape new video URLs from JavaGG
        Returns list of video URLs
        """
        print("\n" + "="*70)
        print("STEP 1: SCRAPING NEW VIDEOS FROM JAVGG")
        print("="*70)
        
        scraper = JavaGGScraper(headless=True)
        new_urls = []
        
        try:
            # Get latest videos from homepage
            page = self.progress['last_scraped_page']
            print(f"\n📄 Scraping page {page}...")
            
            # Navigate to JavaGG homepage or specific page
            base_url = "https://javgg.net"
            if page > 1:
                base_url = f"https://javgg.net/page/{page}/"
            
            scraper.driver.get(base_url)
            time.sleep(3)
            
            # Find all video links
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(scraper.driver.page_source, 'html.parser')
            
            video_links = soup.find_all('a', href=lambda x: x and '/jav/' in x)
            
            for link in video_links:
                url = link.get('href')
                if url and url.startswith('http'):
                    # Extract video code
                    code = url.rstrip('/').split('/')[-1].upper()
                    
                    # Skip if already processed
                    if code in self.progress['processed_videos']:
                        continue
                    
                    # Skip if in failed list (unless retry time passed)
                    if code in self.progress['failed_videos']:
                        continue
                    
                    new_urls.append(url)
                    
                    if len(new_urls) >= max_videos:
                        break
            
            print(f"\n✅ Found {len(new_urls)} new videos to process")
            
        finally:
            scraper.close()
        
        return new_urls
    
    def download_video(self, video_url: str, video_code: str) -> Optional[str]:
        """
        Download video trying multiple servers
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
            
            # Try to download using m3u8 or embed URL
            video_file = self.download_dir / f"{video_code}.mp4"
            
            # Use yt-dlp to download
            import subprocess
            
            download_url = video_data.m3u8_url or video_data.embed_url
            
            print(f"  🔗 Download URL: {download_url[:60]}...")
            
            cmd = [
                'yt-dlp',
                '-o', str(video_file),
                '--no-warnings',
                '--quiet',
                download_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and video_file.exists():
                print(f"  ✅ Downloaded: {video_file.name} ({video_file.stat().st_size / 1024 / 1024:.1f} MB)")
                return str(video_file)
            else:
                print(f"  ❌ Download failed: {result.stderr}")
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
            enriched_data = enrich_with_javdb(video_dict, headless=True, fetch_actress_details=True)
            
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
        Generate preview video
        """
        print(f"\n🎬 Generating preview: {video_code}")
        
        try:
            preview_file = self.download_dir / f"{video_code}_preview.mp4"
            
            # Generate 2-minute preview
            success = generate_preview(
                input_video=video_file,
                output_video=str(preview_file),
                duration=120,  # 2 minutes
                num_clips=6
            )
            
            if success and preview_file.exists():
                print(f"  ✅ Preview generated: {preview_file.name}")
                return str(preview_file)
            else:
                print(f"  ❌ Preview generation failed")
                return None
                
        except Exception as e:
            print(f"  ❌ Error generating preview: {str(e)}")
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
            hosting_urls = upload_to_all_hosts(video_file, video_code)
            urls['hosting'] = hosting_urls
            
            # Upload preview to Internet Archive
            if preview_file:
                print(f"\n  📤 Uploading preview to Internet Archive...")
                ia_url = upload_to_internet_archive(preview_file, video_code)
                urls['internet_archive'] = ia_url
            
            print(f"\n  ✅ Uploads complete")
            print(f"     - Hosting sites: {len(hosting_urls)} URLs")
            if preview_file:
                print(f"     - Internet Archive: {ia_url}")
            
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
    
    def run(self, max_videos: int = 10):
        """
        Run the complete workflow
        """
        print("\n" + "="*70)
        print("JAVGG COMPLETE WORKFLOW")
        print("="*70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Retry pending enrichments first
        if self.progress['pending_enrichment']:
            self.retry_pending_enrichments()
        
        # Scrape new videos
        video_urls = self.scrape_new_videos(max_videos)
        
        if not video_urls:
            print("\n✅ No new videos to process")
            return
        
        # Process each video
        success_count = 0
        for i, url in enumerate(video_urls, 1):
            print(f"\n{'='*70}")
            print(f"VIDEO {i}/{len(video_urls)}")
            print(f"{'='*70}")
            
            if self.process_video(url):
                success_count += 1
        
        # Summary
        print("\n" + "="*70)
        print("WORKFLOW COMPLETE")
        print("="*70)
        print(f"✅ Successfully processed: {success_count}/{len(video_urls)}")
        print(f"❌ Failed: {len(video_urls) - success_count}")
        print(f"⏳ Pending enrichment: {len(self.progress['pending_enrichment'])}")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='JavaGG Complete Workflow')
    parser.add_argument('--max-videos', type=int, default=10, help='Maximum videos to process')
    parser.add_argument('--base-dir', type=str, default=None, help='Base directory')
    
    args = parser.parse_args()
    
    workflow = WorkflowManager(base_dir=args.base_dir)
    workflow.run(max_videos=args.max_videos)
