"""
Example: How to integrate JAVDatabase enrichment into run_continuous.py

This shows the minimal changes needed to add JAVDatabase metadata enrichment
"""

# ============================================================================
# STEP 1: Add import at the top of run_continuous.py
# ============================================================================

from javdb_integration import enrich_with_javdb


# ============================================================================
# STEP 2: Modify the video processing function
# ============================================================================

def process_single_video_with_enrichment(video_url):
    """
    Process single video with JAVDatabase enrichment
    
    This is an example of how to modify your existing video processing function
    """
    
    # ========== EXISTING JABLE SCRAPING CODE ==========
    print(f"Processing: {video_url}")
    
    # 1. Scrape video info from Jable
    video_info = scrape_jable_video(video_url)
    video_code = video_info['code']
    
    # 2. Download video
    video_file = download_video(video_info['m3u8_url'])
    
    # 3. Upload to StreamWish
    hosting_data = upload_to_streamwish(video_file)
    
    # 4. Build Jable data structure
    jable_data = {
        "code": video_code,
        "title": video_info['title'],
        "source_url": video_url,
        "thumbnail_url": video_info['thumbnail'],
        "duration": video_info['duration'],
        "hd_quality": video_info['hd'],
        "views": video_info['views'],
        "likes": video_info['likes'],
        "release_date": video_info['release_date'],
        "upload_time": video_info['upload_time'],
        "processed_at": datetime.now().isoformat(),
        "categories": video_info['categories'],
        "models": video_info['models'],
        "tags": video_info['tags'],
        "preview_images": video_info['preview_images'],
        "hosting": hosting_data,
        "file_size": video_info['file_size'],
        "upload_folder": video_code
    }
    
    # 5. Save to Jable database (EXISTING)
    save_to_jable_database(jable_data)
    print(f"✅ Saved to Jable database: {video_code}")
    
    # ========== NEW: JAVDATABASE ENRICHMENT ==========
    
    # 6. Enrich with JAVDatabase metadata
    try:
        print(f"\n🎭 Enriching {video_code} with JAVDatabase metadata...")
        success = enrich_with_javdb(jable_data, headless=True)
        
        if success:
            print(f"✅ {video_code} enriched and saved to combined database")
        else:
            print(f"⚠️ {video_code} enrichment failed, using Jable data only")
            
    except Exception as e:
        print(f"❌ JAVDatabase enrichment error: {e}")
        print(f"   Continuing with Jable data only...")
    
    # ========== EXISTING CLEANUP CODE ==========
    
    # 7. Cleanup temp files
    cleanup_temp_files(video_file)
    
    return True


# ============================================================================
# STEP 3: Optional - Batch Git Commits
# ============================================================================

def main_loop_with_batched_commits():
    """
    Example: Process videos with batched git commits
    """
    videos_to_process = get_video_list()
    videos_processed = 0
    
    for video_url in videos_to_process:
        try:
            # Process video (includes JAVDatabase enrichment)
            process_single_video_with_enrichment(video_url)
            videos_processed += 1
            
            # Commit every 5 videos
            if videos_processed % 5 == 0:
                print(f"\n📤 Committing batch of 5 videos...")
                git_commit_and_push(f"Added {videos_processed} videos")
                print(f"✅ Pushed to GitHub\n")
                
        except Exception as e:
            print(f"❌ Error processing {video_url}: {e}")
            continue
    
    # Final commit for remaining videos
    if videos_processed % 5 != 0:
        print(f"\n📤 Committing final batch...")
        git_commit_and_push(f"Added {videos_processed} videos (final)")


# ============================================================================
# STEP 4: Optional - Add Statistics Reporting
# ============================================================================

def print_processing_stats():
    """
    Print statistics after processing
    """
    import json
    
    try:
        with open('../javdatabase/database/stats.json', 'r') as f:
            stats = json.load(f)
        
        print("\n" + "="*60)
        print("📊 PROCESSING STATISTICS")
        print("="*60)
        print(f"Total processed: {stats['total_processed']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"JAVDatabase available: {stats['javdb_available']}")
        print(f"JAVDatabase unavailable: {stats['javdb_unavailable']}")
        print(f"Success rate: {stats['successful']/stats['total_processed']*100:.1f}%")
        print(f"JAVDatabase coverage: {stats['javdb_available']/stats['total_processed']*100:.1f}%")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"⚠️ Could not load statistics: {e}")


# ============================================================================
# COMPLETE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    """
    Complete example of integrated workflow
    """
    
    print("="*70)
    print("🚀 STARTING INTEGRATED JABLE + JAVDATABASE SCRAPER")
    print("="*70)
    
    # Get videos to process
    videos = get_video_list()
    print(f"\nFound {len(videos)} videos to process\n")
    
    # Process each video
    for i, video_url in enumerate(videos, 1):
        print(f"\n{'='*70}")
        print(f"📹 VIDEO {i}/{len(videos)}")
        print(f"{'='*70}")
        
        try:
            process_single_video_with_enrichment(video_url)
            
            # Commit every 5 videos
            if i % 5 == 0:
                git_commit_and_push(f"Added videos {i-4} to {i}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    # Final commit
    if len(videos) % 5 != 0:
        git_commit_and_push(f"Added final batch")
    
    # Print statistics
    print_processing_stats()
    
    print("="*70)
    print("✅ SCRAPING COMPLETE")
    print("="*70)


# ============================================================================
# MINIMAL INTEGRATION (Just 3 lines!)
# ============================================================================

"""
If you just want the minimal integration, add these 3 lines after saving to Jable database:

    from javdb_integration import enrich_with_javdb
    
    # After: save_to_jable_database(jable_data)
    enrich_with_javdb(jable_data, headless=True)
    
That's it! Everything else is handled automatically.
"""
