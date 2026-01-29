"""
JAVDatabase Enrichment for JavaGG Scraper
Enriches JavaGG video metadata with additional data from JAVDatabase.com
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict

# Try to import from javdatabase package
try:
    from javdatabase.javdb_scraper import JAVDatabaseScraper
    # Define a wrapper function to match the expected interface if needed, or update usage
    # For now, just disabling the missing module import
    raise ImportError("Improved scraper not found") 
except ImportError:

    # Fallback to original scraper
    javdb_path = Path(__file__).parent.parent / "javdatabase"
    sys.path.insert(0, str(javdb_path))
    
    try:
        from javdb_scraper import JAVDatabaseScraper
        JAVDB_AVAILABLE = True
        print("✓ Using original JAVDatabase scraper")
    except ImportError as e:
        print(f"⚠️ JAVDatabase scraper not available: {e}")
        JAVDB_AVAILABLE = False


def enrich_with_javdb(javgg_data: dict, headless: bool = True, skip_actress_images: bool = False) -> Optional[dict]:
    """
    Enrich JavaGG video data with JAVDatabase metadata
    
    Args:
        javgg_data: Video data from JavaGG scraper (dict format)
        headless: Run browser in headless mode
        skip_actress_images: Skip fetching actress images (faster)
    
    Returns:
        dict: Enriched video data with JAVDatabase metadata, or original data if enrichment fails
    """
    if not JAVDB_AVAILABLE:
        print("⚠️ JAVDatabase integration not available, skipping enrichment")
        return javgg_data
    
    video_code = javgg_data.get("code", "").upper()
    
    if not video_code:
        print("❌ No video code provided")
        return javgg_data
    
    print(f"\n{'='*70}")
    print(f"🔍 JAVDatabase Enrichment: {video_code}")
    print(f"{'='*70}")
    
    # Check if this video type should skip JAVDatabase enrichment
    should_skip, skip_reason = should_skip_javdb_enrichment(video_code)
    if should_skip:
        print(f"⏭️  Skipping JAVDatabase enrichment: {skip_reason}")
        javgg_data['javdb_available'] = False
        javgg_data['javdb_skip_reason'] = skip_reason
        return javgg_data
    
    scraper = None
    try:
        print(f"  📊 Fetching metadata from JAVDatabase...")
        
        # Use fallback scraper logic since improved scraper isn't available
        if 'JAVDatabaseScraper' in globals():
            temp_scraper = JAVDatabaseScraper(headless=headless)
            try:
                javdb_metadata = temp_scraper.scrape_video_metadata(video_code)
            finally:
                temp_scraper.close()
        else:
            # Try to use improved scraper (no need for scraper object)
            javdb_metadata = scrape_javdb_metadata(video_code, headless=headless)
        
        if javdb_metadata:
            print(f"  ✅ JAVDatabase data retrieved")
            print(f"     - Actresses: {len(javdb_metadata.actresses)}")
            print(f"     - Genres: {len(javdb_metadata.categories)}")
            
            # Merge data
            enriched_data = merge_javgg_and_javdb(javgg_data, javdb_metadata)
            
            print(f"  ✅ Data enriched successfully")
            print(f"{'='*70}\n")
            
            return enriched_data
        else:
            print(f"  ⚠️  Video not found on JAVDatabase")
            print(f"     This is normal for new releases (usually indexed within 2-7 days)")
            print(f"     Using JavaGG data only")
            print(f"{'='*70}\n")
            
            javgg_data['javdb_available'] = False
            javgg_data['javdb_not_found'] = True
            return javgg_data
            
    except Exception as e:
        print(f"  ❌ JAVDatabase enrichment failed: {str(e)[:100]}")
        print(f"     Using JavaGG data only")
        print(f"{'='*70}\n")
        
        javgg_data['javdb_available'] = False
        javgg_data['javdb_error'] = str(e)[:200]
        return javgg_data
        
    finally:
        # No cleanup needed with improved scraper
        pass


def should_skip_javdb_enrichment(video_code: str) -> tuple:
    """
    Check if video should skip JAVDatabase enrichment
    
    Returns:
        tuple: (should_skip, reason)
    """
    video_code_upper = video_code.upper()
    
    # FC2PPV videos are not on JAVDatabase (amateur/independent content)
    if video_code_upper.startswith('FC2') or 'FC2PPV' in video_code_upper or 'FC2-PPV' in video_code_upper:
        return (True, "FC2PPV videos are not indexed on JAVDatabase (amateur content)")
    
    # Amateur patterns
    amateur_patterns = ['AMATEUR', 'PERSONAL', 'PRIVATE']
    for pattern in amateur_patterns:
        if pattern in video_code_upper:
            return (True, f"Amateur/personal content not on JAVDatabase")
    
    return (False, "")


def merge_javgg_and_javdb(javgg_data: dict, javdb_metadata) -> dict:
    """
    Merge JavaGG and JAVDatabase metadata
    
    Priority:
    - JAVDatabase: actresses, director, studio, detailed metadata
    - JavaGG: video URLs, download links, full title
    
    Args:
        javgg_data: Data from JavaGG scraper
        javdb_metadata: VideoMetadata object from JAVDatabase scraper
    
    Returns:
        dict: Merged data (no duplicate javdb_data object)
    """
    # Start with JavaGG data
    merged = javgg_data.copy()
    
    # Mark as enriched
    merged['javdb_available'] = True
    merged['javdb_url'] = javdb_metadata.javdb_url
    
    # Merge actresses (prefer JAVDatabase - deduplicated)
    if javdb_metadata.actresses:
        merged['actresses'] = javdb_metadata.actresses
        print(f"     - Merged actresses: {len(javdb_metadata.actresses)}")
    
    # Add actress details (images, profile URLs, bio)
    # Handle different scraper versions (actress_details vs actress_images)
    if hasattr(javdb_metadata, 'actress_details') and javdb_metadata.actress_details:
        merged['actress_details'] = javdb_metadata.actress_details
        print(f"     - Actress details: {len(javdb_metadata.actress_details)}")
    elif hasattr(javdb_metadata, 'actress_images') and javdb_metadata.actress_images:
        # Convert simple image dict to details format
        merged['actress_details'] = {}
        for name, img in javdb_metadata.actress_images.items():
            merged['actress_details'][name] = {'image': img}
        print(f"     - Actress images: {len(javdb_metadata.actress_images)}")
    
    # Add screenshots from JAVDatabase (high quality)
    if javdb_metadata.screenshots:
        merged['screenshots'] = javdb_metadata.screenshots
        print(f"     - Screenshots: {len(javdb_metadata.screenshots)}")
    
    # Merge director with URL
    if javdb_metadata.director:
        merged['director'] = javdb_metadata.director
        if hasattr(javdb_metadata, 'director_url') and javdb_metadata.director_url:
            merged['director_url'] = javdb_metadata.director_url
        print(f"     - Director: {javdb_metadata.director}")
    
    # Merge studio with URL
    if javdb_metadata.studio:
        merged['studio'] = javdb_metadata.studio
        if hasattr(javdb_metadata, 'studio_url') and javdb_metadata.studio_url:
            merged['studio_url'] = javdb_metadata.studio_url
        # Keep studio_japanese from JavaGG if available
        if not merged.get('studio_japanese'):
            merged['studio_japanese'] = javdb_metadata.studio
        print(f"     - Studio: {javdb_metadata.studio}")
    
    # Merge label with URL
    if javdb_metadata.label:
        merged['label'] = javdb_metadata.label
        if hasattr(javdb_metadata, 'label_url') and javdb_metadata.label_url:
            merged['label_url'] = javdb_metadata.label_url
        print(f"     - Label: {javdb_metadata.label}")
    
    # Merge series with URL
    if javdb_metadata.series:
        merged['series'] = javdb_metadata.series
        if hasattr(javdb_metadata, 'series_url') and javdb_metadata.series_url:
            merged['series_url'] = javdb_metadata.series_url
        print(f"     - Series: {javdb_metadata.series}")
    
    # Add Content ID and DVD ID
    if hasattr(javdb_metadata, 'content_id') and javdb_metadata.content_id:
        merged['content_id'] = javdb_metadata.content_id
        print(f"     - Content ID: {javdb_metadata.content_id}")
    
    if hasattr(javdb_metadata, 'dvd_id') and javdb_metadata.dvd_id:
        merged['dvd_id'] = javdb_metadata.dvd_id
    
    # Add release year
    if hasattr(javdb_metadata, 'release_year') and javdb_metadata.release_year:
        merged['release_year'] = javdb_metadata.release_year
    elif hasattr(javdb_metadata, 'release_date') and javdb_metadata.release_date:
        merged['release_date'] = javdb_metadata.release_date
        merged['release_year'] = javdb_metadata.release_date[:4]
    
    # Add runtime minutes
    if hasattr(javdb_metadata, 'runtime_minutes') and javdb_metadata.runtime_minutes:
        merged['runtime_minutes'] = javdb_metadata.runtime_minutes
    elif hasattr(javdb_metadata, 'runtime') and javdb_metadata.runtime:
         merged['runtime'] = javdb_metadata.runtime
    
    # Add rating and engagement metrics (check attributes exist)
    if hasattr(javdb_metadata, 'rating') and javdb_metadata.rating > 0:
        merged['rating'] = javdb_metadata.rating
        if hasattr(javdb_metadata, 'rating_text'):
             merged['rating_text'] = javdb_metadata.rating_text
        print(f"     - Rating: {javdb_metadata.rating}")
    
    if hasattr(javdb_metadata, 'votes') and javdb_metadata.votes > 0:
        merged['votes'] = javdb_metadata.votes
    
    if hasattr(javdb_metadata, 'views') and javdb_metadata.views > 0:
        merged['views'] = javdb_metadata.views
    
    if hasattr(javdb_metadata, 'favorites') and javdb_metadata.favorites > 0:
        merged['favorites'] = javdb_metadata.favorites
    
    if hasattr(javdb_metadata, 'popularity_rank') and javdb_metadata.popularity_rank > 0:
        merged['popularity_rank'] = javdb_metadata.popularity_rank
    
    # Merge categories/tags
    if javdb_metadata.categories:
        existing_tags = set(merged.get('tags', []))
        javdb_categories = set(javdb_metadata.categories)
        merged['tags'] = list(existing_tags | javdb_categories)
        print(f"     - Total tags: {len(merged['tags'])}")
    
    # Add cover URLs (both regular and large)
    if javdb_metadata.cover_url:
        merged['cover_url_javdb'] = javdb_metadata.cover_url
        print(f"     - Cover URL: Yes")
    
    if hasattr(javdb_metadata, 'cover_url_large') and javdb_metadata.cover_url_large:
        merged['cover_url_large'] = javdb_metadata.cover_url_large
    
    # Add description if available
    if javdb_metadata.description:
        merged['description'] = javdb_metadata.description
    
    # Prefer JAVDatabase title_jp if available and JavaGG doesn't have it
    if hasattr(javdb_metadata, 'title_jp') and javdb_metadata.title_jp and not merged.get('title_japanese'):
        merged['title_japanese'] = javdb_metadata.title_jp
    
    return merged


# Example usage:
"""
from javgg_scraper import JavaGGScraper
from javdb_enrichment import enrich_with_javdb

scraper = JavaGGScraper(headless=False)
video_data = scraper.scrape_video("https://javgg.net/jav/sone-572/")

if video_data:
    # Convert to dict
    video_dict = video_data.__dict__
    
    # Enrich with JAVDatabase (fast mode - skip actress images)
    enriched_data = enrich_with_javdb(video_dict, headless=True, skip_actress_images=True)
    
    # Or with actress images (slower)
    # enriched_data = enrich_with_javdb(video_dict, headless=True, skip_actress_images=False)
    
    # Save enriched data
    import json
    with open(f"{video_data.code}_enriched.json", 'w', encoding='utf-8') as f:
        json.dump(enriched_data, f, indent=2, ensure_ascii=False)
"""
