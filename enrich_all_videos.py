"""
Enrich all videos in database with JAVDatabase metadata
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

# Add parent to path for database manager
sys.path.insert(0, str(Path(__file__).parent))
try:
    from database_manager import db_manager
    DATABASE_MANAGER_AVAILABLE = True
except ImportError:
    DATABASE_MANAGER_AVAILABLE = False
    print("⚠️ Database manager not available, using direct file access")


def load_database():
    """Load current database"""
    db_path = Path(__file__).parent / "database" / "combined_videos.json"
    with open(db_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_database(data):
    """Save database"""
    db_path = Path(__file__).parent / "database" / "combined_videos.json"
    
    # Backup first
    backup_path = db_path.with_suffix('.json.backup')
    if db_path.exists():
        import shutil
        shutil.copy(db_path, backup_path)
        print(f"   Backup saved to: {backup_path}")
    
    # Save
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"   Database saved to: {db_path}")


def enrich_all_videos(headless=True, max_videos=None, skip_existing=True):
    """
    Enrich all videos in database with JAVDatabase metadata
    
    Args:
        headless: Run browser in headless mode
        max_videos: Maximum number of videos to process (None = all)
        skip_existing: Skip videos that already have JAVDatabase data
    """
    print("="*70)
    print("ENRICH ALL VIDEOS WITH JAVDATABASE METADATA")
    print("="*70)
    
    # Load database
    print("\n📂 Loading database...")
    videos = load_database()
    print(f"   Total videos: {len(videos)}")
    
    # Filter videos
    if skip_existing:
        videos_to_process = [v for v in videos if not v.get('javdb_available')]
        print(f"   Videos without JAVDatabase data: {len(videos_to_process)}")
    else:
        videos_to_process = videos
        print(f"   Processing all videos (including existing)")
    
    if max_videos:
        videos_to_process = videos_to_process[:max_videos]
        print(f"   Limited to: {max_videos} videos")
    
    if not videos_to_process:
        print("\n✅ All videos already have JAVDatabase data!")
        return
    
    print(f"\n🎬 Will process {len(videos_to_process)} videos")
    
    # Confirm
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Process each video
    success_count = 0
    not_found_count = 0
    error_count = 0
    
    print("\n" + "="*70)
    print("PROCESSING VIDEOS")
    print("="*70)
    
    for i, video in enumerate(videos_to_process, 1):
        code = video.get('code', 'UNKNOWN')
        
        print(f"\n[{i}/{len(videos_to_process)}] {code}")
        print("-"*70)
        
        try:
            # Scrape JAVDatabase
            print(f"   📊 Scraping JAVDatabase...")
            javdb_data = scrape_single_video(code, headless=headless)
            
            if javdb_data:
                print(f"   ✅ JAVDatabase data found")
                print(f"      - Cast: {len(javdb_data.get('cast', []))}")
                print(f"      - Screenshots: {len(javdb_data.get('screenshots', []))}")
                print(f"      - Studio: {javdb_data.get('studio', 'N/A')}")
                
                # Merge data
                print(f"   🔗 Merging data...")
                merged_data = merge_and_validate(video, javdb_data)
                
                # Update in database
                for j, v in enumerate(videos):
                    if v.get('code') == code:
                        videos[j] = merged_data
                        break
                
                print(f"   ✅ Merged and updated")
                success_count += 1
                
            else:
                print(f"   ⚠️  Not found in JAVDatabase")
                print(f"      This is normal for new releases")
                not_found_count += 1
            
            # Save after each video (in case of crash)
            if (i % 5 == 0) or (i == len(videos_to_process)):
                print(f"\n   💾 Saving progress...")
                save_database(videos)
            
            # Delay between requests
            if i < len(videos_to_process):
                print(f"   ⏳ Waiting 3 seconds...")
                time.sleep(3)
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted by user")
            print(f"   Saving progress...")
            save_database(videos)
            print(f"\n   Processed: {i}/{len(videos_to_process)}")
            print(f"   Success: {success_count}")
            print(f"   Not found: {not_found_count}")
            print(f"   Errors: {error_count}")
            return
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            error_count += 1
            continue
    
    # Final save
    print(f"\n💾 Final save...")
    save_database(videos)
    
    # Summary
    print("\n" + "="*70)
    print("ENRICHMENT COMPLETE")
    print("="*70)
    print(f"Total processed: {len(videos_to_process)}")
    print(f"✅ Success: {success_count}")
    print(f"⚠️  Not found: {not_found_count}")
    print(f"❌ Errors: {error_count}")
    
    # Show updated stats
    print(f"\n📊 Database Statistics:")
    with_javdb = [v for v in videos if v.get('javdb_available')]
    print(f"   Total videos: {len(videos)}")
    print(f"   With JAVDatabase: {len(with_javdb)}")
    print(f"   Without JAVDatabase: {len(videos) - len(with_javdb)}")
    
    print(f"\n✅ Done! Check database/combined_videos.json")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich all videos with JAVDatabase metadata')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode (default)')
    parser.add_argument('--no-headless', action='store_true', help='Run with visible browser')
    parser.add_argument('--max', type=int, help='Maximum number of videos to process')
    parser.add_argument('--all', action='store_true', help='Process all videos (including existing)')
    
    args = parser.parse_args()
    
    headless = not args.no_headless
    
    print("\n🎬 JAVDatabase Enrichment Tool")
    print(f"   Mode: {'Headless' if headless else 'Visible browser'}")
    if args.max:
        print(f"   Limit: {args.max} videos")
    if args.all:
        print(f"   Processing: All videos (including existing)")
    else:
        print(f"   Processing: Only videos without JAVDatabase data")
    
    enrich_all_videos(
        headless=headless,
        max_videos=args.max,
        skip_existing=not args.all
    )
