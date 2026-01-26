"""
Manually update Upload18 video with VID from dashboard
"""
import os
import sys
import json
from datetime import datetime

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

def update_video(did, vid):
    """Update video with VID"""
    db = load_database()
    
    # Find video by DID
    found = False
    for video in db['videos']:
        if str(video.get('did')) == str(did) or str(video.get('vid')) == str(did):
            # Update with new VID
            video['vid'] = vid
            video['video_player'] = f"https://upload18.com/play/index/{vid}"
            video['video_downloader'] = f"https://upload18.com/play/index/{vid}"
            video['embed_code'] = f'<iframe width="100%" height="100%" src="https://upload18.com/play/index/{vid}" frameborder="0" allowfullscreen></iframe>'
            
            print(f"✓ Updated video: {video['title']}")
            print(f"  DID: {did}")
            print(f"  VID: {vid}")
            print(f"  Player URL: {video['video_player']}")
            print(f"  Embed Code: {video['embed_code']}")
            
            found = True
            break
    
    if not found:
        print(f"✗ Video with DID {did} not found in database")
        return False
    
    # Save database
    save_database(db)
    print(f"\n✓ Database updated: {DATABASE_PATH}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload18_update_vid.py <did> <vid>")
        print("\nExample:")
        print("  python upload18_update_vid.py 1042970 ac5447863877")
        print("\nGet the VID from your Upload18 dashboard after processing completes.")
        sys.exit(1)
    
    did = sys.argv[1]
    vid = sys.argv[2]
    
    print("=" * 70)
    print("UPLOAD18 VID UPDATER")
    print("=" * 70)
    print()
    
    success = update_video(did, vid)
    sys.exit(0 if success else 1)
