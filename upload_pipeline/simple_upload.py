"""
Simple upload script for SeekStreaming
Automatically gets correct video ID and saves to database
"""
import os
import sys
from dotenv import load_dotenv
from seekstreaming_uploader import SeekstreamingUploader
from video_urls_manager import VideoURLManager

load_dotenv()

def upload_video(video_path, title=None):
    """Upload video and save to database"""
    
    API_KEY = os.getenv('SEEKSTREAMING_API_KEY')
    
    if not API_KEY:
        print("✗ SEEKSTREAMING_API_KEY not found in .env file")
        return False
    
    if not os.path.exists(video_path):
        print(f"✗ Video file not found: {video_path}")
        return False
    
    print("=" * 70)
    print("SEEKSTREAMING VIDEO UPLOADER")
    print("=" * 70)
    print()
    
    # Upload
    uploader = SeekstreamingUploader(API_KEY)
    result = uploader.upload(video_path, title)
    
    if not result.get('success'):
        print(f"\n✗ Upload failed: {result.get('error')}")
        return False
    
    # Save to database
    file_name = os.path.basename(video_path)
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    video_title = title or os.path.splitext(file_name)[0]
    
    video_info = {
        'title': video_title,
        'filename': file_name,
        'file_size_mb': round(file_size_mb, 2)
    }
    
    url_manager = VideoURLManager()
    url_manager.add_video(video_info, result)
    
    print()
    print("=" * 70)
    print("✓ UPLOAD COMPLETE!")
    print("=" * 70)
    print(f"\nVideo Title: {video_title}")
    print(f"Video ID: {result['video_id']}")
    print(f"\nPlayer URL: {result['all_urls']['video_player']}")
    print(f"Embed Code: {result['all_urls']['embed_code']}")
    print(f"\n✓ Saved to database: database/seekstreaming_host.json")
    print()
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_upload.py <video_path> [title]")
        print("\nExamples:")
        print("  python simple_upload.py ../test.mp4")
        print("  python simple_upload.py ../video.mp4 \"My Video Title\"")
        print("  python simple_upload.py C:\\Videos\\movie.mp4 \"Movie Title\"")
        sys.exit(1)
    
    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = upload_video(video_path, title)
    sys.exit(0 if success else 1)
