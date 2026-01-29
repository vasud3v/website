#!/usr/bin/env python3
"""
Database Migration Script
Fixes existing data to match the corrected structure
"""
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

def migrate_database():
    """Migrate database to corrected structure"""
    print("="*70)
    print("DATABASE MIGRATION")
    print("="*70)
    
    db_file = Path("database/combined_videos.json")
    
    if not db_file.exists():
        print("\n❌ Database file not found: database/combined_videos.json")
        print("   Nothing to migrate.")
        return
    
    # Backup first
    backup_file = db_file.with_suffix(f'.backup_{int(datetime.now().timestamp())}.json')
    print(f"\n💾 Creating backup: {backup_file.name}")
    shutil.copy2(db_file, backup_file)
    print("✅ Backup created")
    
    # Load database
    print(f"\n📖 Loading database...")
    with open(db_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both formats
    if isinstance(data, list):
        videos = data
        stats = {}
    else:
        videos = data.get('videos', [])
        stats = data.get('stats', {})
    
    print(f"✅ Loaded {len(videos)} videos")
    
    # Migration counters
    changes = {
        'hosting_urls_renamed': 0,
        'upload_time_added': 0,
        'actresses_deduplicated': 0,
        'source_url_added': 0,
        'duration_parsed': 0,
        'file_size_estimated': 0
    }
    
    # Migrate each video
    print(f"\n🔄 Migrating videos...")
    for i, video in enumerate(videos):
        code = video.get('code', f'video_{i}')
        
        # Fix 1: Rename hosting_urls to hosting
        if 'hosting_urls' in video:
            video['hosting'] = video.pop('hosting_urls')
            changes['hosting_urls_renamed'] += 1
        
        # Fix 2: Add upload_time to hosting entries
        if 'hosting' in video:
            for host in video['hosting']:
                if 'upload_time' not in video['hosting'][host]:
                    # Use uploaded_at if available, otherwise current time
                    if 'uploaded_at' in video:
                        try:
                            dt = datetime.fromisoformat(video['uploaded_at'].replace('Z', '+00:00'))
                            video['hosting'][host]['upload_time'] = int(dt.timestamp())
                        except:
                            video['hosting'][host]['upload_time'] = int(time.time())
                    else:
                        video['hosting'][host]['upload_time'] = int(time.time())
                    changes['upload_time_added'] += 1
        
        # Fix 3: Deduplicate actresses
        if 'actresses' in video and isinstance(video['actresses'], list):
            original_count = len(video['actresses'])
            video['actresses'] = list(set(video['actresses']))
            if len(video['actresses']) < original_count:
                changes['actresses_deduplicated'] += 1
        
        # Fix 4: Add source_url if missing
        if 'source_url' not in video:
            # Try to get from javdb_url or embed_url
            if 'javdb_url' in video:
                video['source_url'] = video['javdb_url']
                changes['source_url_added'] += 1
            elif 'embed_url' in video:
                video['source_url'] = video['embed_url']
                changes['source_url_added'] += 1
        
        # Fix 5: Parse duration from runtime
        if 'runtime' in video and video['runtime'] and not video.get('duration'):
            runtime_str = video['runtime']
            if 'min' in runtime_str:
                try:
                    minutes = int(runtime_str.split()[0])
                    video['duration_minutes'] = minutes
                    hours = minutes // 60
                    mins = minutes % 60
                    video['duration'] = f"{hours}:{mins:02d}:00"
                    changes['duration_parsed'] += 1
                except:
                    pass
        
        # Fix 6: Estimate file_size if missing
        if 'file_size' not in video or not video['file_size']:
            # Estimate based on duration (rough: 1 min = 10MB for 720p)
            if 'duration_minutes' in video and video['duration_minutes']:
                estimated_mb = video['duration_minutes'] * 10
                video['file_size'] = f"~{estimated_mb}MB"
                changes['file_size_estimated'] += 1
        
        # Fix 7: Fix title fields (NEW)
        original_title = video.get('title', '')
        if original_title == code or not original_title:
            # Import the fix function
            import sys
            sys.path.insert(0, 'jable')
            try:
                from utils import fix_video_title
                video = fix_video_title(video)
                if video.get('title') != original_title:
                    changes.setdefault('titles_fixed', 0)
                    changes['titles_fixed'] += 1
            except ImportError:
                # Inline fix if import fails
                title_japanese = video.get('title_japanese', '')
                if title_japanese and ' - ' in title_japanese:
                    parts = title_japanese.split(' - ', 1)
                    if parts[0].strip() == code:
                        video['title'] = parts[1].strip()
                        video['title_japanese'] = ''
                        changes.setdefault('titles_fixed', 0)
                        changes['titles_fixed'] += 1
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"   Processed {i + 1}/{len(videos)} videos...", end='\r')
    
    print(f"   Processed {len(videos)}/{len(videos)} videos... ✅")
    
    # Update stats
    stats['total_videos'] = len(videos)
    stats['last_updated'] = datetime.now().isoformat()
    
    # Save migrated database
    print(f"\n💾 Saving migrated database...")
    migrated_data = {
        'videos': videos,
        'stats': stats
    }
    
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(migrated_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Database saved")
    
    # Print summary
    print("\n" + "="*70)
    print("MIGRATION SUMMARY")
    print("="*70)
    
    total_changes = sum(changes.values())
    
    if total_changes == 0:
        print("\n✅ No changes needed - database already in correct format!")
    else:
        print(f"\n📊 Changes Applied:")
        for change_type, count in changes.items():
            if count > 0:
                label = change_type.replace('_', ' ').title()
                print(f"   {label}: {count}")
        
        print(f"\n✅ Total Changes: {total_changes}")
    
    print(f"\n💾 Backup Location: {backup_file}")
    print(f"   (Keep this in case you need to rollback)")
    
    print("\n" + "="*70)
    print("MIGRATION COMPLETE")
    print("="*70)
    
    # Validate migrated data
    print("\n🔍 Validating migrated data...")
    issues = []
    
    for video in videos:
        # Check for hosting_urls (should be gone)
        if 'hosting_urls' in video:
            issues.append(f"Video {video.get('code')} still has 'hosting_urls'")
        
        # Check for hosting with upload_time
        if 'hosting' in video:
            for host, data in video['hosting'].items():
                if 'upload_time' not in data:
                    issues.append(f"Video {video.get('code')} missing upload_time in {host}")
    
    if issues:
        print(f"⚠️  Found {len(issues)} validation issues:")
        for issue in issues[:5]:  # Show first 5
            print(f"   - {issue}")
        if len(issues) > 5:
            print(f"   ... and {len(issues) - 5} more")
    else:
        print("✅ All validation checks passed!")
    
    print("\n✅ Migration successful!")
    print("   Your database is now using the correct structure.")
    print("   Run 'python validate_workflow.py' to verify.")

if __name__ == "__main__":
    migrate_database()
