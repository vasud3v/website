"""
Save JavaGG videos to centralized database
Integrates with database_manager.py
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path for database_manager
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

try:
    from database_manager import db_manager
    DATABASE_AVAILABLE = True
    print("✓ Connected to centralized database")
except ImportError as e:
    print(f"⚠️ Database manager not available: {e}")
    DATABASE_AVAILABLE = False


def save_video_to_database(video_data: dict, enriched: bool = False) -> bool:
    """
    Save video to centralized database
    
    Args:
        video_data: Video data dict (from JavaGG scraper or enriched)
        enriched: Whether this is enriched with JAVDatabase
    
    Returns:
        bool: True if successful
    """
    if not DATABASE_AVAILABLE:
        print("⚠️ Database not available, cannot save")
        return False
    
    try:
        code = video_data.get('code')
        if not code:
            print("❌ No video code, cannot save")
            return False
        
        # Check if already exists
        existing = db_manager.get_video_by_code(code)
        
        if existing:
            print(f"  📝 Updating existing video: {code}")
            # Merge with existing data (preserve hosting info if present)
            if existing.get('hosting') and not video_data.get('hosting'):
                video_data['hosting'] = existing['hosting']
        else:
            print(f"  ➕ Adding new video: {code}")
        
        # Add metadata
        from datetime import datetime
        video_data['processed_at'] = datetime.now().isoformat()
        video_data['source'] = 'javgg'
        
        # Save to database
        if db_manager.add_or_update_video(video_data):
            print(f"  ✅ Saved to database")
            
            # Show stats
            all_videos = db_manager.get_all_videos()
            print(f"     Total videos in database: {len(all_videos)}")
            
            return True
        else:
            print(f"  ❌ Failed to save to database")
            return False
            
    except Exception as e:
        print(f"  ❌ Error saving to database: {e}")
        return False


def get_video_from_database(code: str) -> Optional[Dict]:
    """
    Get video from database by code
    
    Args:
        code: Video code
    
    Returns:
        dict: Video data or None
    """
    if not DATABASE_AVAILABLE:
        return None
    
    return db_manager.get_video_by_code(code)


def is_video_in_database(code: str) -> bool:
    """
    Check if video is already in database
    
    Args:
        code: Video code
    
    Returns:
        bool: True if exists
    """
    if not DATABASE_AVAILABLE:
        return False
    
    return db_manager.get_video_by_code(code) is not None


def print_database_stats():
    """Print database statistics"""
    if not DATABASE_AVAILABLE:
        print("⚠️ Database not available")
        return
    
    db_manager.print_status()


# Example usage:
"""
from javgg_scraper import JavaGGScraper
from javdb_enrichment import enrich_with_javdb
from save_to_database import save_video_to_database

scraper = JavaGGScraper(headless=False)
video_data = scraper.scrape_video("https://javgg.net/jav/sone-572/")

if video_data:
    # Convert to dict
    video_dict = video_data.__dict__
    
    # Enrich with JAVDatabase
    enriched_data = enrich_with_javdb(video_dict, headless=True, skip_actress_images=True)
    
    # Save to centralized database
    save_video_to_database(enriched_data, enriched=True)
"""
