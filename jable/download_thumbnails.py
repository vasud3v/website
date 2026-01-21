#!/usr/bin/env python3
"""
Download and save video thumbnails
"""
import os
import requests
from pathlib import Path

THUMBNAIL_DIR = "database/thumbnails"

def download_thumbnail(thumbnail_url, video_code):
    """
    Download thumbnail for a video
    
    Args:
        thumbnail_url: URL of the thumbnail image
        video_code: Video code (e.g., "MIRD-269")
        
    Returns:
        Local file path if successful, None if failed
    """
    if not thumbnail_url or not video_code:
        return None
    
    try:
        # Create thumbnails directory
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)
        
        # Determine file extension from URL
        ext = '.jpg'
        if '.png' in thumbnail_url.lower():
            ext = '.png'
        elif '.webp' in thumbnail_url.lower():
            ext = '.webp'
        
        # Local file path
        local_path = os.path.join(THUMBNAIL_DIR, f"{video_code}{ext}")
        
        # Skip if already exists
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
            if size > 0:
                print(f"   [Thumbnail] Already exists: {local_path} ({size} bytes)")
                return local_path
        
        # Download
        print(f"   [Thumbnail] Downloading from {thumbnail_url[:60]}...")
        response = requests.get(thumbnail_url, timeout=30, headers={
            'Referer': 'https://jable.tv/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Save
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        size = os.path.getsize(local_path)
        print(f"   [Thumbnail] ✅ Saved: {local_path} ({size} bytes)")
        
        return local_path
        
    except Exception as e:
        print(f"   [Thumbnail] ⚠️ Failed to download: {e}")
        return None

def get_thumbnail_path(video_code):
    """Get local path for a thumbnail if it exists"""
    for ext in ['.jpg', '.png', '.webp']:
        path = os.path.join(THUMBNAIL_DIR, f"{video_code}{ext}")
        if os.path.exists(path):
            return path
    return None

if __name__ == "__main__":
    # Test
    test_url = "https://example.com/thumbnail.jpg"
    test_code = "TEST-123"
    
    result = download_thumbnail(test_url, test_code)
    print(f"\nResult: {result}")
