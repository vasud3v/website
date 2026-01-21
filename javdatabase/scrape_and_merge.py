"""
Scrape random videos from JAVDatabase and merge with Jable data
"""

import json
import random
from pathlib import Path
from dataclasses import asdict
from scrape_clean import CleanJAVDBScraper


def merge_video_data(jable_video: dict, javdb_video: dict) -> dict:
    """Merge Jable and JAVDatabase data into combined format"""
    
    # Start with basic info
    merged = {
        "code": jable_video["code"],
        "title": javdb_video.get("title") or jable_video["title"],
        "title_jp": javdb_video.get("title_jp"),
        
        # Media
        "cover_url": javdb_video.get("cover_url"),
        "screenshots": javdb_video.get("screenshots", []),
        
        # Cast
        "cast": javdb_video.get("cast", []),
        
        # Video Info
        "release_date": javdb_video.get("release_date"),
        "duration": jable_video.get("duration"),
        "runtime_minutes": javdb_video.get("runtime_minutes"),
        "hd_quality": jable_video.get("hd_quality"),
        "file_size": jable_video.get("file_size"),
        
        # Production
        "studio": javdb_video.get("studio"),
        "director": javdb_video.get("director"),
        "label": javdb_video.get("label"),
        "series": javdb_video.get("series"),
        
        # Categories & Tags
        "categories": jable_video.get("categories", []),
        "genres": javdb_video.get("genres", []),
        "tags": jable_video.get("tags", []),
        
        # Social & Stats
        "views": jable_video.get("views", "").replace(" ", ""),
        "likes": jable_video.get("likes", "").replace(" ", ""),
        "rating": javdb_video.get("rating"),
        "rating_count": javdb_video.get("rating_count"),
        
        # Streaming
        "hosting": jable_video.get("hosting", {}),
        
        # Sources
        "source_javdb": javdb_video.get("source_url"),
        "source_jable": jable_video.get("source_url"),
        "scraped_at": javdb_video.get("scraped_at")
    }
    
    return merged


def main():
    """Main function"""
    
    # Load Jable database
    jable_db_path = "../jable/database/videos_complete.json"
    print(f"Loading Jable database: {jable_db_path}")
    
    with open(jable_db_path, 'r', encoding='utf-8') as f:
        jable_videos = json.load(f)
    
    print(f"Found {len(jable_videos)} videos in Jable database")
    
    # Get 5 random videos
    random_videos = random.sample(jable_videos, 5)
    codes = [v["code"] for v in random_videos]
    
    print(f"\nSelected random videos: {', '.join(codes)}")
    print("="*60)
    
    # Initialize scraper
    scraper = CleanJAVDBScraper(headless=True)
    
    try:
        scraper._init_driver()
        
        javdb_videos = []
        merged_videos = []
        
        # Scrape each video
        for i, code in enumerate(codes, 1):
            print(f"\n[{i}/5] Scraping {code} from JAVDatabase...")
            
            try:
                video_data = scraper.scrape_video_by_code(code)
            except Exception as e:
                print(f"  ✗ Error: {e}")
                video_data = None
            
            if video_data:
                javdb_dict = asdict(video_data)
                javdb_videos.append(javdb_dict)
                
                # Find matching Jable video
                jable_video = next((v for v in random_videos if v["code"] == code), None)
                
                if jable_video:
                    # Merge data
                    merged = merge_video_data(jable_video, javdb_dict)
                    merged_videos.append(merged)
                    print(f"  ✓ Merged with Jable data")
            else:
                print(f"  ✗ Not found on JAVDatabase")
        
        # Save outputs
        output_dir = Path("database")
        output_dir.mkdir(exist_ok=True)
        
        # Save JAVDatabase data
        javdb_output = output_dir / "javdb_sample_5.json"
        with open(javdb_output, 'w', encoding='utf-8') as f:
            json.dump(javdb_videos, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved JAVDatabase data: {javdb_output}")
        
        # Save merged data
        merged_output = output_dir / "combined_sample_5.json"
        with open(merged_output, 'w', encoding='utf-8') as f:
            json.dump(merged_videos, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved combined data: {merged_output}")
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Videos scraped: {len(javdb_videos)}/5")
        print(f"Videos merged: {len(merged_videos)}/5")
        print(f"\nCodes: {', '.join([v['code'] for v in merged_videos])}")
        
        if merged_videos:
            print(f"\nSample video: {merged_videos[0]['code']}")
            print(f"  - Screenshots: {len(merged_videos[0].get('screenshots', []))}")
            print(f"  - Cast: {len(merged_videos[0].get('cast', []))}")
            print(f"  - Genres: {len(merged_videos[0].get('genres', []))}")
            print(f"  - Hosting: {list(merged_videos[0].get('hosting', {}).keys())}")
    
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
