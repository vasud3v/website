"""
Fix all database issues with parallel processing
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
sys.path.insert(0, 'javgg')
sys.path.insert(0, 'javdatabase')

from javdb_scraper import JAVDatabaseScraper

# Thread-safe lock for database updates
db_lock = Lock()

def fix_video(video_data, index, total):
    """Fix a single video"""
    code = video_data.get('code', 'Unknown')
    
    print(f"\n[{index}/{total}] {code}")
    
    # Check if needs fixing
    screenshots = video_data.get('screenshots', [])
    categories = video_data.get('categories', [])
    tags = video_data.get('tags', [])
    
    needs_fix = False
    issues = []
    
    if not screenshots:
        needs_fix = True
        issues.append("no screenshots")
    
    if categories == tags:
        needs_fix = True
        issues.append("categories=tags")
    
    if not needs_fix:
        print(f"  ✓ Already good")
        return {'code': code, 'fixed': False, 'reason': 'already_good'}
    
    print(f"  Issues: {', '.join(issues)}")
    print(f"  Re-enriching...")
    
    # Create scraper for this thread
    scraper = JAVDatabaseScraper(headless=True)
    
    try:
        metadata = scraper.scrape_video_metadata(code)
        
        if metadata:
            updates = {}
            
            # Update screenshots
            if metadata.screenshots:
                updates['screenshots'] = metadata.screenshots
                print(f"    ✓ Added {len(metadata.screenshots)} screenshots")
            
            # Update categories (JAVDatabase only)
            if metadata.categories:
                updates['categories'] = metadata.categories
                print(f"    ✓ Updated categories: {len(metadata.categories)}")
            
            # Update tags (merge with existing)
            if metadata.categories:
                existing_tags = set(video_data.get('tags', []))
                javdb_categories = set(metadata.categories)
                updates['tags'] = list(existing_tags | javdb_categories)
                print(f"    ✓ Updated tags: {len(updates['tags'])}")
            
            # Update actress details if missing
            if metadata.actress_details and not video_data.get('actress_details'):
                updates['actress_details'] = {}
                for name, details in metadata.actress_details.items():
                    updates['actress_details'][name] = {
                        'name': details.get('name'),
                        'name_jp': details.get('name_jp'),
                        'image': details.get('image'),
                        'profile_url': details.get('profile_url'),
                        'age': details.get('age'),
                        'birthdate': details.get('birthdate'),
                        'measurements': details.get('measurements'),
                        'height': details.get('height'),
                        'debut_date': details.get('debut_date'),
                        'debut_age': details.get('debut_age'),
                        'birthplace': details.get('birthplace'),
                        'zodiac_sign': details.get('zodiac_sign'),
                        'blood_type': details.get('blood_type'),
                        'cup_size': details.get('cup_size'),
                        'shoe_size': details.get('shoe_size'),
                        'hair_length': details.get('hair_length'),
                        'hair_color': details.get('hair_color')
                    }
                print(f"    ✓ Added actress details: {len(updates['actress_details'])}")
            
            print(f"  ✓ Fixed")
            return {'code': code, 'fixed': True, 'updates': updates}
        else:
            print(f"  ✗ Could not scrape from JAVDatabase")
            return {'code': code, 'fixed': False, 'reason': 'scrape_failed'}
    
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:80]}")
        return {'code': code, 'fixed': False, 'reason': f'error: {str(e)[:50]}'}
    
    finally:
        scraper.close()


def main():
    print("="*70)
    print("FIXING ALL DATABASE ISSUES (PARALLEL)")
    print("="*70)
    
    # Load database
    with open('database/combined_videos.json', 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    total = len(db['videos'])
    print(f"\nTotal videos: {total}")
    
    # Use 4 workers by default
    max_workers = 4
    
    print(f"\nUsing {max_workers} parallel workers")
    print(f"Starting parallel processing...\n")
    
    # Process videos in parallel
    results = []
    fixed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(fix_video, video, i+1, total): i 
            for i, video in enumerate(db['videos'])
        }
        
        # Process results as they complete
        for future in as_completed(futures):
            idx = futures[future]
            try:
                result = future.result()
                results.append(result)
                
                # Apply updates to database
                if result['fixed'] and 'updates' in result:
                    with db_lock:
                        # Find video and update
                        for video in db['videos']:
                            if video.get('code') == result['code']:
                                video.update(result['updates'])
                                fixed_count += 1
                                break
            
            except Exception as e:
                print(f"\n✗ Task failed: {str(e)[:80]}")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Fixed: {fixed_count}/{total}")
    
    # Show breakdown
    already_good = sum(1 for r in results if not r['fixed'] and r.get('reason') == 'already_good')
    scrape_failed = sum(1 for r in results if not r['fixed'] and r.get('reason') == 'scrape_failed')
    errors = sum(1 for r in results if not r['fixed'] and 'error' in r.get('reason', ''))
    
    print(f"\nBreakdown:")
    print(f"  ✓ Fixed: {fixed_count}")
    print(f"  ✓ Already good: {already_good}")
    print(f"  ✗ Scrape failed: {scrape_failed}")
    print(f"  ✗ Errors: {errors}")
    
    # Save database
    with open('database/combined_videos.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Database saved")


if __name__ == "__main__":
    main()
