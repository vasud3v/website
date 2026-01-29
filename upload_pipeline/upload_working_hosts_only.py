"""
Upload to Working Hosts Only
Uses only the 4 verified working hosts: Uploady, Turboviplay, MixDrop, SeekStreaming
Skips: Streamtape (ISP blocked), Upload18 (encoding issues)
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_manager import db_manager

# Import working uploaders only
from turboviplay_uploader import TurboviplayUploader
from seekstreaming_uploader import SeekstreamingUploader
from mixdrop_uploader import MixDropUploader
from uploady_uploader import UploadyUploader

load_dotenv()


def validate_video(video_path):
    """Validate video before upload"""
    try:
        if not os.path.exists(video_path):
            return False, "File not found"
        
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        
        if size_mb < 1:
            return False, f"File too small: {size_mb:.2f} MB"
        
        # Quick validation with ffprobe
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
            return False, "ffprobe validation failed"
        
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
        if duration < 1:
            return False, f"Duration too short: {duration}s"
        
        return True, f"Valid ({size_mb:.1f} MB, {duration:.0f}s, {codec})"
        
    except Exception as e:
        return False, f"Validation error: {str(e)[:100]}"


class WorkingHostsUploader:
    def __init__(self):
        self.uploaders = {}
        self.initialize_uploaders()
    
    def initialize_uploaders(self):
        """Initialize only working uploaders"""
        print("🔧 Initializing working uploaders...")
        
        # Uploady (Priority 1 - Fastest)
        if os.getenv("UPLOADY_API_KEY"):
            self.uploaders['uploady'] = {
                'uploader': UploadyUploader(
                    email=os.getenv("UPLOADY_EMAIL"),
                    username=os.getenv("UPLOADY_USERNAME"),
                    api_key=os.getenv("UPLOADY_API_KEY")
                ),
                'priority': 1,
                'name': 'Uploady'
            }
            print("  ✓ Uploady (fastest)")
        
        # Turboviplay (Priority 2 - Reliable)
        if os.getenv("TURBOVIPLAY_API_KEY"):
            self.uploaders['turboviplay'] = {
                'uploader': TurboviplayUploader(
                    email=os.getenv("TURBOVIPLAY_EMAIL"),
                    username=os.getenv("TURBOVIPLAY_USERNAME"),
                    password=os.getenv("TURBOVIPLAY_PASSWORD"),
                    api_key=os.getenv("TURBOVIPLAY_API_KEY")
                ),
                'priority': 2,
                'name': 'Turboviplay'
            }
            print("  ✓ Turboviplay (reliable)")
        
        # MixDrop (Priority 3 - Good alternative)
        if os.getenv("MIXDROP_API_KEY"):
            self.uploaders['mixdrop'] = {
                'uploader': MixDropUploader(
                    email=os.getenv("MIXDROP_EMAIL"),
                    api_key=os.getenv("MIXDROP_API_KEY")
                ),
                'priority': 3,
                'name': 'MixDrop'
            }
            print("  ✓ MixDrop (alternative)")
        
        # SeekStreaming (Priority 4 - Backup)
        if os.getenv("SEEKSTREAMING_API_KEY"):
            self.uploaders['seekstreaming'] = {
                'uploader': SeekstreamingUploader(
                    api_key=os.getenv("SEEKSTREAMING_API_KEY"),
                    email=os.getenv("SEEKSTREAMING_EMAIL"),
                    password=os.getenv("SEEKSTREAMING_PASSWORD")
                ),
                'priority': 4,
                'name': 'SeekStreaming'
            }
            print("  ✓ SeekStreaming (backup)")
        
        if not self.uploaders:
            print("  ⚠️  No uploaders configured!")
            print("  Please add API keys to .env file")
        else:
            print(f"\n✓ {len(self.uploaders)} working uploader(s) ready")
            print("  Skipped: Streamtape (ISP blocked), Upload18 (encoding issues)")
    
    def upload_to_host(self, host_key, host_info, video_path, title):
        """Upload to a single host"""
        host_name = host_info['name']
        uploader = host_info['uploader']
        
        print(f"\n{'='*70}")
        print(f"[{host_name}] Starting upload...")
        print(f"{'='*70}")
        
        try:
            import time
            start_time = time.time()
            
            result = uploader.upload(video_path, title)
            
            elapsed = time.time() - start_time
            result['upload_time'] = elapsed
            result['host_name'] = host_name
            result['timestamp'] = datetime.now().isoformat()
            
            if result.get('success'):
                print(f"\n[{host_name}] ✓ Upload successful in {elapsed:.1f}s")
            else:
                print(f"\n[{host_name}] ✗ Upload failed: {result.get('error', 'Unknown')}")
            
            return host_key, result
            
        except Exception as e:
            print(f"\n[{host_name}] ✗ Exception: {str(e)}")
            return host_key, {
                'success': False,
                'error': str(e),
                'host_name': host_name,
                'timestamp': datetime.now().isoformat()
            }
    
    def upload_parallel(self, video_path, title, max_workers=4):
        """Upload to all hosts in parallel"""
        if not self.uploaders:
            print("✗ No uploaders available")
            return {}
        
        print(f"\n📤 Uploading to {len(self.uploaders)} working host(s) in parallel...")
        print(f"   Max workers: {max_workers}")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self.upload_to_host,
                    host_key,
                    host_info,
                    video_path,
                    title
                ): host_key
                for host_key, host_info in self.uploaders.items()
            }
            
            for future in as_completed(futures):
                host_key = futures[future]
                try:
                    host_key, result = future.result()
                    results[host_key] = result
                except Exception as e:
                    print(f"✗ {host_key} exception: {str(e)}")
                    results[host_key] = {
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
        
        return results
    
    def upload_video(self, video_path, video_code, title=None):
        """Upload video with validation"""
        print("\n" + "="*80)
        print(f"WORKING HOSTS UPLOAD PIPELINE")
        print("="*80)
        print(f"Video: {Path(video_path).name}")
        print(f"Code: {video_code}")
        print(f"Title: {title or video_code}")
        print("="*80)
        
        # Validate video
        print("\n🔍 Validating video...")
        is_valid, msg = validate_video(video_path)
        
        if not is_valid:
            print(f"✗ Validation failed: {msg}")
            print("  Skipping upload - video is corrupted or invalid")
            return False
        
        print(f"✓ Validation passed: {msg}")
        
        # Upload to all hosts in parallel
        results = self.upload_parallel(video_path, title or video_code)
        
        # Summary
        successful = sum(1 for r in results.values() if r.get('success'))
        failed = len(results) - successful
        
        print(f"\n{'='*80}")
        print(f"UPLOAD SUMMARY")
        print(f"{'='*80}")
        print(f"Total hosts: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        
        if successful > 0:
            print(f"\n✓ Successful uploads:")
            for host, result in results.items():
                if result.get('success'):
                    host_name = result.get('host_name', host)
                    embed_url = result.get('embed_url', result.get('url', 'N/A'))
                    print(f"  • {host_name}: {embed_url}")
        
        if failed > 0:
            print(f"\n✗ Failed uploads:")
            for host, result in results.items():
                if not result.get('success'):
                    host_name = result.get('host_name', host)
                    error = result.get('error', 'Unknown')
                    print(f"  • {host_name}: {error[:60]}")
        
        print(f"\n{'='*80}\n")
        
        # Update database if video exists
        if successful > 0:
            self.update_database(video_code, results)
        
        return successful > 0
    
    def update_database(self, video_code, results):
        """Update database with upload results"""
        try:
            video = db_manager.get_video_by_code(video_code)
            
            if not video:
                print(f"⚠️  Video '{video_code}' not found in database")
                return
            
            if 'hosting_urls' not in video:
                video['hosting_urls'] = {}
            
            # Update hosting URLs
            for host, result in results.items():
                if result.get('success'):
                    video['hosting_urls'][host] = {
                        'embed_url': result.get('embed_url', ''),
                        'download_url': result.get('url', result.get('download_url', '')),
                        'file_code': result.get('file_code', result.get('vid', ''))
                    }
            
            video['uploaded_at'] = datetime.now().isoformat()
            
            if db_manager.add_or_update_video(video):
                print(f"✓ Updated database for '{video_code}'")
            else:
                print(f"✗ Failed to update database")
                
        except Exception as e:
            print(f"✗ Database update error: {str(e)}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python upload_working_hosts_only.py <video_path> <video_code> [title]")
        print("\nExample:")
        print("  python upload_working_hosts_only.py video.mp4 VIDEO-001 'Video Title'")
        print("\nWorking hosts:")
        print("  ✓ Uploady (fastest)")
        print("  ✓ Turboviplay (reliable)")
        print("  ✓ MixDrop (alternative)")
        print("  ✓ SeekStreaming (backup)")
        print("\nSkipped hosts:")
        print("  ✗ Streamtape (ISP blocked)")
        print("  ✗ Upload18 (encoding issues)")
        sys.exit(1)
    
    video_path = sys.argv[1]
    video_code = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else video_code
    
    if not os.path.exists(video_path):
        print(f"✗ Video file not found: {video_path}")
        sys.exit(1)
    
    uploader = WorkingHostsUploader()
    success = uploader.upload_video(video_path, video_code, title)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
