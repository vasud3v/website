
"""
Auto download and upload - no user input required
Processes first video automatically
"""

import sys
sys.path.append('.')

from jable_scraper import JableScraper
from download_with_decrypt_v2 import HLSDownloaderV2 as HLSDownloader
import os
import json
import time
import requests
import subprocess
import shutil
import re

# Upload service selection
UPLOAD_SERVICE = "streamtape"  # Options: "streamwish", "lulustream", "streamtape"

# Import appropriate upload function
if UPLOAD_SERVICE == "streamtape":
    from simple_streamtape_upload import upload_to_streamtape as upload
elif UPLOAD_SERVICE == "lulustream":
    from lulustream_upload import upload_to_lulustream as upload
else:
    from fast_upload import upload_fast as upload

STREAMWISH_API_KEY = "31637q4gsnt23yyvd0or6"
MAX_WORKERS = 32  # Lower for decryption overhead


def sanitize_filename(filename):
    """Sanitize filename to remove invalid characters"""
    # Remove invalid filesystem characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def find_ffmpeg():
    """Find ffmpeg executable"""
    paths = [
        'ffmpeg',
        r'C:\Users\hp\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe',
        os.path.join('N_m3u8DL-RE_Beta_win-x64', 'ffmpeg.exe')
    ]
    
    for path in paths:
        try:
            result = subprocess.run([path, '-version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                return path
        except:
            continue
    return None


def convert_to_mp4(input_ts, output_mp4):
    """Convert TS to MP4 using ffmpeg"""
    print(f"   Converting {os.path.basename(input_ts)} to MP4...")
    sys.stdout.flush()
    
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("   ❌ ffmpeg not found!")
        return False
    
    # Verify input file exists
    if not os.path.exists(input_ts):
        print(f"   ❌ Input file not found: {input_ts}")
        return False
    
    input_size = os.path.getsize(input_ts) / (1024**3)
    print(f"   Input size: {input_size:.2f} GB")
    sys.stdout.flush()
    
    cmd = [
        ffmpeg,
        '-i', input_ts,
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        '-movflags', '+faststart',
        '-y',
        output_mp4
    ]
    
    try:
        print(f"   Running ffmpeg conversion...")
        sys.stdout.flush()
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0 and os.path.exists(output_mp4):
            output_size = os.path.getsize(output_mp4) / (1024**3)
            print(f"   ✅ Converted to MP4 ({output_size:.2f} GB)")
            sys.stdout.flush()
            
            # Verify with ffprobe
            ffprobe = ffmpeg.replace('ffmpeg.exe', 'ffprobe.exe')
            probe_cmd = [ffprobe, '-v', 'error', '-show_entries', 
                        'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                        output_mp4]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
            
            if probe_result.returncode == 0:
                try:
                    duration = float(probe_result.stdout.strip())
                    minutes = int(duration // 60)
                    seconds = int(duration % 60)
                    print(f"   Duration: {minutes}m {seconds}s")
                    print(f"   ✅ Video is playable!")
                    sys.stdout.flush()
                except:
                    pass
            
            # Remove TS file after successful conversion
            try:
                os.remove(input_ts)
                print(f"   🗑️ Removed temporary TS file")
                sys.stdout.flush()
            except:
                pass
            
            return True
        else:
            print(f"   ❌ Conversion failed!")
            if result.stderr:
                print(f"   Error: {result.stderr[:300]}")
            sys.stdout.flush()
            return False
            
    except subprocess.TimeoutExpired:
        print(f"   ❌ Conversion timed out (>10 minutes)")
        sys.stdout.flush()
        return False
    except Exception as e:
        print(f"   ❌ Conversion error: {e}")
        sys.stdout.flush()
        return False


# Main
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║        🚀 AUTO DOWNLOAD & UPLOAD 🚀                     ║
╚══════════════════════════════════════════════════════════╝
""")

    # Load videos
    with open('database/videos.json', 'r', encoding='utf-8') as f:
        videos = json.load(f)

    # Process first video automatically
    video = videos[0]
    print(f"Processing: {video['code']} - {video['title']}")
    print("="*60)

    scraper = JableScraper(headless=True)

    try:
        # Scrape
        print(f"\n📋 Scraping...")
        video_data = scraper.scrape_video(video['source_url'])
        
        if not video_data:
            print("❌ Scraping failed")
            exit(1)
        
        print(f"✅ Got M3U8 URL")
        
        # Download with decryption support
        output_ts = f"temp_downloads/{sanitize_filename(video_data.code)}.ts"
        output = f"temp_downloads/{sanitize_filename(video_data.code)}.mp4"
        os.makedirs("temp_downloads", exist_ok=True)
        
        downloader = HLSDownloader(MAX_WORKERS)
        if not downloader.download(video_data.m3u8_url, output_ts, video_data.code):
            print("❌ Download failed")
            exit(1)
        
        # Convert TS to MP4
        print(f"\n🔄 Converting to MP4...")
        if not convert_to_mp4(output_ts, output):
            print("❌ Conversion failed")
            exit(1)
        
        # Upload
        result = upload(output, video_data.code, video_data.title)
        if not result.get('success'):
            print("❌ Upload failed")
            exit(1)
        
        # Save to database
        print(f"\n💾 Saving to database...")
        try:
            with open('videos_complete.json', 'r', encoding='utf-8') as f:
                all_videos = json.load(f)
        except:
            all_videos = []
        
        video_complete = {
            'code': video_data.code,
            'title': video_data.title,
            'streamwish_embed': result['embed_url'],
            'streamwish_watch': result['watch_url'],
            'streamwish_filecode': result['filecode'],
            'thumbnail_url': video_data.thumbnail_url,
            'duration': video_data.duration,
            'views': video_data.views,
            'likes': video_data.likes,
            'release_date': video_data.release_date,
            'upload_time': video_data.upload_time,
            'hd_quality': video_data.hd_quality,
            'categories': video_data.categories,
            'models': video_data.models,
            'tags': video_data.tags,
            'preview_images': video_data.preview_images,
            'source_url': video_data.source_url,
            'uploaded_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        all_videos.append(video_complete)
        
        with open('videos_complete.json', 'w', encoding='utf-8') as f:
            json.dump(all_videos, f, indent=2, ensure_ascii=False)
        
        # Cleanup
        try:
            os.remove(output)
        except:
            pass
        
        print(f"\n{'='*60}")
        print(f"✅ SUCCESS!")
        print(f"{'='*60}")
        print(f"\n📺 Embed: {result['embed_url']}")
        print(f"🔗 Watch: {result['watch_url']}")
        
    finally:
        scraper.close()
