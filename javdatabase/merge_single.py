"""
Merge single video data from Jable/JavaGG and JAVDatabase
Priority: JAVDatabase metadata first, JavaGG as fallback
"""

def merge_and_validate(source_data: dict, javdb_data: dict = None) -> dict:
    """
    Merge source video data (from Jable/JavaGG) with JAVDatabase data
    
    PRIORITY LOGIC:
    - If JAVDatabase has the video: Use JAVDatabase metadata (primary)
    - If field is empty in JAVDatabase: Use JavaGG as fallback
    - JavaGG only provides: embed_url, m3u8_url, thumbnail_url, hosting_urls
    
    Args:
        source_data: Video data from Jable or JavaGG scraper
        javdb_data: Video data from JAVDatabase scraper (optional)
    
    Returns:
        dict: Merged video data with clean structure
    """
    
    # If no JAVDatabase data, return source data only
    if not javdb_data:
        merged = source_data.copy()
        merged['javdb_available'] = False
        return merged
    
    # Start with JAVDatabase as primary source
    merged = {
        'code': source_data.get('code'),
        'source': source_data.get('source', 'javgg'),
        'scraped_at': source_data.get('scraped_at'),
        'processed_at': source_data.get('processed_at'),
    }
    
    # Mark as having JAVDatabase data
    merged['javdb_available'] = True
    merged['javdb_url'] = javdb_data.get('source_url', '')
    
    # === TITLE (prefer JAVDatabase, but validate it's not just the code) ===
    javdb_title = javdb_data.get('title', '')
    source_title = source_data.get('title', '')
    code = source_data.get('code', '')
    
    # Use JAVDatabase title if it's not empty and not just the code
    if javdb_title and javdb_title != code:
        merged['title'] = javdb_title
    # Otherwise use source title if it's not just the code
    elif source_title and source_title != code:
        merged['title'] = source_title
    # Last resort: use code (but this shouldn't happen)
    else:
        merged['title'] = code
    
    # Japanese title from JAVDatabase
    merged['title_japanese'] = javdb_data.get('title_jp', '') or source_data.get('title_japanese', '')
    
    # === VIDEO URLS (from JavaGG only) ===
    merged['embed_url'] = source_data.get('embed_url', '')
    merged['m3u8_url'] = source_data.get('m3u8_url', '')
    
    # === CAST/ACTRESSES (from JAVDatabase) ===
    if javdb_data.get('cast'):
        merged['cast'] = javdb_data['cast']
        
        # Extract actress names for quick access
        actresses = []
        for actress in javdb_data['cast']:
            if isinstance(actress, dict):
                name = actress.get('actress_name') or actress.get('name')
                if name and name not in actresses:
                    actresses.append(name)
        merged['actresses'] = actresses
    else:
        merged['cast'] = []
        merged['actresses'] = []
    
    # === SCREENSHOTS (from JAVDatabase) ===
    merged['screenshots'] = javdb_data.get('screenshots', [])
    
    # === STUDIO (prefer JAVDatabase) ===
    merged['studio'] = javdb_data.get('studio') or source_data.get('studio', '')
    
    # === DIRECTOR (from JAVDatabase) - only include if has value ===
    director = javdb_data.get('director')
    if director:
        merged['director'] = director
    
    # === LABEL (from JAVDatabase) - only include if has value ===
    label = javdb_data.get('label')
    if label:
        merged['label'] = label
    
    # === SERIES (from JAVDatabase) - only include if has value ===
    series = javdb_data.get('series')
    if series:
        merged['series'] = series
    
    # === RELEASE DATE (prefer JAVDatabase) ===
    release_date = javdb_data.get('release_date') or source_data.get('release_date', '')
    if release_date:
        merged['release_date'] = release_date
        
        # Extract year
        if len(release_date) >= 4:
            merged['release_year'] = release_date[:4]
    
    # === RUNTIME (from JAVDatabase) ===
    runtime_minutes = javdb_data.get('runtime_minutes', 0)
    if runtime_minutes:
        merged['runtime'] = f"{runtime_minutes} min"
    
    # === COVER IMAGE (prefer JAVDatabase high quality) ===
    merged['cover_url'] = javdb_data.get('cover_url') or source_data.get('thumbnail_url', '')
    
    # === ALTERNATIVE COVER (DMM/FANZA) ===
    cover_url_dmm = javdb_data.get('cover_url_dmm')
    if cover_url_dmm:
        merged['cover_url_dmm'] = cover_url_dmm
    
    # === GENRES (from JAVDatabase only) ===
    javdb_genres = javdb_data.get('genres', [])
    if javdb_genres:
        merged['genres'] = javdb_genres
    
    # === RATING (from JAVDatabase) ===
    if javdb_data.get('rating'):
        merged['rating'] = javdb_data['rating']
    
    if javdb_data.get('rating_count'):
        merged['rating_count'] = javdb_data['rating_count']
    
    # === HOSTING URLS (from JavaGG/upload pipeline) ===
    hosting = source_data.get('hosting', {})
    if hosting:
        merged['hosting'] = hosting
    
    # === UPLOAD TIMESTAMP ===
    uploaded_at = source_data.get('uploaded_at')
    if uploaded_at:
        merged['uploaded_at'] = uploaded_at
    
    return merged
