"""
Integrated pipeline to be called from Jable scraper
Handles JAVDatabase scraping + merging + saving for single video
Uses centralized database manager in root/database folder
Includes smart retry system for videos not found in JAVDatabase
"""

import json
import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))
sys.path.insert(0, str(Path(__file__).parent))

# Import centralized database manager
try:
    from database_manager import db_manager
    DATABASE_MANAGER_AVAILABLE = True
except ImportError:
    DATABASE_MANAGER_AVAILABLE = False
    print("⚠️ Database manager not available, using legacy database handling")

# Import retry manager
try:
    from retry_manager import retry_manager
    RETRY_MANAGER_AVAILABLE = True
except ImportError:
    RETRY_MANAGER_AVAILABLE = False
    print("⚠️ Retry manager not available")

from scrape_single import scrape_single_video
from merge_single import merge_and_validate


class IntegratedPipeline:
    """Integrated pipeline for processing single video"""
    
    def __init__(self, combined_db_path: str = None):
        """Initialize pipeline with centralized database path"""
        if combined_db_path is None:
            # Use absolute path to project root database
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            combined_db_path = str(project_root / "database" / "combined_videos.json")
        
        self.combined_db_path = combined_db_path
        self.use_db_manager = DATABASE_MANAGER_AVAILABLE
        
        if not self.use_db_manager:
            # Legacy: Ensure directories exist
            Path(self.combined_db_path).parent.mkdir(parents=True, exist_ok=True)
        else:
            print("✓ Using centralized database manager")
    
    def load_combined_database(self) -> list:
        """Load existing combined database"""
        if self.use_db_manager:
            return db_manager.get_all_videos()
        
        # Legacy fallback
        try:
            if os.path.exists(self.combined_db_path):
                with open(self.combined_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data.get('videos', [])
                    if isinstance(data, list):
                        return data
            return []
        except Exception as e:
            print(f"⚠️ Error loading database: {e}")
            return []
    
    def save_combined_database(self, data: list) -> bool:
        """Save combined database"""
        if self.use_db_manager:
            # With database manager, we save individual videos
            # This method is not used directly
            return True
        
        # Legacy fallback
        try:
            temp_path = f"{self.combined_db_path}.tmp"
            
            # Prepare new data structure
            new_data = {
                'videos': data,
                'stats': {
                    'total_videos': len(data),
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
            
            if os.path.exists(self.combined_db_path):
                backup_path = f"{self.combined_db_path}.bak"
                shutil.copy(self.combined_db_path, backup_path)
            
            shutil.move(temp_path, self.combined_db_path)
            return True
        except Exception as e:
            print(f"❌ Error saving database: {e}")
            return False
    
    def is_already_processed(self, video_code: str) -> bool:
        """Check if video already has JAVDatabase data"""
        if self.use_db_manager:
            video = db_manager.get_video_by_code(video_code)
            if video:
                # Only skip if it has JAVDatabase data already
                # This allows enrichment of videos that only have Jable data
                has_javdb = video.get('javdb_available', False) or video.get('javdb_data') is not None
                if has_javdb:
                    print(f"   Video {video_code} already has JAVDatabase data, skipping")
                    return True
                else:
                    print(f"   Video {video_code} exists but missing JAVDatabase data, will enrich")
                    return False
            return False
        
        # Legacy fallback
        existing = self.load_combined_database()
        for v in existing:
            if v.get("code") == video_code.upper():
                # Only skip if it has JAVDatabase data
                has_javdb = v.get('javdb_available', False) or v.get('javdb_data') is not None
                if has_javdb:
                    print(f"   Video {video_code} already has JAVDatabase data, skipping")
                    return True
                else:
                    print(f"   Video {video_code} exists but missing JAVDatabase data, will enrich")
                    return False
        return False
    
    def log_error(self, video_code: str, error: str, error_type: str = "unknown"):
        """Log error"""
        if self.use_db_manager:
            db_manager.mark_as_failed(code=video_code, error=error)
        else:
            # Legacy error logging
            print(f"❌ Error for {video_code}: {error}")
    
    def update_stats(self, success: bool, javdb_available: bool):
        """Update processing statistics"""
        if self.use_db_manager:
            db_manager.update_stats()
            db_manager.update_progress()
    
    def should_skip_javdb_enrichment(self, video_code: str) -> tuple[bool, str]:
        """
        Check if video should skip JAVDatabase enrichment
        
        Returns:
            tuple: (should_skip, reason)
        """
        video_code_upper = video_code.upper()
        
        # FC2PPV videos are not on JAVDatabase (amateur/independent content)
        if video_code_upper.startswith('FC2') or 'FC2PPV' in video_code_upper or 'FC2-PPV' in video_code_upper:
            return (True, "FC2PPV videos are not indexed on JAVDatabase (amateur content)")
        
        # Add other patterns that are not on JAVDatabase
        # Example: Some amateur codes, personal uploads, etc.
        amateur_patterns = ['AMATEUR', 'PERSONAL', 'PRIVATE']
        for pattern in amateur_patterns:
            if pattern in video_code_upper:
                return (True, f"Amateur/personal content not on JAVDatabase")
        
        return (False, "")
    
    def process_video(self, jable_data: dict, headless: bool = True) -> Optional[dict]:
        """
        Process single video: scrape JAVDatabase + merge + save
        
        Args:
            jable_data: Video data from Jable scraper
            headless: Run browser in headless mode
        
        Returns:
            dict: Merged video data or None if failed
        """
        video_code = jable_data.get("code", "").upper()
        
        if not video_code:
            print("❌ No video code provided")
            return None
        
        print(f"\n{'='*70}")
        print(f"🎬 Processing: {video_code}")
        print(f"{'='*70}")
        
        # Check if this video type should skip JAVDatabase enrichment
        should_skip, skip_reason = self.should_skip_javdb_enrichment(video_code)
        if should_skip:
            print(f"⏭️  Skipping JAVDatabase enrichment: {skip_reason}")
            print(f"   Will save Javmix data only...")
            
            # Save Javmix data without JAVDatabase enrichment
            try:
                # Add metadata to indicate no JAVDatabase data
                jable_data['javdb_available'] = False
                jable_data['javdb_skip_reason'] = skip_reason
                
                if self.use_db_manager:
                    if db_manager.add_or_update_video(jable_data):
                        print(f"  ✅ Saved Javmix data to database")
                        all_videos = db_manager.get_all_videos()
                        print(f"     Total videos in database: {len(all_videos)}")
                        self.update_stats(success=True, javdb_available=False)
                        
                        print(f"\n{'='*70}")
                        print(f"✅ {video_code} processed successfully!")
                        print(f"   JAVDatabase: ⏭️  Skipped ({skip_reason})")
                        print(f"{'='*70}\n")
                        
                        return jable_data
                    else:
                        print(f"  ❌ Failed to save database")
                        return None
                else:
                    # Legacy save
                    existing = self.load_combined_database()
                    existing = [v for v in existing if v.get("code") != video_code]
                    existing.append(jable_data)
                    
                    if self.save_combined_database(existing):
                        print(f"  ✅ Saved to {self.combined_db_path}")
                        print(f"     Total videos in database: {len(existing)}")
                        self.update_stats(success=True, javdb_available=False)
                        
                        print(f"\n{'='*70}")
                        print(f"✅ {video_code} processed successfully!")
                        print(f"   JAVDatabase: ⏭️  Skipped ({skip_reason})")
                        print(f"{'='*70}\n")
                        
                        return jable_data
                    else:
                        print(f"  ❌ Failed to save database")
                        return None
            except Exception as e:
                print(f"  ❌ Save failed: {e}")
                self.log_error(video_code, str(e), "save_error")
                return None
        
        # Check if already processed
        if self.is_already_processed(video_code):
            print(f"⏭️  {video_code} already in combined database, skipping...")
            return None
        
        # Step 1: Scrape JAVDatabase
        print(f"\n📊 Step 1: Fetching metadata from JAVDatabase...")
        javdb_data = None
        
        try:
            javdb_data = scrape_single_video(video_code, headless=headless)
            
            if javdb_data:
                print(f"  ✅ JAVDatabase data retrieved")
                print(f"     - Screenshots: {len(javdb_data.get('screenshots', []))}")
                print(f"     - Cast: {len(javdb_data.get('cast', []))}")
                print(f"     - Genres: {len(javdb_data.get('genres', []))}")
            else:
                print(f"  ⚠️  Video not found on JAVDatabase")
                print(f"     This is normal for new releases (usually indexed within 2-7 days)")
                print(f"     Will use Jable data only and retry later")
                
                # Add to retry queue for automatic retry after 2 days
                if RETRY_MANAGER_AVAILABLE:
                    print(f"\n📋 Adding to retry queue...")
                    retry_manager.add_to_queue(video_code, jable_data, reason="not_found_in_javdb")
                    
                    # Show queue stats
                    stats = retry_manager.get_queue_stats()
                    print(f"   Retry queue: {stats['total']} videos ({stats['ready_for_retry']} ready, {stats['pending']} pending)")
                
        except Exception as e:
            print(f"  ❌ JAVDatabase scraping failed: {e}")
            print(f"     Will use Jable data only")
            self.log_error(video_code, str(e), "javdb_scrape_error")
        
        # Step 2: Merge data
        print(f"\n🔗 Step 2: Merging data...")
        try:
            merged_data = merge_and_validate(jable_data, javdb_data)
            print(f"  ✅ Data merged successfully")
            
            # Show what was merged
            if javdb_data:
                print(f"     - JAVDatabase: ✅ Available")
                print(f"     - Cast: {len(merged_data.get('cast', []))} actresses")
                print(f"     - Screenshots: {len(merged_data.get('screenshots', []))}")
            else:
                print(f"     - JAVDatabase: ⚠️  Not available (Jable data only)")
            
            if merged_data.get('hosting'):
                print(f"     - Hosting: {', '.join(merged_data['hosting'].keys())}")
            else:
                print(f"     - Hosting: ⚠️  Not available yet")
            
        except Exception as e:
            print(f"  ❌ Merge failed: {e}")
            self.log_error(video_code, str(e), "merge_error")
            self.update_stats(success=False, javdb_available=bool(javdb_data))
            return None
        
        # Step 3: Save to combined database
        print(f"\n💾 Step 3: Saving to combined database...")
        try:
            if self.use_db_manager:
                # Use database manager to add or update
                if db_manager.add_or_update_video(merged_data):
                    print(f"  ✅ Saved to centralized database")
                    all_videos = db_manager.get_all_videos()
                    print(f"     Total videos in database: {len(all_videos)}")
                    self.update_stats(success=True, javdb_available=bool(javdb_data))
                else:
                    print(f"  ❌ Failed to save database")
                    self.log_error(video_code, "Failed to save database", "save_error")
                    return None
            else:
                # Legacy: Load, update, save
                existing = self.load_combined_database()
                
                # Remove if exists
                existing = [v for v in existing if v.get("code") != video_code]
                
                # Add new video
                existing.append(merged_data)
                
                # Save
                if self.save_combined_database(existing):
                    print(f"  ✅ Saved to {self.combined_db_path}")
                    print(f"     Total videos in database: {len(existing)}")
                    self.update_stats(success=True, javdb_available=bool(javdb_data))
                else:
                    print(f"  ❌ Failed to save database")
                    self.log_error(video_code, "Failed to save database", "save_error")
                    return None
                
        except Exception as e:
            print(f"  ❌ Save failed: {e}")
            self.log_error(video_code, str(e), "save_error")
            self.update_stats(success=False, javdb_available=bool(javdb_data))
            return None
        
        # Success!
        print(f"\n{'='*70}")
        print(f"✅ {video_code} processed successfully!")
        print(f"   JAVDatabase: {'✅ Available' if javdb_data else '⚠️  Not available'}")
        
        # If JAVDatabase data was found, remove from retry queue
        if javdb_data and RETRY_MANAGER_AVAILABLE:
            retry_manager.remove_from_queue(video_code)
        
        print(f"{'='*70}\n")
        
        return merged_data
    
    def process_retry_queue(self, max_videos: int = 10, headless: bool = True) -> dict:
        """
        Process videos from retry queue that are ready for retry
        
        Args:
            max_videos: Maximum number of videos to retry in this run
            headless: Run browser in headless mode
        
        Returns:
            dict: Statistics about retry processing
        """
        if not RETRY_MANAGER_AVAILABLE:
            print("⚠️ Retry manager not available")
            return {'processed': 0, 'success': 0, 'failed': 0}
        
        print(f"\n{'='*70}")
        print(f"🔄 PROCESSING JAVDATABASE RETRY QUEUE")
        print(f"{'='*70}")
        
        # Get videos ready for retry
        ready_videos = retry_manager.get_videos_ready_for_retry()
        
        if not ready_videos:
            print("   No videos ready for retry")
            return {'processed': 0, 'success': 0, 'failed': 0}
        
        print(f"   Found {len(ready_videos)} videos ready for retry")
        print(f"   Processing up to {max_videos} videos...")
        
        processed = 0
        success = 0
        failed = 0
        
        for item in ready_videos[:max_videos]:
            video_code = item.get('code')
            video_data = item.get('video_data', {})
            retry_count = item.get('retry_count', 0)
            
            print(f"\n{'─'*70}")
            print(f"🔄 Retry {retry_count + 1}/{retry_manager.max_retries}: {video_code}")
            print(f"{'─'*70}")
            
            try:
                # Try to scrape JAVDatabase again
                javdb_data = scrape_single_video(video_code, headless=headless)
                
                if javdb_data:
                    print(f"  ✅ JAVDatabase data found!")
                    
                    # Merge and save
                    merged_data = merge_and_validate(video_data, javdb_data)
                    
                    if self.use_db_manager:
                        if db_manager.add_or_update_video(merged_data):
                            print(f"  ✅ Updated database with JAVDatabase data")
                            retry_manager.update_retry_status(video_code, success=True, found_in_javdb=True)
                            success += 1
                        else:
                            print(f"  ❌ Failed to update database")
                            retry_manager.update_retry_status(video_code, success=False, found_in_javdb=True)
                            failed += 1
                    else:
                        # Legacy save
                        existing = self.load_combined_database()
                        existing = [v for v in existing if v.get("code") != video_code]
                        existing.append(merged_data)
                        
                        if self.save_combined_database(existing):
                            print(f"  ✅ Updated database with JAVDatabase data")
                            retry_manager.update_retry_status(video_code, success=True, found_in_javdb=True)
                            success += 1
                        else:
                            print(f"  ❌ Failed to update database")
                            retry_manager.update_retry_status(video_code, success=False, found_in_javdb=True)
                            failed += 1
                else:
                    print(f"  ⚠️  Still not found in JAVDatabase")
                    retry_manager.update_retry_status(video_code, success=False, found_in_javdb=False)
                    failed += 1
                
            except Exception as e:
                print(f"  ❌ Retry failed: {e}")
                retry_manager.update_retry_status(video_code, success=False, found_in_javdb=False)
                failed += 1
            
            processed += 1
        
        print(f"\n{'='*70}")
        print(f"🔄 RETRY QUEUE PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"   Processed: {processed}")
        print(f"   Success: {success}")
        print(f"   Failed: {failed}")
        
        # Show updated queue stats
        stats = retry_manager.get_queue_stats()
        print(f"\n   Updated queue stats:")
        print(f"   - Total: {stats['total']}")
        print(f"   - Ready: {stats['ready_for_retry']}")
        print(f"   - Pending: {stats['pending']}")
        print(f"   - Max retries: {stats['max_retries_reached']}")
        print(f"{'='*70}\n")
        
        return {'processed': processed, 'success': success, 'failed': failed}


def process_single_video_from_jable(jable_data: dict, headless: bool = True) -> bool:
    """
    Main entry point called from Jable scraper
    
    Args:
        jable_data: Video data from Jable scraper
        headless: Run browser in headless mode
    
    Returns:
        bool: True if successful, False otherwise
    """
    pipeline = IntegratedPipeline()
    result = pipeline.process_video(jable_data, headless=headless)
    return result is not None


def process_javdb_retry_queue(max_videos: int = 10, headless: bool = True) -> dict:
    """
    Process JAVDatabase retry queue
    
    Args:
        max_videos: Maximum number of videos to retry
        headless: Run browser in headless mode
    
    Returns:
        dict: Statistics about retry processing
    """
    pipeline = IntegratedPipeline()
    return pipeline.process_retry_queue(max_videos=max_videos, headless=headless)


def get_retry_queue_stats() -> dict:
    """Get statistics about retry queue"""
    if RETRY_MANAGER_AVAILABLE:
        return retry_manager.get_queue_stats()
    return {'total': 0, 'ready_for_retry': 0, 'pending': 0, 'max_retries_reached': 0}


if __name__ == "__main__":
    # Test mode
    print("Testing integrated pipeline...")
    
    # Sample Jable data
    test_jable_data = {
        "code": "MIDA-486",
        "title": "Test Video",
        "duration": "2:00:00",
        "views": "100000",
        "likes": "1000",
        "categories": ["Test"],
        "tags": ["Test"],
        "hosting": {"streamwish": {"watch_url": "https://example.com"}},
        "source_url": "https://jable.tv/test"
    }
    
    success = process_single_video_from_jable(test_jable_data, headless=True)
    
    if success:
        print("\n✅ Test successful!")
    else:
        print("\n❌ Test failed!")
