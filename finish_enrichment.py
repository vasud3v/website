"""
Finish enriching remaining videos (with smart backup)
"""

import json
import sys
import time
from pathlib import Path

# Add javdatabase to path
javdb_path = Path(__file__).parent / "javdatabase"
sys.path.insert(0, str(javdb_path))

from scrape_single import scrape_single_video
from merge_single import merge_and_validate


def save_database_with_backup(videos, db_path):
    """Save database with single backup file and update all tracking"""
    backup_path = db_path.with_suffix('.json.backup')
    
    # If database exists, backup it (overwrite old backup)
    if db_path.exists():
        import shutil
        shutil.copy(db_path, backup_path)
    
    # Save new data
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)
    
    # Update all tracking files using database_manager
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from database_manager import db_manager
        db_manager.update_progress()
        db_manager.update_stats()
        print(f"   ✅ Updated tracking files")
    except Exception as e:
        print(f"   ⚠️  Could not update tracking files: {e}")


def finish_enrichment():
    """Enrich all remaining videos"""
    print("="*70)
    print("FINISH ENRICHMENT - Remaining Videos")
    print("="*70)
    
    # Load database
    print("\n📂 Loading database...")
    db_path = Path(__file__).parent / "database" / "combined_videos.json"
    with open(db_path, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    print(f"   Total videos: {len(videos)}")
    
    # Find videos without JAVDatabase data
    remaining = [(i, v) for i, v in enumerate(videos) if not v.get('javdb_available')]
    
    print(f"   Remaining without JAVDatabase: {len(remaining)}")
    
    if not remaining:
        print("\n✅ All videos already enriched!")
        return
    
    print(f"\n📋 Videos to process:")
    for i, (idx, video) in enumerate(remaining, 1):
        code = video.get('code', 'UNKNOWN')
        print(f"   {i}. {code}")
    
    print(f"\n🎬 Processing {len(remaining)} videos...")
    
    success = 0
    not_found = 0
    errors = 0
    
    for i, (idx, video) in enumerate(remaining, 1):
        code = video.get('code', 'UNKNOWN')
        
        print(f"\n[{i}/{len(remaining)}] {code}")
        print("-"*70)
        
        try:
            print(f"   📊 Scraping...")
            javdb_data = scrape_single_video(code, headless=True)
            
            if javdb_data:
                print(f"   ✅ Found - Cast: {len(javdb_data.get('cast', []))}, Screenshots: {len(javdb_data.get('screenshots', []))}")
                
                merged_data = merge_and_validate(video, javdb_data)
                videos[idx] = merged_data
                
                success += 1
            else:
                print(f"   ⚠️  Not found")
                not_found += 1
            
            # Save every 3 videos (overwrites same backup)
            if i % 3 == 0:
                print(f"   💾 Saving progress...")
                save_database_with_backup(videos, db_path)
            
            if i < len(remaining):
                time.sleep(3)
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted! Saving progress...")
            save_database_with_backup(videos, db_path)
            print(f"   Processed: {i}/{len(remaining)}")
            print(f"   Success: {success}, Not found: {not_found}, Errors: {errors}")
            return
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            errors += 1
    
    # Final save
    print(f"\n💾 Final save...")
    save_database_with_backup(videos, db_path)
    
    print(f"\n" + "="*70)
    print("ENRICHMENT COMPLETE!")
    print("="*70)
    print(f"✅ Success: {success}")
    print(f"⚠️  Not found: {not_found}")
    print(f"❌ Errors: {errors}")
    
    with_javdb = [v for v in videos if v.get('javdb_available')]
    print(f"\n📊 Final Statistics:")
    print(f"   Total videos: {len(videos)}")
    print(f"   With JAVDatabase: {len(with_javdb)}")
    print(f"   Without JAVDatabase: {len(videos) - len(with_javdb)}")
    
    print(f"\n🎉 Done! Database updated.")
    print(f"   Backup saved as: {db_path.with_suffix('.json.backup').name}")


if __name__ == "__main__":
    finish_enrichment()
