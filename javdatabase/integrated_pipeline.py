"""
Integrated pipeline to be called from Jable scraper
Handles JAVDatabase scraping + merging + saving for single video
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
sys.path.insert(0, str(Path(__file__).parent))

from scrape_single import scrape_single_video
from merge_single import merge_and_validate


class IntegratedPipeline:
    """Integrated pipeline for processing single video"""
    
    def __init__(self, combined_db_path: str = "../database/combined_videos.json"):
        self.combined_db_path = combined_db_path
        self.error_log_path = "database/errors.json"
        self.stats_path = "database/stats.json"
        
        # Ensure directories exist
        Path(self.combined_db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.error_log_path).parent.mkdir(parents=True, exist_ok=True)
    
    def load_combined_database(self) -> list:
        """Load existing combined database with error handling"""
        try:
            if os.path.exists(self.combined_db_path):
                with open(self.combined_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    print(f"⚠️ Invalid database format, starting fresh")
                    # Backup corrupted file
                    backup_path = f"{self.combined_db_path}.backup.{int(time.time())}"
                    shutil.copy(self.combined_db_path, backup_path)
                    print(f"  Backed up to: {backup_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON decode error: {e}")
            # Backup corrupted file
            if os.path.exists(self.combined_db_path):
                backup_path = f"{self.combined_db_path}.backup.{int(time.time())}"
                shutil.copy(self.combined_db_path, backup_path)
                print(f"  Backed up corrupted file to: {backup_path}")
            return []
        except Exception as e:
            print(f"⚠️ Error loading database: {e}")
            return []
    
    def save_combined_database(self, data: list) -> bool:
        """Save combined database with atomic write"""
        try:
            # Write to temporary file first
            temp_path = f"{self.combined_db_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            if os.path.exists(self.combined_db_path):
                backup_path = f"{self.combined_db_path}.bak"
                shutil.copy(self.combined_db_path, backup_path)
            
            shutil.move(temp_path, self.combined_db_path)
            return True
            
        except Exception as e:
            print(f"❌ Error saving database: {e}")
            return False
    
    def is_already_processed(self, video_code: str) -> bool:
        """Check if video already exists in combined database"""
        existing = self.load_combined_database()
        return any(v.get("code") == video_code.upper() for v in existing)
    
    def log_error(self, video_code: str, error: str, error_type: str = "unknown"):
        """Log error to error file"""
        try:
            errors = []
            if os.path.exists(self.error_log_path):
                with open(self.error_log_path, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            
            errors.append({
                "code": video_code,
                "error": error,
                "error_type": error_type,
                "timestamp": datetime.now().isoformat()
            })
            
            with open(self.error_log_path, 'w', encoding='utf-8') as f:
                json.dump(errors, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Could not log error: {e}")
    
    def update_stats(self, success: bool, javdb_available: bool):
        """Update processing statistics"""
        try:
            stats = {
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "javdb_available": 0,
                "javdb_unavailable": 0,
                "last_updated": None
            }
            
            if os.path.exists(self.stats_path):
                with open(self.stats_path, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            
            stats["total_processed"] += 1
            if success:
                stats["successful"] += 1
            else:
                stats["failed"] += 1
            
            if javdb_available:
                stats["javdb_available"] += 1
            else:
                stats["javdb_unavailable"] += 1
            
            stats["last_updated"] = datetime.now().isoformat()
            
            with open(self.stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Could not update stats: {e}")
    
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
                print(f"     Will use Jable data only")
                
        except Exception as e:
            print(f"  ❌ JAVDatabase scraping failed: {e}")
            print(f"     Will use Jable data only")
            self.log_error(video_code, str(e), "javdb_scrape_error")
        
        # Step 2: Merge data
        print(f"\n🔗 Step 2: Merging data...")
        try:
            merged_data = merge_and_validate(jable_data, javdb_data)
            print(f"  ✅ Data merged successfully")
            
        except Exception as e:
            print(f"  ❌ Merge failed: {e}")
            self.log_error(video_code, str(e), "merge_error")
            self.update_stats(success=False, javdb_available=bool(javdb_data))
            return None
        
        # Step 3: Save to combined database
        print(f"\n💾 Step 3: Saving to combined database...")
        try:
            existing = self.load_combined_database()
            
            # Remove if exists (shouldn't happen, but just in case)
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
        print(f"{'='*70}\n")
        
        return merged_data


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
