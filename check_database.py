"""Check current database status"""
import json

with open('database/combined_videos.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total videos: {len(data)}")
print(f"\nFirst 10 video codes:")
for i, video in enumerate(data[:10], 1):
    code = video.get('code', 'NO CODE')
    javdb = video.get('javdb_available', False)
    cast_count = len(video.get('cast', []))
    screenshots = len(video.get('screenshots', []))
    print(f"{i}. {code} - JAVDatabase: {'✅' if javdb else '❌'} - Cast: {cast_count} - Screenshots: {screenshots}")

# Count videos without JAVDatabase data
without_javdb = [v for v in data if not v.get('javdb_available')]
print(f"\nVideos without JAVDatabase data: {len(without_javdb)}")
print(f"Videos with JAVDatabase data: {len(data) - len(without_javdb)}")
