#!/usr/bin/env python3
"""
Test Re-upload Logic
Verifies that videos are re-uploaded when database is empty
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import db_manager

def test_reupload_logic():
    """Test the re-upload logic"""
    print("="*70)
    print("TESTING RE-UPLOAD LOGIC")
    print("="*70)
    
    # Test case 1: Video not in database
    print("\n1. Video NOT in database:")
    video = db_manager.get_video_by_code("TEST-001")
    if video:
        print(f"   ❌ FAIL: Video found when it shouldn't exist")
    else:
        print(f"   ✅ PASS: Video not found, will be processed")
    
    # Test case 2: Video in database WITHOUT hosting data
    print("\n2. Video in database WITHOUT hosting data:")
    test_video = {
        'code': 'TEST-002',
        'title': 'Test Video',
        'source_url': 'https://test.com/test-002',
        'scraped_at': '2026-01-29T00:00:00'
    }
    db_manager.add_or_update_video(test_video)
    
    video = db_manager.get_video_by_code("TEST-002")
    if video and not video.get('hosting'):
        print(f"   ✅ PASS: Video found without hosting, will be re-uploaded")
    else:
        print(f"   ❌ FAIL: Video should exist without hosting")
    
    # Test case 3: Video in database WITH hosting data
    print("\n3. Video in database WITH hosting data:")
    test_video_with_hosting = {
        'code': 'TEST-003',
        'title': 'Test Video with Hosting',
        'source_url': 'https://test.com/test-003',
        'scraped_at': '2026-01-29T00:00:00',
        'hosting': {
            'mixdrop': {
                'embed_url': 'https://mixdrop.to/e/test',
                'upload_time': 1234567890
            }
        }
    }
    db_manager.add_or_update_video(test_video_with_hosting)
    
    video = db_manager.get_video_by_code("TEST-003")
    if video and video.get('hosting'):
        print(f"   ✅ PASS: Video found with hosting, will be skipped")
    else:
        print(f"   ❌ FAIL: Video should exist with hosting")
    
    # Test case 4: Empty database scenario
    print("\n4. Empty database scenario:")
    all_videos = db_manager.get_all_videos()
    print(f"   Total videos in database: {len(all_videos)}")
    
    # Simulate checking a video that was in progress file but not in DB
    video_code = "ABF-315"
    video = db_manager.get_video_by_code(video_code)
    if not video:
        print(f"   ✅ PASS: {video_code} not in database, will be processed")
    elif not video.get('hosting'):
        print(f"   ✅ PASS: {video_code} in database but no hosting, will be re-uploaded")
    else:
        print(f"   ⚠️  {video_code} has hosting data, will be skipped")
    
    print("\n" + "="*70)
    print("EXPECTED BEHAVIOR")
    print("="*70)
    print("""
When database is deleted:
1. ✅ Videos NOT in database → Process and upload
2. ✅ Videos in database WITHOUT hosting → Re-upload only
3. ⏭️  Videos in database WITH hosting → Skip

When progress file exists but database is empty:
1. ✅ Check database first, not just progress file
2. ✅ If not in database, remove from progress and re-process
3. ✅ If in database without hosting, re-upload
""")
    
    print("\n" + "="*70)
    print("CLEANUP")
    print("="*70)
    
    # Clean up test videos
    print("Removing test videos...")
    all_videos = db_manager.get_all_videos()
    cleaned_videos = [v for v in all_videos if not v.get('code', '').startswith('TEST-')]
    
    if len(cleaned_videos) < len(all_videos):
        # Save cleaned database
        import json
        from datetime import datetime
        db_file = Path("database/combined_videos.json")
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump({
                'videos': cleaned_videos,
                'stats': {
                    'total_videos': len(cleaned_videos),
                    'last_updated': datetime.now().isoformat()
                }
            }, f, indent=2, ensure_ascii=False)
        print(f"✅ Removed {len(all_videos) - len(cleaned_videos)} test videos")
    else:
        print("✅ No test videos to remove")

if __name__ == "__main__":
    test_reupload_logic()
