"""
Merge single video data from Jable and JAVDatabase
Handles all edge cases and data inconsistencies
"""

import json
from typing import Optional


def normalize_views_likes(value: str) -> str:
    """Remove spaces from views/likes"""
    if not value:
        return "0"
    return str(value).replace(" ", "").replace(",", "")


def merge_single_video(jable_data: dict, javdb_data: Optional[dict]) -> dict:
    """
    Merge Jable and JAVDatabase data for single video
    
    Args:
        jable_data: Data from Jable scraper (required)
        javdb_data: Data from JAVDatabase scraper (optional)
    
    Returns:
        dict: Merged video data
    """
    
    # Start with code (always from Jable)
    merged = {
        "code": jable_data.get("code", "").upper()
    }
    
    # Title: Prefer JAVDatabase (more professional), fallback to Jable
    if javdb_data and javdb_data.get("title"):
        merged["title"] = javdb_data["title"]
    else:
        merged["title"] = jable_data.get("title", "")
    
    # Japanese title (only from JAVDatabase)
    merged["title_jp"] = javdb_data.get("title_jp") if javdb_data else None
    
    # Media URLs
    merged["cover_url"] = javdb_data.get("cover_url") if javdb_data else jable_data.get("thumbnail_url")
    merged["screenshots"] = javdb_data.get("screenshots", []) if javdb_data else []
    
    # Cast (only from JAVDatabase, empty array if not available)
    merged["cast"] = javdb_data.get("cast", []) if javdb_data else []
    
    # Video Info
    merged["release_date"] = javdb_data.get("release_date") if javdb_data else None
    merged["duration"] = jable_data.get("duration")
    merged["runtime_minutes"] = javdb_data.get("runtime_minutes") if javdb_data else None
    merged["hd_quality"] = jable_data.get("hd_quality", False)
    merged["file_size"] = jable_data.get("file_size")
    
    # Production
    merged["studio"] = javdb_data.get("studio") if javdb_data else None
    merged["director"] = javdb_data.get("director") if javdb_data else None
    merged["label"] = javdb_data.get("label") if javdb_data else None
    merged["series"] = javdb_data.get("series") if javdb_data else None
    
    # Categories & Tags
    merged["categories"] = jable_data.get("categories", [])
    merged["genres"] = javdb_data.get("genres", []) if javdb_data else []
    merged["tags"] = jable_data.get("tags", [])
    
    # Social & Stats
    merged["views"] = normalize_views_likes(jable_data.get("views", "0"))
    merged["likes"] = normalize_views_likes(jable_data.get("likes", "0"))
    merged["rating"] = javdb_data.get("rating") if javdb_data else None
    merged["rating_count"] = javdb_data.get("rating_count") if javdb_data else None
    
    # Streaming (always from Jable)
    # Handle both old format (single service object) and new format (dict of services)
    hosting_data = jable_data.get("hosting", {})
    if hosting_data:
        # Check if it's old format (has 'service' key) or new format (dict of services)
        if isinstance(hosting_data, dict) and 'service' in hosting_data:
            # Old format: convert to new format
            service_name = hosting_data.get('service', 'unknown').lower()
            merged["hosting"] = {
                service_name: {
                    'embed_url': hosting_data.get('embed_url', ''),
                    'watch_url': hosting_data.get('watch_url', ''),
                    'download_url': hosting_data.get('download_url', ''),
                    'direct_url': hosting_data.get('direct_url', ''),
                    'api_url': hosting_data.get('api_url', ''),
                    'filecode': hosting_data.get('filecode', ''),
                    'upload_time': hosting_data.get('time', 0),
                    'uploaded_at': hosting_data.get('uploaded_at', '')
                }
            }
        else:
            # New format: use as-is
            merged["hosting"] = hosting_data
    else:
        merged["hosting"] = {}
    
    # Sources
    merged["source_javdb"] = javdb_data.get("source_url") if javdb_data else None
    merged["source_jable"] = jable_data.get("source_url")
    
    # Metadata
    merged["javdb_available"] = bool(javdb_data)
    merged["scraped_at"] = javdb_data.get("scraped_at") if javdb_data else None
    
    return merged


def merge_and_validate(jable_data: dict, javdb_data: Optional[dict]) -> dict:
    """
    Merge and validate data
    
    Returns:
        dict: Validated merged data
    """
    merged = merge_single_video(jable_data, javdb_data)
    
    # Validation
    if not merged.get("code"):
        raise ValueError("Video code is required")
    
    if not merged.get("title"):
        raise ValueError("Video title is required")
    
    # Hosting is optional - video can exist without hosting info
    # This allows JAVDatabase-only entries or entries pending upload
    if not merged.get("hosting"):
        merged["hosting"] = {}
    
    return merged


if __name__ == "__main__":
    # Test with sample data
    jable_sample = {
        "code": "MIDA-486",
        "title": "Basic title",
        "duration": "2:22:45",
        "views": "165 168",
        "likes": "1152",
        "categories": ["Sex Only"],
        "tags": ["Girl", "Big tits"],
        "hosting": {"streamwish": {"watch_url": "https://example.com"}},
        "source_url": "https://jable.tv/videos/mida-486/"
    }
    
    javdb_sample = {
        "code": "MIDA-486",
        "title": "Professional title",
        "cover_url": "https://example.com/cover.jpg",
        "screenshots": ["https://example.com/1.jpg"],
        "cast": [{"actress_name": "Test"}],
        "studio": "MOODYZ",
        "genres": ["Big Tits"],
        "source_url": "https://javdatabase.com/movies/mida-486/"
    }
    
    result = merge_and_validate(jable_sample, javdb_sample)
    print(json.dumps(result, indent=2, ensure_ascii=False))
