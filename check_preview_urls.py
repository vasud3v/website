#!/usr/bin/env python3
"""Check if preview_url is being saved in database"""
import json

# Load database
with open('database/combined_videos.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

# Handle both list and dict formats
if isinstance(db, dict):
    videos = db.get('videos', [])
else:
    videos = db

# Count videos with preview_url
videos_with_preview = [v for v in videos if v.get('preview_url')]

print(f"Total videos: {len(videos)}")
print(f"Videos with preview_url: {len(videos_with_preview)}")
if len(videos) > 0:
    print(f"Percentage: {len(videos_with_preview) / len(videos) * 100:.1f}%")

if videos_with_preview:
    print(f"\nSample videos with preview_url:")
    for v in videos_with_preview[:5]:
        preview_url = v.get('preview_url', '')
        if len(preview_url) > 80:
            print(f"  {v.get('code', 'N/A')}: {preview_url[:80]}...")
        else:
            print(f"  {v.get('code', 'N/A')}: {preview_url}")
else:
    print("\n⚠️ No videos have preview_url set!")
    print("This means Internet Archive uploads are not being saved to database.")
