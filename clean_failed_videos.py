"""
Clean up failed_videos.json - remove entries that are now successful
"""

import json
from pathlib import Path

def clean_failed_videos():
    """Remove failed entries for videos that are now successful"""
    print("="*70)
    print("CLEAN FAILED VIDEOS")
    print("="*70)
    
    # Load databases
    db_path = Path(__file__).parent / "database"
    
    with open(db_path / "combined_videos.json", 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    with open(db_path / "failed_videos.json", 'r', encoding='utf-8') as f:
        failed = json.load(f)
    
    print(f"\n📂 Current status:")
    print(f"   Total videos: {len(videos)}")
    print(f"   Failed entries: {len(failed)}")
    
    # Get codes of successful videos (have hosting with data)
    successful_codes = {v.get('code') for v in videos 
                       if v.get('hosting') and len(v.get('hosting', {})) > 0}
    
    # Filter out failed entries that are now successful
    still_failed = []
    removed = []
    
    for entry in failed:
        code = entry.get('code')
        if code and code in successful_codes:
            removed.append(code)
        else:
            still_failed.append(entry)
    
    if removed:
        print(f"\n✅ Removing {len(removed)} entries that are now successful:")
        for code in removed:
            print(f"   - {code}")
        
        # Save cleaned list
        with open(db_path / "failed_videos.json", 'w', encoding='utf-8') as f:
            json.dump(still_failed, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Cleaned! Remaining failed: {len(still_failed)}")
    else:
        print(f"\n✅ No cleanup needed - all failed entries are still valid")
    
    if still_failed:
        print(f"\n⚠️  Still failed:")
        for entry in still_failed:
            code = entry.get('code', 'UNKNOWN')
            error = entry.get('last_error', 'Unknown error')
            retries = entry.get('retry_count', 0)
            print(f"   - {code}: {error} (retries: {retries})")


if __name__ == "__main__":
    clean_failed_videos()
