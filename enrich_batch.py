"""
Enrich videos in batches (safer for large databases)
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add javdatabase to path
javdb_path = Path(__file__).parent / "javdatabase"
sys.path.insert(0, str(javdb_path))

from scrape_single import scrape_single_video
from merge_single import merge_and_validate


def load_database():
    """Load current database"""
    db_path = Path(__file__).parent / "database" / "combined_videos.json"
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_database(data):
    """Save database with single backup file and update tracking"""
    db_path = Path(__file__).parent / "database" / "combined_videos.json"
    backup_path = db_path.with_suffix('.json.backup')
    
    # Backup existing database (overwrites old backup)
    if db_path.exists():
        import shutil
        shutil.copy(db_path, backup_path)
        print(f"   ✅ Backup: {backup_path.name}")
    
    # Save
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Update all tracking files using database_manager
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from database_manager import db_manager
        db_manager.update_progress()
        db_manager.update_stats()
        print(f"   ✅ Updated tracking files")
    except Exception as e:
        print(f"   ⚠️  Could not update tracking files: {e}")


def enrich_batch(batch_size=5, start_index=0, headless=True):
    """
    Enrich videos in batches
    
    Args:
        batch_size: Number of videos to process in this batch
        start_index: Index to start from (for resuming)
        headless: Run browser in headless mode
    """
    print("="*70)
    print(f"BATCH ENRICHMENT - {batch_size} videos starting from index {start_index}")
    print("="*70)
    
    # Load database
    print("\n📂 Loading database...")
    videos = load_database()
    total_videos = len(videos)
    print(f"   Total videos: {total_videos}")
    
    # Filter videos without JAVDatabase data
    videos_without_javdb = []
    for i, v in enumerate(videos):
        if not v.get('javdb_available'):
            videos_without_javdb.append((i, v))
    
    print(f"   Videos without JAVDatabase: {len(videos_without_javdb)}")
    
    if not videos_without_javdb:
        print("\n✅ All videos already have JAVDatabase data!")
        return
    
    # Get batch
    batch = videos_without_javdb[start_index:start_index + batch_size]
    
    if not batch:
        print(f"\n⚠️  No videos to process at index {start_index}")
        print(f"   Total videos without JAVDatabase: {len(videos_without_javdb)}")
        return
    
    print(f"\n🎬 Processing batch: {len(batch)} videos")
    print(f"   Range: {start_index + 1} to {start_index + len(batch)} of {len(videos_without_javdb)}")
    
    # Show what will be processed
    print(f"\n📋 Videos in this batch:")
    for i, (idx, video) in enumerate(batch, 1):
        code = video.get('code', 'UNKNOWN')
        print(f"   {i}. {code}")
    
    # Process batch
    success_count = 0
    not_found_count = 0
    error_count = 0
    
    print("\n" + "="*70)
    print("PROCESSING")
    print("="*70)
    
    for i, (original_idx, video) in enumerate(batch, 1):
        code = video.get('code', 'UNKNOWN')
        
        print(f"\n[{i}/{len(batch)}] {code}")
        print("-"*70)
        
        try:
            # Scrape JAVDatabase
            print(f"   📊 Scraping JAVDatabase...")
            javdb_data = scrape_single_video(code, headless=headless)
            
            if javdb_data:
                print(f"   ✅ Found!")
                print(f"      Title: {javdb_data.get('title', 'N/A')[:50]}...")
                print(f"      Cast: {len(javdb_data.get('cast', []))}")
                print(f"      Screenshots: {len(javdb_data.get('screenshots', []))}")
                print(f"      Studio: {javdb_data.get('studio', 'N/A')}")
                
                # Merge data
                print(f"   🔗 Merging...")
                merged_data = merge_and_validate(video, javdb_data)
                
                # Update in original database
                videos[original_idx] = merged_data
                
                print(f"   ✅ Updated")
                success_count += 1
                
            else:
                print(f"   ⚠️  Not found in JAVDatabase")
                not_found_count += 1
            
            # Delay between requests
            if i < len(batch):
                print(f"   ⏳ Waiting 3 seconds...")
                time.sleep(3)
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted by user")
            print(f"   Saving progress...")
            save_database(videos)
            print(f"\n   Processed: {i}/{len(batch)}")
            print(f"   Success: {success_count}")
            return
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
            continue
    
    # Save after batch
    print(f"\n💾 Saving database...")
    save_database(videos)
    
    # Summary
    print("\n" + "="*70)
    print("BATCH COMPLETE")
    print("="*70)
    print(f"Processed: {len(batch)} videos")
    print(f"✅ Success: {success_count}")
    print(f"⚠️  Not found: {not_found_count}")
    print(f"❌ Errors: {error_count}")
    
    # Show overall progress
    videos_with_javdb = [v for v in videos if v.get('javdb_available')]
    remaining = len(videos) - len(videos_with_javdb)
    
    print(f"\n📊 Overall Progress:")
    print(f"   Total videos: {len(videos)}")
    print(f"   With JAVDatabase: {len(videos_with_javdb)}")
    print(f"   Remaining: {remaining}")
    
    if remaining > 0:
        next_start = start_index + batch_size
        print(f"\n💡 To continue, run:")
        print(f"   python enrich_batch.py --start {next_start}")
    else:
        print(f"\n🎉 All videos enriched!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich videos in batches')
    parser.add_argument('--batch', type=int, default=5, help='Batch size (default: 5)')
    parser.add_argument('--start', type=int, default=0, help='Start index (default: 0)')
    parser.add_argument('--no-headless', action='store_true', help='Run with visible browser')
    
    args = parser.parse_args()
    
    headless = not args.no_headless
    
    print("\n🎬 JAVDatabase Batch Enrichment")
    print(f"   Batch size: {args.batch}")
    print(f"   Start index: {args.start}")
    print(f"   Mode: {'Headless' if headless else 'Visible browser'}")
    
    enrich_batch(
        batch_size=args.batch,
        start_index=args.start,
        headless=headless
    )
