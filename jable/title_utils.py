#!/usr/bin/env python3
"""
Title Validation and Fixing Utilities
Ensures video titles are properly formatted and not just the code
"""
import re

def fix_video_title(video_data: dict) -> dict:
    """
    Fix title fields in video data
    Ensures title is not just the code
    
    Args:
        video_data: Dictionary with video information
        
    Returns:
        Fixed video_data dictionary
    """
    code = video_data.get('code', '')
    title = video_data.get('title', '')
    title_japanese = video_data.get('title_japanese', '')
    
    # Issue 1: Title is just the code or empty
    if not title or title == code:
        # Try to extract from title_japanese
        if title_japanese and ' - ' in title_japanese:
            parts = title_japanese.split(' - ', 1)
            if parts[0].strip() == code:
                # Format: "CODE - English title"
                title = parts[1].strip()
                title_japanese = ''  # No actual Japanese text
        elif title_japanese and title_japanese != code:
            # Use title_japanese as title if it's not the code
            title = title_japanese
            title_japanese = ''
    
    # Issue 2: Detect if title_japanese is actually English
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    if title_japanese and not japanese_pattern.search(title_japanese):
        # It's not Japanese, move to title if title is empty or code
        if not title or title == code:
            title = title_japanese
        title_japanese = ''
    
    # Issue 3: If title is still empty or code, use code with warning
    if not title or title == code:
        print(f"  ⚠️ Warning: No proper title found for {code}, using code as title")
        title = code
    
    # Update video data
    video_data['title'] = title
    video_data['title_japanese'] = title_japanese
    
    # Add explicit English field if not present
    if 'title_english' not in video_data:
        video_data['title_english'] = title
    
    return video_data


def validate_title(video_data: dict) -> bool:
    """
    Validate that video has a proper title
    
    Args:
        video_data: Dictionary with video information
        
    Returns:
        True if title is valid, False if title == code
    """
    code = video_data.get('code', '')
    title = video_data.get('title', '')
    
    # Title should not be empty or just the code
    if not title or title == code:
        return False
    
    return True


def extract_title_from_description(description: str, code: str) -> str:
    """
    Extract title from description field
    Common format: "CODE JAV English Title ActressName 日本語"
    
    Args:
        description: Description text
        code: Video code
        
    Returns:
        Extracted title or empty string
    """
    if not description:
        return ''
    
    # Try to extract English part after "JAV"
    jav_match = re.search(r'JAV\s+(.+?)(?=[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]|$)', description)
    if jav_match:
        title = jav_match.group(1).strip()
        # Remove actress names if present (usually at the end)
        # This is a simple heuristic
        if len(title) > 100:
            title = title[:100] + '...'
        return title
    
    # Fallback: try to extract anything after the code
    code_match = re.search(rf'{re.escape(code)}\s+(.+)', description)
    if code_match:
        return code_match.group(1).strip()
    
    return ''


# Example usage:
"""
from title_utils import fix_video_title, validate_title

# Before saving to database
video_data = fix_video_title(video_data)

# Validate
if not validate_title(video_data):
    print(f"Warning: Video {video_data['code']} has no proper title")
"""
