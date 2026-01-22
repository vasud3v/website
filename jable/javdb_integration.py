"""
Integration hook for Jable scraper to call JAVDatabase pipeline
Uses centralized database manager in root/database folder
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for database_manager
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

# Add javdatabase to path
javdb_path = parent_path / "javdatabase"
sys.path.insert(0, str(javdb_path))

# Import centralized database manager
try:
    from database_manager import db_manager
    DATABASE_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Database manager not available: {e}")
    DATABASE_MANAGER_AVAILABLE = False

try:
    from integrated_pipeline import IntegratedPipeline
    JAVDB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ JAVDatabase integration not available: {e}")
    JAVDB_AVAILABLE = False


def enrich_with_javdb(video_data: dict, headless: bool = True) -> bool:
    """
    Enrich Jable video data with JAVDatabase metadata
    Saves to centralized database/combined_videos.json
    
    Args:
        video_data: Video data from Jable scraper
        headless: Run browser in headless mode
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not JAVDB_AVAILABLE:
        print("⚠️ JAVDatabase integration not available, skipping enrichment")
        return False
    
    if not DATABASE_MANAGER_AVAILABLE:
        print("⚠️ Database manager not available, skipping enrichment")
        return False
    
    try:
        # Use centralized database path (absolute path to project root)
        project_root = Path(__file__).parent.parent
        combined_db_path = project_root / "database" / "combined_videos.json"
        pipeline = IntegratedPipeline(combined_db_path=str(combined_db_path))
        
        # Process the video
        result = pipeline.process_video(video_data, headless=headless)
        
        if result:
            print(f"✓ JAVDatabase enrichment successful for {video_data.get('code')}")
            # Update database manager stats
            db_manager.update_stats()
            db_manager.update_progress()
        
        return result
        
    except Exception as e:
        print(f"❌ JAVDatabase enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return False
