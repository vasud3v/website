"""
Integration hook for Jable scraper to call JAVDatabase pipeline
Add this import to run_continuous.py after each video is processed
"""

import sys
import os
from pathlib import Path

# Add javdatabase to path
javdb_path = Path(__file__).parent.parent / "javdatabase"
sys.path.insert(0, str(javdb_path))

try:
    from integrated_pipeline import process_single_video_from_jable
    JAVDB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ JAVDatabase integration not available: {e}")
    JAVDB_AVAILABLE = False


def enrich_with_javdb(video_data: dict, headless: bool = True) -> bool:
    """
    Enrich Jable video data with JAVDatabase metadata
    
    Args:
        video_data: Video data from Jable scraper
        headless: Run browser in headless mode
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not JAVDB_AVAILABLE:
        print("⚠️ JAVDatabase integration not available, skipping enrichment")
        return False
    
    try:
        return process_single_video_from_jable(video_data, headless=headless)
    except Exception as e:
        print(f"❌ JAVDatabase enrichment failed: {e}")
        return False


# Example usage in run_continuous.py:
"""
from javdb_integration import enrich_with_javdb

# After processing each video:
video_data = {
    "code": "MIDA-486",
    "title": "...",
    # ... other Jable data
}

# Save to Jable database
save_to_jable_database(video_data)

# Enrich with JAVDatabase and save to combined database
enrich_with_javdb(video_data, headless=True)
"""
