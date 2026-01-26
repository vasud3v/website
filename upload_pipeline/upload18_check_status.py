"""
Check Upload18 video processing status and update database with VID
"""
import os
import sys
import json
import requests
import urllib3
from dotenv import load_dotenv
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

API_KEY = os.getenv('UPLOAD18_API_KEY')
DATABASE_PATH = "../database/upload18_host.json"

def load_database():
    """Load the database"""
    if os.path.exists(DATABASE_PATH):
        with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"videos": [], "stats": {"total_videos": 0, "total_size_mb": 0}}

def save_database(data):
    """Save the database"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    with open(DATABASE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def check_videos():
    """Check all videos and update with VID"""
    print("=" * 70)
    print("UPLOAD18 VIDEO STATUS CHECKER")
    print("=" * 70)
    print()
    
    # Get video list from API
    print("Fetching video list from Upload18...")
    try:
        response = requests.get(
            f"https://upload18.com/api/myvideo",
            params={'apikey': API_KEY, 'per_page': 100},
            verify=False,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"✗ Failed to fetch videos: HTTP {response.status_code}")
            return False
        
        result = response.json()
        if result.get('status') != 'success':
            print(f"✗ API error: {result.get('msg')}")
            return False
        
        api_videos = result.get('data', [])
        print(f"✓ Found {len(api_videos)} videos on Upload18")
        print()
        
    except Exception as e:
        print(f"✗ Error fetching videos: {str(e)}")
        return False
    
    # Load local database
    db = load_database()
    updated_count = 0
    
    print("Checking videos in database...")
    print("-" * 70)
    
    for video in db['videos']:
        did = video.get('did')
        current_vid = video.get('vid', '')
        
        # Skip if already has VID
        if current_vid and current_vid != '':
            print(f"✓ Video #{video['id']}: {video['title']}")
            print(f"  VID: {current_vid} (already set)")
            continue
        
        # Find matching video by DID
        print(f"⏳ Video #{video['id']}: {video['title']}")
        print(f"  DID: {did}")
        
        # Search in API videos
        found = False
        for api_video in api_videos:
            if str(api_video.get('did')) == str(did):
                vid = api_video.get('vid')
                status = api_video.get('zt')  # 0=pending, 1=transcoding, 2=done
                
                if vid and vid != '':
                    # Update database
                    video['vid'] = vid
                    video['video_player'] = f"https://upload18.com/embed/{vid}"
                    video['video_downloader'] = f"https://upload18.com/v/{vid}"
                    video['embed_code'] = f'<iframe src="https://upload18.com/embed/{vid}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
                    
                    status_text = {0: 'Pending', 1: 'Transcoding', 2: 'Done'}.get(status, 'Unknown')
                    print(f"  ✓ VID found: {vid}")
                    print(f"  Status: {status_text}")
                    updated_count += 1
                    found = True
                else:
                    print(f"  ⚠ Video found but VID is empty (still processing)")
                    found = True
                break
        
        if not found:
            print(f"  ⚠ Video not found in API response")
        
        print()
    
    # Save updated database
    if updated_count > 0:
        save_database(db)
        print("=" * 70)
        print(f"✓ Updated {updated_count} video(s) in database")
        print(f"✓ Database saved: {DATABASE_PATH}")
        print("=" * 70)
    else:
        print("=" * 70)
        print("ℹ No updates needed")
        print("=" * 70)
    
    return True


if __name__ == "__main__":
    if not API_KEY:
        print("✗ UPLOAD18_API_KEY not found in .env file")
        sys.exit(1)
    
    success = check_videos()
    sys.exit(0 if success else 1)
