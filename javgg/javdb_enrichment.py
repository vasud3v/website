"""
JAVDatabase Enrichment for JavaGG Scraper
Enriches JavaGG video metadata with additional data from JAVDatabase.com
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict

# Import JAVDatabase scraper
javdb_path = Path(__file__).parent.parent / "javdatabase"
sys.path.insert(0, str(javdb_path))

try:
    from javdb_scraper import JAVDatabaseScraper
    JAVDB_AVAILABLE = True
    print("✓ JAVDatabase scraper available")
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
    
    # CRITICAL FIX: Extract actual video code from suffixes like "-REDUCE-MOSAIC"
    # Examples:
    #   "APAK-323-REDUCE-MOSAIC" -> "APAK-323"
    #   "FC2-PPV-4838212" -> "FC2-PPV-4838212" (keep as is)
    #   "012926-001-CARIB" -> "012926-001-CARIB" (keep as is)
    
    actual_code = video_code
    
    # Remove common suffixes that are not part of the actual video code
    suffixes_to_remove = [
        '-REDUCE-MOSAIC',
        '-REDUCED-MOSAIC',
        '-UNCENSORED',
        '-LEAKED',
        '-UNCEN',
        ' REDUCE MOSAIC',
        ' REDUCED MOSAIC',
        ' UNCENSORED'
    ]
    
    for suffix in suffixes_to_remove:
        if actual_code.endswith(suffix):
            actual_code = actual_code[:-len(suffix)]
            print(f"  📝 Cleaned code: {video_code} -> {actual_code}")
            break
    
    print(f"\n{'='*70}")
    print(f"🔍 JAVDatabase Enrichment: {actual_code}")
    print(f"{'='*70}")
    
    # Try JAVDatabase first for all videos
    # If not found, will fall back to enhanced JavaGG scraping
    
    try:
        print(f"  📊 Fetching metadata from JAVDatabase...")
        
        # Use JAVDatabase scraper with the cleaned code
        temp_scraper = JAVDatabaseScraper(headless=headless)
        try:
            javdb_metadata = temp_scraper.scrape_video_metadata(actual_code)
        finally:
            try:
                temp_scraper.close()
            except:
                pass
        
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
            print(f"     Falling back to enhanced JavaGG scraping...")
            
            # Fallback: Scrape enhanced metadata from JavaGG
            enhanced_data = scrape_enhanced_from_javgg(javgg_data)
            
            print(f"{'='*70}\n")
            
            return enhanced_data
            
    except Exception as e:
        print(f"  ❌ JAVDatabase enrichment failed: {str(e)[:100]}")
        print(f"     Using JavaGG data only")
        print(f"{'='*70}\n")
        
        javgg_data['javdb_available'] = False
        javgg_data['javdb_error'] = str(e)[:200]
        return javgg_data


def scrape_enhanced_from_javgg(javgg_data: dict) -> dict:
    """
    Scrape enhanced metadata from JavaGG when JAVDatabase doesn't have the video.
    This extracts categories, tags, and post_date from the JavaGG page.
    
    Args:
        javgg_data: Basic video data from JavaGG scraper
    
    Returns:
        dict: Enhanced video data with additional metadata from JavaGG
    """
    video_code = javgg_data.get("code", "")
    source_url = javgg_data.get("source_url", "")
    
    if not source_url:
        print(f"  ⚠️  No source URL available for enhanced scraping")
        javgg_data['javdb_available'] = False
        javgg_data['javdb_not_found'] = True
        return javgg_data
    
    try:
        print(f"  🔍 Scraping enhanced metadata from JavaGG...")
        
        # Import scraper
        from javgg_scraper import JavaGGScraper
        
        # Create temporary scraper instance
        temp_scraper = JavaGGScraper(headless=True)
        
        try:
            # Re-scrape the video to get enhanced metadata
            enhanced_video_data = temp_scraper.scrape_video(source_url)
            
            if enhanced_video_data:
                # Merge enhanced data
                if enhanced_video_data.categories:
                    javgg_data['categories'] = enhanced_video_data.categories
                    print(f"     - Categories: {len(enhanced_video_data.categories)}")
                
                if enhanced_video_data.tags:
                    javgg_data['tags'] = enhanced_video_data.tags
                    print(f"     - Tags: {len(enhanced_video_data.tags)}")
                
                if enhanced_video_data.release_date:
                    javgg_data['release_date'] = enhanced_video_data.release_date
                    javgg_data['release_date_formatted'] = enhanced_video_data.release_date_formatted
                    print(f"     - Release Date: {enhanced_video_data.release_date}")
                
                # Update other fields if they're better in the new scrape
                if enhanced_video_data.duration and not javgg_data.get('duration'):
                    javgg_data['duration'] = enhanced_video_data.duration
                    javgg_data['duration_minutes'] = enhanced_video_data.duration_minutes
                
                if enhanced_video_data.models and not javgg_data.get('models'):
                    javgg_data['models'] = enhanced_video_data.models
                
                if enhanced_video_data.studio and not javgg_data.get('studio'):
                    javgg_data['studio'] = enhanced_video_data.studio
                    javgg_data['studio_japanese'] = enhanced_video_data.studio_japanese
                
                if enhanced_video_data.director and not javgg_data.get('director'):
                    javgg_data['director'] = enhanced_video_data.director
                
                if enhanced_video_data.series and not javgg_data.get('series'):
                    javgg_data['series'] = enhanced_video_data.series
                
                print(f"  ✅ Enhanced metadata scraped from JavaGG")
            else:
                print(f"  ⚠️  Could not re-scrape video from JavaGG")
        
        finally:
            try:
                temp_scraper.close()
            except:
                pass
        
        javgg_data['javdb_available'] = False
        javgg_data['javdb_not_found'] = True
        javgg_data['enhanced_from_javgg'] = True
        
        return javgg_data
        
    except Exception as e:
        print(f"  ⚠️  Enhanced JavaGG scraping failed: {str(e)[:100]}")
        javgg_data['javdb_available'] = False
        javgg_data['javdb_not_found'] = True
        return javgg_data


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
        # Remove duplicates while preserving order
        unique_actresses = []
        seen = set()
        for actress in javdb_metadata.actresses:
            if actress not in seen:
                unique_actresses.append(actress)
                seen.add(actress)
        merged['actresses'] = unique_actresses
        merged['models'] = unique_actresses  # Also populate models field
        print(f"     - Merged actresses: {len(unique_actresses)}")
    
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
        # Don't overwrite studio_japanese if JavaGG already has it with actual Japanese
        # Only set it if empty or if it's just English
        if not merged.get('studio_japanese') or merged.get('studio_japanese') == merged.get('studio'):
            # JAVDatabase doesn't provide Japanese studio names, keep English
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
    
    # Merge release date and formatted date
    if hasattr(javdb_metadata, 'release_date') and javdb_metadata.release_date:
        merged['release_date'] = javdb_metadata.release_date
        merged['release_year'] = javdb_metadata.release_date[:4]
        # Format as "Month Day, Year"
        try:
            from datetime import datetime
            date_obj = datetime.strptime(javdb_metadata.release_date, '%Y-%m-%d')
            merged['release_date_formatted'] = date_obj.strftime('%B %d, %Y')
            print(f"     - Release Date: {merged['release_date_formatted']}")
        except:
            merged['release_date_formatted'] = javdb_metadata.release_date
    elif hasattr(javdb_metadata, 'release_year') and javdb_metadata.release_year:
        merged['release_year'] = javdb_metadata.release_year
    
    # Merge runtime/duration
    if hasattr(javdb_metadata, 'runtime') and javdb_metadata.runtime:
        merged['runtime'] = javdb_metadata.runtime
        merged['duration'] = javdb_metadata.runtime
        # Extract minutes from runtime string (e.g., "145 min" -> 145)
        try:
            import re
            minutes_match = re.search(r'(\d+)', javdb_metadata.runtime)
            if minutes_match:
                merged['duration_minutes'] = int(minutes_match.group(1))
                print(f"     - Duration: {merged['duration_minutes']} minutes")
        except:
            pass
    elif hasattr(javdb_metadata, 'runtime_minutes') and javdb_metadata.runtime_minutes:
        merged['runtime_minutes'] = javdb_metadata.runtime_minutes
        merged['duration_minutes'] = javdb_metadata.runtime_minutes
        merged['duration'] = f"{javdb_metadata.runtime_minutes} min"
    
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
        existing_categories = set(merged.get('categories', []))
        javdb_categories = set(javdb_metadata.categories)
        
        # Tags: Merge all sources
        merged['tags'] = list(existing_tags | existing_categories | javdb_categories)
        
        # Categories: Only use JAVDatabase categories (more accurate)
        merged['categories'] = list(javdb_categories)
        
        print(f"     - Tags: {len(merged['tags'])}, Categories: {len(merged['categories'])}")
    
    # Add cover URLs (both regular and large)
    if javdb_metadata.cover_url:
        merged['cover_url_javdb'] = javdb_metadata.cover_url
        print(f"     - Cover URL: Yes")
    
    if hasattr(javdb_metadata, 'cover_url_large') and javdb_metadata.cover_url_large:
        merged['cover_url_large'] = javdb_metadata.cover_url_large
    
    # Add description if available
    if javdb_metadata.description:
        merged['description'] = javdb_metadata.description
        print(f"     - Description: {len(javdb_metadata.description)} chars")
    
    # Prefer JAVDatabase title_jp if available
    # Note: JAVDatabase doesn't provide Japanese titles, only English
    # Keep JavaGG's title_japanese if it has actual Japanese characters
    if hasattr(javdb_metadata, 'title_jp') and javdb_metadata.title_jp:
        # Check if current title_japanese is empty or just English
        current_title_jp = merged.get('title_japanese', '')
        has_japanese = any('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FFF' for c in current_title_jp)
        if not has_japanese:
            # Don't overwrite with English title from JAVDatabase
            # Keep it empty if JavaGG didn't find Japanese
            pass
    
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
