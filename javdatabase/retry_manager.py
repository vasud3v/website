"""
JAVDatabase Retry Manager
Tracks videos not found in JAVDatabase and retries them after 2 days
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

# Use absolute path to project root database
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
RETRY_QUEUE_FILE = PROJECT_ROOT / "database" / "javdb_retry_queue.json"

# Ensure database directory exists
RETRY_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)


class JAVDBRetryManager:
    """Manages retry queue for videos not found in JAVDatabase"""
    
    def __init__(self):
        self.retry_queue_file = RETRY_QUEUE_FILE
        self.retry_delay_days = 2  # Retry after 2 days
        self.max_retries = 5  # Maximum retry attempts
    
    def load_queue(self) -> List[Dict]:
        """Load retry queue from file"""
        try:
            if self.retry_queue_file.exists():
                with open(self.retry_queue_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"⚠️ Error loading retry queue: {e}")
            return []
    
    def save_queue(self, queue: List[Dict]) -> bool:
        """Save retry queue to file"""
        try:
            # Ensure directory exists
            self.retry_queue_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.retry_queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving retry queue: {e}")
            return False
    
    def add_to_queue(self, video_code: str, video_data: Dict, reason: str = "not_found") -> bool:
        """
        Add video to retry queue
        
        Args:
            video_code: Video code (e.g., "FNS-149")
            video_data: Full video data from Jable
            reason: Reason for retry (default: "not_found")
        
        Returns:
            bool: True if added successfully
        """
        try:
            queue = self.load_queue()
            
            # Check if already in queue
            for item in queue:
                if item.get('code') == video_code:
                    print(f"   ℹ️ {video_code} already in retry queue")
                    return True
            
            # Add new entry
            now = datetime.now()
            retry_after = now + timedelta(days=self.retry_delay_days)
            
            entry = {
                'code': video_code,
                'title': video_data.get('title', ''),
                'source_url': video_data.get('source_url', ''),
                'reason': reason,
                'added_at': now.isoformat(),
                'retry_after': retry_after.isoformat(),
                'retry_count': 0,
                'last_retry': None,
                'video_data': video_data  # Store full video data for retry
            }
            
            queue.append(entry)
            
            if self.save_queue(queue):
                print(f"   ✅ Added {video_code} to retry queue")
                print(f"      Retry after: {retry_after.strftime('%Y-%m-%d %H:%M')}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error adding to retry queue: {e}")
            return False
    
    def get_videos_ready_for_retry(self) -> List[Dict]:
        """
        Get videos that are ready for retry (past retry_after time)
        
        Returns:
            List of video entries ready for retry
        """
        try:
            queue = self.load_queue()
            now = datetime.now()
            ready = []
            
            for item in queue:
                retry_after_str = item.get('retry_after')
                retry_count = item.get('retry_count', 0)
                
                if not retry_after_str:
                    continue
                
                # Skip if max retries reached
                if retry_count >= self.max_retries:
                    continue
                
                retry_after = datetime.fromisoformat(retry_after_str)
                
                if now >= retry_after:
                    ready.append(item)
            
            return ready
            
        except Exception as e:
            print(f"❌ Error getting ready videos: {e}")
            return []
    
    def update_retry_status(self, video_code: str, success: bool, found_in_javdb: bool = False) -> bool:
        """
        Update retry status after attempt
        
        Args:
            video_code: Video code
            success: Whether the retry was successful
            found_in_javdb: Whether video was found in JAVDatabase
        
        Returns:
            bool: True if updated successfully
        """
        try:
            queue = self.load_queue()
            updated = False
            
            for item in queue:
                if item.get('code') == video_code:
                    now = datetime.now()
                    item['last_retry'] = now.isoformat()
                    item['retry_count'] = item.get('retry_count', 0) + 1
                    
                    if success and found_in_javdb:
                        # Remove from queue - successfully enriched
                        queue.remove(item)
                        print(f"   ✅ {video_code} successfully enriched, removed from retry queue")
                    elif item['retry_count'] >= self.max_retries:
                        # Max retries reached - remove from queue
                        queue.remove(item)
                        print(f"   ⚠️ {video_code} max retries reached ({self.max_retries}), removed from queue")
                    else:
                        # Schedule next retry
                        next_retry = now + timedelta(days=self.retry_delay_days)
                        item['retry_after'] = next_retry.isoformat()
                        print(f"   ⏰ {video_code} retry scheduled for {next_retry.strftime('%Y-%m-%d %H:%M')}")
                    
                    updated = True
                    break
            
            if updated:
                return self.save_queue(queue)
            return False
            
        except Exception as e:
            print(f"❌ Error updating retry status: {e}")
            return False
    
    def remove_from_queue(self, video_code: str) -> bool:
        """Remove video from retry queue"""
        try:
            queue = self.load_queue()
            original_len = len(queue)
            
            queue = [item for item in queue if item.get('code') != video_code]
            
            if len(queue) < original_len:
                if self.save_queue(queue):
                    print(f"   ✅ Removed {video_code} from retry queue")
                    return True
            return False
            
        except Exception as e:
            print(f"❌ Error removing from queue: {e}")
            return False
    
    def get_queue_stats(self) -> Dict:
        """Get statistics about retry queue"""
        try:
            queue = self.load_queue()
            now = datetime.now()
            
            ready_count = 0
            pending_count = 0
            max_retries_count = 0
            
            for item in queue:
                retry_count = item.get('retry_count', 0)
                retry_after_str = item.get('retry_after')
                
                if retry_count >= self.max_retries:
                    max_retries_count += 1
                elif retry_after_str:
                    retry_after = datetime.fromisoformat(retry_after_str)
                    if now >= retry_after:
                        ready_count += 1
                    else:
                        pending_count += 1
            
            return {
                'total': len(queue),
                'ready_for_retry': ready_count,
                'pending': pending_count,
                'max_retries_reached': max_retries_count
            }
            
        except Exception as e:
            print(f"❌ Error getting queue stats: {e}")
            return {'total': 0, 'ready_for_retry': 0, 'pending': 0, 'max_retries_reached': 0}
    
    def cleanup_old_entries(self, days: int = 30) -> int:
        """
        Remove entries older than specified days that have reached max retries
        
        Args:
            days: Remove entries older than this many days
        
        Returns:
            int: Number of entries removed
        """
        try:
            queue = self.load_queue()
            now = datetime.now()
            cutoff = now - timedelta(days=days)
            
            original_len = len(queue)
            
            # Keep entries that are either:
            # 1. Not at max retries yet
            # 2. Added recently (within cutoff period)
            queue = [
                item for item in queue
                if (item.get('retry_count', 0) < self.max_retries or
                    datetime.fromisoformat(item.get('added_at', now.isoformat())) > cutoff)
            ]
            
            removed = original_len - len(queue)
            
            if removed > 0:
                self.save_queue(queue)
                print(f"   🗑️ Cleaned up {removed} old entries from retry queue")
            
            return removed
            
        except Exception as e:
            print(f"❌ Error cleaning up queue: {e}")
            return 0


# Global instance
retry_manager = JAVDBRetryManager()


if __name__ == "__main__":
    # Test the retry manager
    print("Testing JAVDatabase Retry Manager...")
    
    # Test data
    test_video = {
        'code': 'TEST-123',
        'title': 'Test Video',
        'source_url': 'https://jable.tv/videos/test-123/'
    }
    
    # Add to queue
    print("\n1. Adding video to queue...")
    retry_manager.add_to_queue('TEST-123', test_video, 'not_found')
    
    # Get stats
    print("\n2. Queue stats:")
    stats = retry_manager.get_queue_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Get ready videos
    print("\n3. Videos ready for retry:")
    ready = retry_manager.get_videos_ready_for_retry()
    print(f"   Found {len(ready)} videos ready")
    
    # Remove from queue
    print("\n4. Removing from queue...")
    retry_manager.remove_from_queue('TEST-123')
    
    print("\n✅ Test complete!")
