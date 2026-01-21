#!/usr/bin/env python3
"""
Backfill existing Jable videos into combined database
Processes all videos from jable/database/videos_complete.json
and enriches them with JAVDatabase metadata
"""

import json
import sys
import os
from pathlib import Path

# Add javdatabase to path
sys.path.insert(0, str(Path(__file__).parent))

from integrated_pipeline import IntegratedPipeline


def load_jable_database(path: str = "../jable/database/videos_complete.json"):
    """Load Jable database"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading Jable database: {e}")
        return []


def main():
    print("=" * 70)
    print("BACKFILL EXISTING JABLE VIDEOS TO COMBINED DATABASE")
    print("=" * 70)
    
    # Load Jable database
    jable_path = "../jable/database/videos_complete.json"
    print(f"\n📂 Loading Jable database from {jable_path}...")
    jable_videos = load_jable_database(jable_path)
    
    if not jable_videos:
        print("❌ No videos found in Jable database")
        return
    
    print(f"✅ Found {len(jable_videos)} videos in Jable database")
    
    # Initialize pipeline
    pipeline = IntegratedPipeline(combined_db_path="../database/combined_videos.json")
    
    # Load existing combined database
    existing = pipeline.load_combined_database()
    existing_codes = {v.get("code", "").upper() for v in existing}
    print(f"📊 Combined database currently has {len(existing)} videos")
    
    # Filter videos that need processing
    to_process = [v for v in jable_videos if v.get("code", "").upper() not in existing_codes]
    
    if not to_process:
        print("\n✅ All Jable videos are already in combined database!")
        return
    
    print(f"\n🔄 Need to process {len(to_process)} videos")
    print(f"⏭️  Skipping {len(jable_videos) - len(to_process)} already processed")
    
    # Process each video
    success_count = 0
    failed_count = 0
    
    for i, video in enumerate(to_process, 1):
        code = video.get("code", "UNKNOWN")
        print(f"\n{'='*70}")
        print(f"[{i}/{len(to_process)}] Processing: {code}")
        print(f"{'='*70}")
        
        try:
            # Convert Jable format to expected format
            jable_data = {
                "code": video.get("code"),
                "title": video.get("title"),
                "source_url": video.get("source_url"),
                "thumbnail_url": video.get("thumbnail_url") or video.get("thumbnail_original"),
                "duration": video.get("duration"),
                "hd_quality": video.get("hd_quality", False),
                "views": video.get("views"),
                "likes": video.get("likes"),
                "release_date": video.get("release_date"),
                "upload_time": video.get("upload_time", ""),
                "processed_at": video.get("processed_at"),
                "categories": video.get("categories", []),
                "models": video.get("models", []),
                "tags": video.get("tags", []),
                "preview_images": video.get("preview_images", []),
                "hosting": video.get("hosting", {}),
                "file_size": video.get("file_size"),
                "upload_folder": video.get("upload_folder")
            }
            
            # Process with pipeline
            result = pipeline.process_video(jable_data, headless=True)
            
            if result:
                success_count += 1
                print(f"✅ Success! ({success_count}/{i})")
            else:
                failed_count += 1
                print(f"⚠️  Failed or skipped ({failed_count}/{i})")
                
        except Exception as e:
            failed_count += 1
            print(f"❌ Error processing {code}: {e}")
            continue
    
    # Final summary
    print(f"\n{'='*70}")
    print("BACKFILL COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Successfully processed: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total attempted: {len(to_process)}")
    
    # Show final database stats
    final_db = pipeline.load_combined_database()
    print(f"\n📊 Combined database now has {len(final_db)} videos")
    
    # Count JAVDatabase coverage
    javdb_count = sum(1 for v in final_db if v.get("javdb_available"))
    print(f"🎭 JAVDatabase coverage: {javdb_count}/{len(final_db)} ({javdb_count*100//len(final_db) if final_db else 0}%)")


if __name__ == "__main__":
    main()
