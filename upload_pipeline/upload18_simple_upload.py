"""
Simple upload script for Upload18
Automatically saves to database
"""
import os
import sys
from dotenv import load_dotenv
from upload18_uploader import Upload18Uploader
import json
from datetime import datetime

load_dotenv()

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

def upload_video(video_path, title=None):
    """Upload video and save to database"""
    
    EMAIL = os.getenv('UPLOAD18_EMAIL')
    USERNAME = os.getenv('UPLOAD18_USERNAME')
    PASSWORD = os.getenv('UPLOAD18_PASSWORD')
    API_KEY = os.getenv('UPLOAD18_API_KEY')
    
    if not all([EMAIL, USERNAME, PASSWORD, API_KEY]):
        print("✗ Upload18 credentials not found in .env file")
        print("  Required: UPLOAD18_EMAIL, UPLOAD18_USERNAME, UPLOAD18_PASSWORD, UPLOAD18_API_KEY")
        return False
    
    if not os.path.exists(video_path):
        print(f"✗ Video file not found: {video_path}")
        return False
    
    print("=" * 70)
    print("UPLOAD18 VIDEO UPLOADER")
    print("=" * 70)
    print()
    
    # Upload
    uploader = Upload18Uploader(EMAIL, USERNAME, PASSWORD, API_KEY)
    result = uploader.upload(video_path, title)
    
    if not result.get('success'):
        print(f"\n✗ Upload failed: {result.get('error')}")
        return False
    
    # Save to database
    file_name = os.path.basename(video_path)
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    video_title = title or os.path.splitext(file_name)[0]
    
    db = load_database()
    
    new_video = {
        "id": len(db['videos']) + 1,
        "title": video_title,
        "filename": file_name,
        "file_size_mb": round(file_size_mb, 2),
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "vid": result['vid'],
        "did": result['did'],
        "video_player": result['url'],
        "video_downloader": result['url'],
        "embed_code": f'<iframe width="100%" height="100%" src="{result["url"]}" frameborder="0" allowfullscreen></iframe>'
    }
    
    db['videos'].append(new_video)
    db['stats']['total_videos'] = len(db['videos'])
    db['stats']['total_size_mb'] = round(sum(v.get('file_size_mb', 0) for v in db['videos']), 2)
    
    save_database(db)
    
    print()
    print("=" * 70)
    print("✓ UPLOAD COMPLETE!")
    print("=" * 70)
    print(f"\nVideo Title: {video_title}")
    print(f"Video ID: {result['vid']}")
    print(f"DID: {result['did']}")
    print(f"\nPlayer URL: {result['embed_url']}")
    print(f"Download URL: {result['url']}")
    print(f"Embed Code: {new_video['embed_code']}")
    print(f"\n✓ Saved to database: {DATABASE_PATH}")
    print()
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload18_simple_upload.py <video_path> [title]")
        print("\nExamples:")
        print("  python upload18_simple_upload.py ../test.mp4")
        print("  python upload18_simple_upload.py ../video.mp4 \"My Video Title\"")
        sys.exit(1)
    
    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = upload_video(video_path, title)
    sys.exit(0 if success else 1)
