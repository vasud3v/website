"""
Upload videos with validation
Only uploads videos that pass integrity checks
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_manager import db_manager

# Import uploaders
from seekstreaming_uploader import SeekstreamingUploader
from streamtape_uploader import StreamtapeUploader
from turboviplay_uploader import TurboviplayUploader
from doodstream_uploader import DoodStreamUploader

from dotenv import load_dotenv
load_dotenv()


def validate_video(video_path):
    """Validate video before upload"""
    try:
        if not os.path.exists(video_path):
            return False, "File not found"
        
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        
        if size_mb < 10:
            return False, f"File too small: {size_mb:.2f} MB"
        
        # Use ffprobe
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_format',
            '-show_streams',
            '-of', 'json',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return False, f"ffprobe failed"
        
        data = json.loads(result.stdout)
        format_info = data.get('format', {})
        streams = data.get('streams', [])
        
        # Check format
        format_name = format_info.get('format_name', '')
        if 'png' in format_name.lower() or 'image' in format_name.lower():
            return False, f"Invalid format: {format_name}"
        
        # Check video stream
        video_streams = [s for s in streams if s.get('codec_type') == 'video']
        if not video_streams:
            return False, "No video stream"
        
        codec = video_streams[0].get('codec_name', '')
        if codec.lower() in ['png', 'jpg', 'jpeg']:
            return False, f"Invalid codec: {codec}"
        
        # Check duration
        duration = float(format_info.get('duration', 0))
        if duration < 30:
            return False, f"Duration too short: {duration}s"
        
        # Test decode
        test_cmd = [
            'ffmpeg',
            '-v', 'error',
            '-i', str(video_path),
            '-t', '10',
            '-f', 'null',
            '-'
        ]
        
        test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
        
        if test_result.returncode != 0 or test_result.stderr:
            return False, "Decode error"
        
        return True, f"Valid ({size_mb:.1f} MB, {duration:.0f}s, {codec})"
        
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"


def upload_video_with_validation(video_path, video_code, title=None):
    """Upload video with validation"""
    print("="*80)
    print(f"UPLOADING: {video_code}")
    print("="*80)
    
    # Validate first
    print("\n🔍 Validating video...")
    is_valid, msg = validate_video(video_path)
    
    if not is_valid:
        print(f"✗ Validation failed: {msg}")
        print("  Skipping upload - video is corrupted or incomplete")
        return False
    
    print(f"✓ Validation passed: {msg}")
    
    # Initialize uploaders (only working hosts)
    uploaders = {}
    
    # Turboviplay
    if os.getenv("TURBOVIPLAY_API_KEY"):
        uploaders['turboviplay'] = TurboviplayUploader(
            email=os.getenv("TURBOVIPLAY_EMAIL"),
            username=os.getenv("TURBOVIPLAY_USERNAME"),
            password=os.getenv("TURBOVIPLAY_PASSWORD"),
            api_key=os.getenv("TURBOVIPLAY_API_KEY")
        )
    
    # SeekStreaming
    if os.getenv("SEEKSTREAMING_API_KEY"):
        uploaders['seekstreaming'] = SeekstreamingUploader(
            api_key=os.getenv("SEEKSTREAMING_API_KEY"),
            email=os.getenv("SEEKSTREAMING_EMAIL"),
            password=os.getenv("SEEKSTREAMING_PASSWORD")
        )
    
    # StreamWish (Popular on JAV sites)
    if os.getenv("STREAMWISH_API_KEY"):
        from streamwish_uploader import StreamWishUploader
        uploaders['streamwish'] = StreamWishUploader(
            api_key=os.getenv("STREAMWISH_API_KEY")
        )
    
    # MixDrop (Popular alternative)
    if os.getenv("MIXDROP_API_KEY"):
        from mixdrop_uploader import MixDropUploader
        uploaders['mixdrop'] = MixDropUploader(
            email=os.getenv("MIXDROP_EMAIL"),
            api_key=os.getenv("MIXDROP_API_KEY")
        )
    
    if not uploaders:
        print("✗ No uploaders configured")
        return False
    
    print(f"\n📤 Uploading to {len(uploaders)} host(s)...")
    
    results = {}
    
    for host, uploader in uploaders.items():
        print(f"\n[{host.upper()}]")
        result = uploader.upload(video_path, title)
        results[host] = result
        
        if result['success']:
            print(f"  ✓ Upload successful")
        else:
            print(f"  ✗ Upload failed: {result.get('error', 'Unknown')}")
    
    # Update database
    video = db_manager.get_video_by_code(video_code)
    
    if video:
        if 'hosting' not in video:
            video['hosting'] = {}
        
        for host, result in results.items():
            if result['success']:
                video['hosting'][host] = {
                    'embed_url': result.get('embed_url', ''),
                    'download_url': result.get('url', ''),
                    'file_code': result.get('file_code', '')
                }
        
        video['uploaded_at'] = datetime.now().isoformat()
        db_manager.add_or_update_video(video)
        print(f"\n✓ Updated database")
    
    successful = sum(1 for r in results.values() if r['success'])
    print(f"\n{'='*80}")
    print(f"SUMMARY: {successful}/{len(results)} uploads successful")
    print(f"{'='*80}\n")
    
    return successful > 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_with_validation.py <video_path> <video_code> [title]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    video_code = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else video_code
    
    success = upload_video_with_validation(video_path, video_code, title)
    sys.exit(0 if success else 1)
