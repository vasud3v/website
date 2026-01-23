"""
Batch scrape all videos from combined database
Enriches videos with JAVDatabase metadata
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))
sys.path.insert(0, str(Path(__file__).parent))

from scrape_single import scrape_single_video
from merge_single import merge_and_validate

try:
    from database_manager import db_manager
    DATABASE_MANAGER_AVAILABLE = True
except ImportError:
    DATABASE_MANAGER_AVAILABLE = False
    print("⚠️ Database manager not available, using direct file access")


class BatchScraper:
    """Batch scrape and merge videos"""
    
    def __init__(self, db_path: str = None, headless: bool = True):
        if db_path is None:
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            db_path = str(project_root / "database" / "combined_videos.json")
        
        self.db_path = db_path
        self.headless = headless
        self.stats = {
            'total': 0,
            'already_enriched': 0,
            'success': 0,
            'not_found': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def load_database(self):
        """Load combined database"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return []
    
    def save_database(self, data):
        """Save combined database"""
        try:
            # Backup first
            backup_path = f"{self