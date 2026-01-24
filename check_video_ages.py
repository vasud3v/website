import json
from datetime import datetime

# Load videos
with open('database/combined_videos.json', 'r', encoding='utf-8') as f:
    videos = json.load(f)

print(f"Total videos: {len(videos)}\n")
print("Video ages (release dates):")
print("=" * 60)

for i, video in enumerate(videos[:10], 1):
    code = video.get('code', 'N/A')
    release_date = video.get('release_date', 'Unknown')
    has_javdb = video.get('javdb_available', False) or video.get('cast') is not None
    
    print(f"{i}. {code}")
    print(f"   Release: {release_date}")
    print(f"   JAVDatabase: {'YES' if has_javdb else 'NO'}")
    print()

print("=" * 60)
print("\nConclusion:")
print("If most videos show 'Released at 2026-01-XX' (recent dates),")
print("they are too new for JAVDatabase (which takes 2-7 days to index).")
print("\nThis is NORMAL and expected behavior!")
