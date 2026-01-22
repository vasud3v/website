#!/usr/bin/env python3
"""
Centralized Database Manager
- Single source of truth in database/combined_videos.json
- Progress tracking for all operations
- Handles database deletion gracefully
- Tracks hosting status and failures
- Automatic recovery and sync
- Enhanced file locking with retry logic
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import shutil

try:
    from filelock import FileLock, Timeout
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False
    print("⚠️ filelock library not available, using basic locking")

# Central database location
DATABASE_DIR = "database"
COMBINED_DB = os.path.join(DATABASE_DIR, "combined_videos.json")
PROGRESS_DB = os.path.join(DATABASE_DIR, "progress_tracking.json")
FAILED_DB = os.path.join(DATABASE_DIR, "failed_videos.json")
HOSTING_STATUS_DB = os.path.join(DATABASE_DIR, "hosting_status.json")
STATS_DB = os.path.join(DATABASE_DIR, "stats.json")

# Backup directory
BACKUP_DIR = os.path.join(DATABASE_DIR, "backups")

# Legacy database locations (for migration)
LEGACY_LOCATIONS = [
    "jable/database/videos_complete.json",
    "jable/database/videos_failed.json",
    "javdatabase/database/stats.json"
]


class DatabaseManager:
    """Centralized database management with progress tracking"""
    
    def __init__(self):
        """Initialize database manager"""
        self.locks = {}  # filepath -> FileLock instance
        self.lock_timeout = 30  # seconds
        self.max_retries = 3
        
        self.ensure_structure()
        self.migrate_legacy_data()
    
    def _get_lock(self, filepath: str) -> Optional[FileLock]:
        """Get or create lock for a file"""
        if not FILELOCK_AVAILABLE:
            return None
        
        if filepath not in self.locks:
            lock_file = filepath + ".lock"
            self.locks[filepath] = FileLock(lock_file, timeout=self.lock_timeout)
        return self.locks[filepath]
    
    def _read_json_locked(self, filepath: str, default: Any = None) -> Any:
        """Read JSON with file lock and retry logic"""
        lock = self._get_lock(filepath)
        
        if not lock:
            # Fallback to non-locked read
            return self._read_json(filepath, default)
        
        for attempt in range(self.max_retries):
            try:
                with lock:
                    return self._read_json(filepath, default)
            except Timeout:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                    print(f"⚠️ Lock timeout on {filepath}, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed to acquire lock on {filepath} after {self.max_retries} attempts")
                    # Fallback to non-locked read
                    return self._read_json(filepath, default)
            except Exception as e:
                print(f"⚠️ Error reading {filepath}: {e}")
                return default if default is not None else []
        
        return default if default is not None else []
    
    def _write_json_locked(self, filepath: str, data: Any, backup: bool = True) -> bool:
        """Write JSON with exclusive lock and retry logic"""
        lock = self._get_lock(filepath)
        
        if not lock:
            # Fallback to non-locked write
            return self._write_json(filepath, data, backup)
        
        for attempt in range(self.max_retries):
            try:
                with lock:
                    return self._write_json(filepath, data, backup)
            except Timeout:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                    print(f"⚠️ Lock timeout on {filepath}, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed to acquire lock on {filepath} after {self.max_retries} attempts")
                    # Fallback to non-locked write
                    return self._write_json(filepath, data, backup)
            except Exception as e:
                print(f"❌ Error writing {filepath}: {e}")
                return False
        
        return False
    
    def ensure_structure(self):
        """Ensure all database files and directories exist"""
        # Create directories
        os.makedirs(DATABASE_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Initialize files if they don't exist
        if not os.path.exists(COMBINED_DB):
            self._write_json(COMBINED_DB, [])
            print(f"✓ Created {COMBINED_DB}")
        
        if not os.path.exists(PROGRESS_DB):
            self._write_json(PROGRESS_DB, {
                "last_updated": datetime.now().isoformat(),
                "total_discovered": 0,
                "total_processed": 0,
                "total_failed": 0,
                "in_progress": [],
                "last_video_code": None,
                "last_video_url": None,
                "session_start": datetime.now().isoformat()
            })
            print(f"✓ Created {PROGRESS_DB}")
        
        if not os.path.exists(FAILED_DB):
            self._write_json(FAILED_DB, [])
            print(f"✓ Created {FAILED_DB}")
        
        if not os.path.exists(HOSTING_STATUS_DB):
            self._write_json(HOSTING_STATUS_DB, {
                "streamwish": {"available": True, "last_check": None, "rate_limited_until": None},
                "lulustream": {"available": True, "last_check": None, "rate_limited_until": None},
                "streamtape": {"available": True, "last_check": None, "rate_limited_until": None}
            })
            print(f"✓ Created {HOSTING_STATUS_DB}")
        
        if not os.path.exists(STATS_DB):
            self._write_json(STATS_DB, {
                "total_videos": 0,
                "total_size_bytes": 0,
                "by_hosting": {},
                "by_category": {},
                "by_model": {},
                "last_updated": datetime.now().isoformat()
            })
            print(f"✓ Created {STATS_DB}")
    
    def migrate_legacy_data(self):
        """Migrate data from legacy locations to central database"""
        migrated = 0
        
        for legacy_path in LEGACY_LOCATIONS:
            if os.path.exists(legacy_path):
                try:
                    with open(legacy_path, 'r', encoding='utf-8') as f:
                        legacy_data = json.load(f)
                    
                    if isinstance(legacy_data, list) and len(legacy_data) > 0:
                        # Merge into combined database
                        current_data = self.get_all_videos()
                        
                        # Get existing codes to avoid duplicates
                        existing_codes = {v.get('code') for v in current_data if v.get('code')}
                        
                        for video in legacy_data:
                            code = video.get('code')
                            if code and code not in existing_codes:
                                current_data.append(video)
                                existing_codes.add(code)
                                migrated += 1
                        
                        if migrated > 0:
                            self._write_json(COMBINED_DB, current_data)
                            print(f"✓ Migrated {migrated} videos from {legacy_path}")
                        
                        # Backup and remove legacy file
                        backup_name = f"{os.path.basename(legacy_path)}.migrated.{int(time.time())}"
                        backup_path = os.path.join(BACKUP_DIR, backup_name)
                        shutil.copy2(legacy_path, backup_path)
                        print(f"✓ Backed up {legacy_path} to {backup_path}")
                
                except Exception as e:
                    print(f"⚠️ Could not migrate {legacy_path}: {e}")
        
        if migrated > 0:
            self.update_stats()
    
    def _read_json(self, filepath: str, default: Any = None) -> Any:
        """Safely read JSON file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading {filepath}: {e}")
        return default if default is not None else []
    
    def _write_json(self, filepath: str, data: Any, backup: bool = True):
        """Safely write JSON file with atomic write and backup"""
        try:
            # Create backup if file exists
            if backup and os.path.exists(filepath):
                backup_path = filepath + '.backup'
                shutil.copy2(filepath, backup_path)
            
            # Atomic write
            temp_path = filepath + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Replace original
            if os.path.exists(filepath):
                os.remove(filepath)
            os.rename(temp_path, filepath)
            
            return True
        except Exception as e:
            print(f"❌ Error writing {filepath}: {e}")
            # Clean up temp file
            if os.path.exists(filepath + '.tmp'):
                try:
                    os.remove(filepath + '.tmp')
                except:
                    pass
            return False
    
    def get_all_videos(self) -> List[Dict]:
        """Get all videos from combined database"""
        return self._read_json_locked(COMBINED_DB, [])
    
    def get_video_by_code(self, code: str) -> Optional[Dict]:
        """Get video by code"""
        videos = self.get_all_videos()
        for video in videos:
            if video.get('code') == code:
                return video
        return None
    
    def get_video_by_url(self, url: str) -> Optional[Dict]:
        """Get video by source URL"""
        videos = self.get_all_videos()
        normalized_url = self._normalize_url(url)
        for video in videos:
            if self._normalize_url(video.get('source_url', '')) == normalized_url:
                return video
        return None
    
    def is_processed(self, code: str = None, url: str = None) -> bool:
        """Check if video is already processed (has hosting data)"""
        if code:
            video = self.get_video_by_code(code)
        elif url:
            video = self.get_video_by_url(url)
        else:
            return False
        
        if video:
            hosting = video.get('hosting', {})
            return bool(hosting and len(hosting) > 0)
        return False
    
    def add_or_update_video(self, video_data: Dict) -> bool:
        """Add new video or update existing one"""
        try:
            videos = self.get_all_videos()
            code = video_data.get('code')
            
            if not code:
                print("❌ Video data missing code")
                return False
            
            # Find existing video
            found = False
            for i, v in enumerate(videos):
                if v.get('code') == code:
                    # Update existing
                    videos[i] = video_data
                    found = True
                    print(f"✓ Updated video: {code}")
                    break
            
            if not found:
                # Add new
                videos.append(video_data)
                print(f"✓ Added video: {code}")
            
            # Sort by processed_at (newest first)
            videos.sort(key=lambda x: x.get('processed_at', ''), reverse=True)
            
            # Remove duplicates (keep first occurrence)
            seen_codes = set()
            unique_videos = []
            for video in videos:
                v_code = video.get('code')
                if v_code and v_code not in seen_codes:
                    seen_codes.add(v_code)
                    unique_videos.append(video)
            
            # Save
            if self._write_json_locked(COMBINED_DB, unique_videos):
                self.update_progress()
                self.update_stats()
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error adding/updating video: {e}")
            return False
    
    def mark_as_failed(self, code: str = None, url: str = None, error: str = None, retry_count: int = 0):
        """Mark video as failed"""
        try:
            failed_videos = self._read_json_locked(FAILED_DB, [])
            
            # Find existing entry
            found = False
            for v in failed_videos:
                if (code and v.get('code') == code) or (url and v.get('source_url') == url):
                    v['retry_count'] = retry_count + 1
                    v['last_error'] = error
                    v['last_attempt'] = datetime.now().isoformat()
                    found = True
                    break
            
            if not found:
                failed_videos.append({
                    'code': code,
                    'source_url': url,
                    'retry_count': 1,
                    'last_error': error,
                    'last_attempt': datetime.now().isoformat()
                })
            
            self._write_json_locked(FAILED_DB, failed_videos)
            self.update_progress()
            return True
            
        except Exception as e:
            print(f"❌ Error marking as failed: {e}")
            return False
    
    def get_failed_count(self, code: str = None, url: str = None) -> int:
        """Get retry count for failed video"""
        try:
            failed_videos = self._read_json_locked(FAILED_DB, [])
            for v in failed_videos:
                if (code and v.get('code') == code) or (url and v.get('source_url') == url):
                    return v.get('retry_count', 0)
        except:
            pass
        return 0
    
    def update_progress(self):
        """Update progress tracking"""
        try:
            videos = self.get_all_videos()
            failed_videos = self._read_json_locked(FAILED_DB, [])
            
            # Count processed (has hosting data)
            processed = sum(1 for v in videos if v.get('hosting') and len(v.get('hosting', {})) > 0)
            
            progress = {
                "last_updated": datetime.now().isoformat(),
                "total_videos": len(videos),
                "total_processed": processed,
                "total_failed": len(failed_videos),
                "success_rate": (processed / len(videos) * 100) if len(videos) > 0 else 0,
                "last_video_code": videos[0].get('code') if videos else None,
                "last_video_url": videos[0].get('source_url') if videos else None
            }
            
            self._write_json(PROGRESS_DB, progress, backup=False)
            
        except Exception as e:
            print(f"⚠️ Could not update progress: {e}")
    
    def update_stats(self):
        """Update statistics"""
        try:
            videos = self.get_all_videos()
            
            stats = {
                "total_videos": len(videos),
                "total_size_bytes": sum(v.get('file_size', 0) for v in videos),
                "by_hosting": {},
                "by_category": {},
                "by_model": {},
                "last_updated": datetime.now().isoformat()
            }
            
            # Count by hosting
            for video in videos:
                hosting = video.get('hosting', {})
                for service in hosting.keys():
                    stats['by_hosting'][service] = stats['by_hosting'].get(service, 0) + 1
            
            # Count by category
            for video in videos:
                for category in video.get('categories', []):
                    stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Count by model
            for video in videos:
                for model in video.get('models', []):
                    stats['by_model'][model] = stats['by_model'].get(model, 0) + 1
            
            self._write_json(STATS_DB, stats, backup=False)
            
        except Exception as e:
            print(f"⚠️ Could not update stats: {e}")
    
    def update_hosting_status(self, service: str, available: bool = True, rate_limited_until: int = None):
        """Update hosting service status"""
        try:
            status = self._read_json_locked(HOSTING_STATUS_DB, {})
            
            if service not in status:
                status[service] = {}
            
            status[service]['available'] = available
            status[service]['last_check'] = datetime.now().isoformat()
            
            if rate_limited_until:
                status[service]['rate_limited_until'] = rate_limited_until
            
            self._write_json(HOSTING_STATUS_DB, status, backup=False)
            
        except Exception as e:
            print(f"⚠️ Could not update hosting status: {e}")
    
    def get_hosting_status(self, service: str) -> Dict:
        """Get hosting service status"""
        try:
            status = self._read_json_locked(HOSTING_STATUS_DB, {})
            return status.get(service, {"available": True, "last_check": None})
        except:
            return {"available": True, "last_check": None}
    
    def is_hosting_available(self, service: str) -> bool:
        """Check if hosting service is available"""
        status = self.get_hosting_status(service)
        
        # Check if rate limited
        if status.get('rate_limited_until'):
            if time.time() < status['rate_limited_until']:
                return False
        
        return status.get('available', True)
    
    def get_progress(self) -> Dict:
        """Get current progress"""
        return self._read_json(PROGRESS_DB, {})
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        return self._read_json(STATS_DB, {})
    
    def create_backup(self, label: str = None) -> str:
        """Create full database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}"
            if label:
                backup_name += f"_{label}"
            
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup all database files
            files_backed_up = 0
            for filename in os.listdir(DATABASE_DIR):
                if filename.endswith('.json'):
                    src = os.path.join(DATABASE_DIR, filename)
                    dst = os.path.join(backup_path, filename)
                    shutil.copy2(src, dst)
                    files_backed_up += 1
            
            print(f"✓ Created backup: {backup_path} ({files_backed_up} files)")
            return backup_path
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            if not os.path.exists(backup_path):
                print(f"❌ Backup not found: {backup_path}")
                return False
            
            # Create safety backup first
            self.create_backup("before_restore")
            
            # Restore files
            files_restored = 0
            for filename in os.listdir(backup_path):
                if filename.endswith('.json'):
                    src = os.path.join(backup_path, filename)
                    dst = os.path.join(DATABASE_DIR, filename)
                    shutil.copy2(src, dst)
                    files_restored += 1
            
            print(f"✓ Restored from backup: {backup_path} ({files_restored} files)")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def verify_integrity(self) -> Dict:
        """Verify database integrity"""
        issues = []
        
        # Check if files exist
        for filepath in [COMBINED_DB, PROGRESS_DB, FAILED_DB, HOSTING_STATUS_DB, STATS_DB]:
            if not os.path.exists(filepath):
                issues.append(f"Missing file: {filepath}")
        
        # Check for duplicates
        videos = self.get_all_videos()
        codes = [v.get('code') for v in videos if v.get('code')]
        if len(codes) != len(set(codes)):
            duplicates = len(codes) - len(set(codes))
            issues.append(f"Found {duplicates} duplicate video codes")
        
        # Check for videos without hosting
        no_hosting = sum(1 for v in videos if not v.get('hosting') or len(v.get('hosting', {})) == 0)
        if no_hosting > 0:
            issues.append(f"Found {no_hosting} videos without hosting data")
        
        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "total_videos": len(videos),
            "checked_at": datetime.now().isoformat()
        }
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison to prevent duplicates.
        
        Rules:
        - Convert to lowercase
        - Use https:// protocol
        - Remove www. prefix
        - Remove trailing slashes
        - Remove query parameters (?key=value)
        - Remove fragments (#section)
        """
        if not url:
            return ""
        
        url = url.lower().strip()
        
        # Normalize protocol
        url = url.replace('http://', 'https://')
        
        # Remove www prefix
        url = url.replace('https://www.', 'https://')
        
        # Remove query parameters
        if '?' in url:
            url = url.split('?')[0]
        
        # Remove fragments
        if '#' in url:
            url = url.split('#')[0]
        
        # Remove trailing slash (after removing query/fragment)
        url = url.rstrip('/')
        
        return url
    
    def print_status(self):
        """Print current database status"""
        print("\n" + "="*60)
        print("DATABASE STATUS")
        print("="*60)
        
        progress = self.get_progress()
        stats = self.get_stats()
        
        print(f"\n📊 Progress:")
        print(f"   Total videos: {progress.get('total_videos', 0)}")
        print(f"   Processed: {progress.get('total_processed', 0)}")
        print(f"   Failed: {progress.get('total_failed', 0)}")
        print(f"   Success rate: {progress.get('success_rate', 0):.1f}%")
        
        print(f"\n💾 Storage:")
        total_gb = stats.get('total_size_bytes', 0) / (1024**3)
        print(f"   Total size: {total_gb:.2f} GB")
        
        print(f"\n🌐 Hosting:")
        for service, count in stats.get('by_hosting', {}).items():
            status = self.get_hosting_status(service)
            available = "✓" if status.get('available') else "✗"
            print(f"   {available} {service}: {count} videos")
        
        print(f"\n📁 Database location: {DATABASE_DIR}")
        print(f"   Combined DB: {os.path.getsize(COMBINED_DB) / 1024:.1f} KB" if os.path.exists(COMBINED_DB) else "   Combined DB: Not found")
        
        # Integrity check
        integrity = self.verify_integrity()
        if integrity['healthy']:
            print(f"\n✅ Database integrity: HEALTHY")
        else:
            print(f"\n⚠️ Database integrity: ISSUES FOUND")
            for issue in integrity['issues']:
                print(f"   - {issue}")
        
        print("="*60)


# Global instance
db_manager = DatabaseManager()


if __name__ == "__main__":
    # Test and display status
    db_manager.print_status()
