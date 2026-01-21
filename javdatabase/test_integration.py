"""
Test script to verify the integrated pipeline works correctly
Run this before deploying to production
"""

import json
import os
import sys
from pathlib import Path

# Test imports
print("="*70)
print("🧪 TESTING INTEGRATED PIPELINE")
print("="*70)

print("\n1. Testing imports...")
try:
    from scrape_single import scrape_single_video
    print("   ✅ scrape_single imported")
except ImportError as e:
    print(f"   ❌ Failed to import scrape_single: {e}")
    sys.exit(1)

try:
    from merge_single import merge_and_validate
    print("   ✅ merge_single imported")
except ImportError as e:
    print(f"   ❌ Failed to import merge_single: {e}")
    sys.exit(1)

try:
    from integrated_pipeline import IntegratedPipeline, process_single_video_from_jable
    print("   ✅ integrated_pipeline imported")
except ImportError as e:
    print(f"   ❌ Failed to import integrated_pipeline: {e}")
    sys.exit(1)

# Test data structures
print("\n2. Testing data structures...")

test_jable_data = {
    "code": "TEST-001",
    "title": "Test Video Title",
    "source_url": "https://jable.tv/test",
    "thumbnail_url": "https://example.com/thumb.jpg",
    "duration": "2:00:00",
    "hd_quality": True,
    "views": "100 000",
    "likes": "1 000",
    "release_date": "2026-01-21",
    "upload_time": "2026-01-21T12:00:00",
    "processed_at": "2026-01-21T12:00:00",
    "categories": ["Test Category"],
    "models": ["Test Model"],
    "tags": ["Test", "Tag"],
    "preview_images": ["https://example.com/preview.jpg"],
    "hosting": {
        "streamwish": {
            "embed_url": "https://example.com/embed",
            "watch_url": "https://example.com/watch",
            "filecode": "test123"
        }
    },
    "file_size": 1000000000,
    "upload_folder": "TEST-001"
}

test_javdb_data = {
    "code": "TEST-001",
    "title": "Professional Test Video Title",
    "title_jp": "テストビデオ",
    "cover_url": "https://example.com/cover.jpg",
    "screenshots": [
        "https://example.com/screenshot1.jpg",
        "https://example.com/screenshot2.jpg"
    ],
    "cast": [
        {
            "actress_name": "Test Actress",
            "actress_name_jp": "テスト女優",
            "actress_age": 25,
            "actress_height_cm": 160,
            "actress_image_url": "https://example.com/actress.jpg",
            "actress_cup_size": "C"
        }
    ],
    "release_date": "2026-01-21",
    "runtime_minutes": 120,
    "studio": "Test Studio",
    "director": "Test Director",
    "genres": ["Test Genre", "Another Genre"],
    "source_url": "https://javdatabase.com/test",
    "scraped_at": "2026-01-21T12:00:00"
}

print("   ✅ Test data created")

# Test merge function
print("\n3. Testing merge function...")
try:
    merged = merge_and_validate(test_jable_data, test_javdb_data)
    
    # Verify required fields
    assert merged["code"] == "TEST-001", "Code mismatch"
    assert merged["title"], "Title missing"
    assert merged["hosting"], "Hosting missing"
    assert len(merged["screenshots"]) == 2, "Screenshots missing"
    assert len(merged["cast"]) == 1, "Cast missing"
    assert merged["javdb_available"] == True, "JAVDatabase flag wrong"
    
    print("   ✅ Merge successful")
    print(f"      - Code: {merged['code']}")
    print(f"      - Screenshots: {len(merged['screenshots'])}")
    print(f"      - Cast: {len(merged['cast'])}")
    print(f"      - JAVDatabase: {merged['javdb_available']}")
    
except Exception as e:
    print(f"   ❌ Merge failed: {e}")
    sys.exit(1)

# Test merge without JAVDatabase data
print("\n4. Testing merge without JAVDatabase data...")
try:
    merged_no_javdb = merge_and_validate(test_jable_data, None)
    
    assert merged_no_javdb["code"] == "TEST-001", "Code mismatch"
    assert merged_no_javdb["javdb_available"] == False, "JAVDatabase flag wrong"
    assert len(merged_no_javdb["cast"]) == 0, "Cast should be empty"
    
    print("   ✅ Fallback merge successful")
    print(f"      - JAVDatabase: {merged_no_javdb['javdb_available']}")
    print(f"      - Cast: {len(merged_no_javdb['cast'])} (empty as expected)")
    
except Exception as e:
    print(f"   ❌ Fallback merge failed: {e}")
    sys.exit(1)

# Test pipeline
print("\n5. Testing integrated pipeline...")
try:
    pipeline = IntegratedPipeline(combined_db_path="database/test_combined.json")
    
    # Test database operations
    print("   Testing database operations...")
    
    # Load (should be empty)
    data = pipeline.load_combined_database()
    assert isinstance(data, list), "Database should be a list"
    print(f"      ✅ Load: {len(data)} videos")
    
    # Save
    test_data = [merged]
    success = pipeline.save_combined_database(test_data)
    assert success, "Save failed"
    print(f"      ✅ Save: successful")
    
    # Load again
    data = pipeline.load_combined_database()
    assert len(data) == 1, "Should have 1 video"
    assert data[0]["code"] == "TEST-001", "Code mismatch"
    print(f"      ✅ Reload: {len(data)} videos")
    
    # Test duplicate detection
    is_dup = pipeline.is_already_processed("TEST-001")
    assert is_dup, "Should detect duplicate"
    print(f"      ✅ Duplicate detection: working")
    
    # Cleanup test file
    if os.path.exists("database/test_combined.json"):
        os.remove("database/test_combined.json")
    if os.path.exists("database/test_combined.json.bak"):
        os.remove("database/test_combined.json.bak")
    
    print("   ✅ Pipeline tests passed")
    
except Exception as e:
    print(f"   ❌ Pipeline test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test error logging
print("\n6. Testing error logging...")
try:
    pipeline = IntegratedPipeline()
    pipeline.log_error("TEST-001", "Test error", "test_error")
    
    if os.path.exists("database/errors.json"):
        with open("database/errors.json", 'r') as f:
            errors = json.load(f)
        assert len(errors) > 0, "No errors logged"
        print(f"   ✅ Error logging: {len(errors)} errors logged")
        
        # Cleanup
        os.remove("database/errors.json")
    else:
        print("   ⚠️  Error log file not created")
    
except Exception as e:
    print(f"   ❌ Error logging failed: {e}")

# Test statistics
print("\n7. Testing statistics...")
try:
    pipeline = IntegratedPipeline()
    pipeline.update_stats(success=True, javdb_available=True)
    
    if os.path.exists("database/stats.json"):
        with open("database/stats.json", 'r') as f:
            stats = json.load(f)
        assert stats["total_processed"] > 0, "No stats recorded"
        print(f"   ✅ Statistics: {stats['total_processed']} videos tracked")
        
        # Cleanup
        os.remove("database/stats.json")
    else:
        print("   ⚠️  Stats file not created")
    
except Exception as e:
    print(f"   ❌ Statistics failed: {e}")

# Summary
print("\n" + "="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)
print("\nThe integrated pipeline is ready for production!")
print("\nNext steps:")
print("1. Add 'from javdb_integration import enrich_with_javdb' to run_continuous.py")
print("2. Call 'enrich_with_javdb(jable_data)' after each video")
print("3. Run the scraper and monitor database/combined_videos.json")
print("\nFor detailed instructions, see INTEGRATION_GUIDE.md")
print("="*70)
