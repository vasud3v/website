"""
Edge Case Fixes - Critical safety mechanisms
"""
import os
import sys
import time
import signal
import subprocess
import json
from pathlib import Path

# Global state for cleanup
_current_video_code = None
_temp_dir = "temp_downloads"

def set_current_video(code):
    """Set current video being processed for cleanup"""
    global _current_video_code
    _current_video_code = code

def cleanup_handler(signum=None, frame=None):
    """Handle process interruption gracefully"""
    print(f"\n⚠️ Process interrupted (signal {signum}), cleaning up...")
    
    if _current_video_code:
        try:
            # Cleanup temp files
            from utils import cleanup_temp_files
            cleanup_temp_files(_current_video_code, _temp_dir)
            
            # Release disk space
            from disk_space_manager import disk_manager
            disk_manager.release_space(_current_video_code)
            
            print(f"✓ Cleaned up {_current_video_code}")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
    
    sys.exit(1)

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGTERM, cleanup_handler)
    signal.signal(signal.SIGINT, cleanup_handler)
    
    # Windows doesn't have SIGHUP
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, cleanup_handler)
    
    print("✓ Signal handlers registered")

def check_ffmpeg():
    """Check if FFmpeg is installed and available"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version
            version_line = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg found: {version_line}")
            return True
        return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH")
        return False
    except Exception as e:
        print(f"⚠️ FFmpeg check error: {e}")
        return False

def verify_mp4_integrity(mp4_file, min_duration=10):
    """
    Verify MP4 file integrity using FFprobe
    
    Args:
        mp4_file: Path to MP4 file
        min_duration: Minimum expected duration in seconds
    
    Returns:
        bool: True if file is valid
    """
    if not os.path.exists(mp4_file):
        print(f"❌ File not found: {mp4_file}")
        return False
    
    file_size = os.path.getsize(mp4_file)
    if file_size < 1024 * 1024:  # Less than 1MB
        print(f"❌ File too small: {file_size / 1024:.1f} KB")
        return False
    
    try:
        # Use FFprobe to check file
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration,size',
            '-of', 'json',
            mp4_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ FFprobe error: {result.stderr}")
            return False
        
        data = json.loads(result.stdout)
        duration = float(data['format'].get('duration', 0))
        size = int(data['format'].get('size', 0))
        
        print(f"✓ MP4 valid: {duration:.1f}s, {size / (1024**2):.1f} MB")
        
        if duration < min_duration:
            print(f"⚠️ Duration too short: {duration:.1f}s < {min_duration}s")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ FFprobe timeout")
        return False
    except json.JSONDecodeError:
        print("❌ FFprobe output invalid")
        return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def save_video_with_retry(entry, max_retries=3):
    """
    Save video to database with retry and backup
    
    Args:
        entry: Video entry dict
        max_retries: Maximum retry attempts
    
    Returns:
        bool: True if saved successfully
    """
    from database_manager import db_manager
    
    for attempt in range(max_retries):
        try:
            result = db_manager.add_or_update_video(entry)
            if result:
                print(f"✓ Saved to database (attempt {attempt + 1})")
                return True
        except Exception as e:
            print(f"⚠️ Save attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"   Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                # Last resort: save to backup file
                code = entry.get('code', 'unknown')
                backup_dir = Path("database/backups")
                backup_dir.mkdir(exist_ok=True)
                
                backup_file = backup_dir / f"backup_{code}_{int(time.time())}.json"
                
                try:
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        json.dump(entry, f, indent=2, ensure_ascii=False)
                    print(f"✓ Saved to backup: {backup_file}")
                    return True
                except Exception as backup_error:
                    print(f"❌ Backup save failed: {backup_error}")
                    return False
    
    return False

def monitor_disk_space_during_download(check_interval_mb=100):
    """
    Generator that yields True if disk space is OK
    Call this every N MB downloaded
    
    Args:
        check_interval_mb: Check every N MB
    
    Yields:
        bool: True if space OK, False if low
    """
    from utils import check_disk_space
    
    bytes_since_check = 0
    check_interval_bytes = check_interval_mb * 1024 * 1024
    
    while True:
        bytes_downloaded = yield
        bytes_since_check += bytes_downloaded
        
        if bytes_since_check >= check_interval_bytes:
            has_space, free_gb, _ = check_disk_space(min_free_gb=1)
            bytes_since_check = 0
            
            if not has_space:
                print(f"⚠️ Disk space low during download: {free_gb:.1f}GB")
                yield False
                return
            
            yield True

def add_upload_timeout(timeout_seconds=7200):
    """
    Decorator to add timeout to upload functions
    
    Args:
        timeout_seconds: Timeout in seconds (default 2 hours)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import threading
            
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)
            
            if thread.is_alive():
                print(f"❌ Upload timeout after {timeout_seconds}s")
                return None
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        
        return wrapper
    return decorator

def check_duplicate_by_url(url, videos):
    """
    Check if video already exists by URL (not just code)
    
    Args:
        url: Video URL
        videos: List of video entries
    
    Returns:
        dict or None: Existing video entry if found
    """
    from utils import normalize_url
    
    normalized = normalize_url(url)
    
    for video in videos:
        video_url = video.get('source_url', '')
        if normalize_url(video_url) == normalized:
            return video
    
    return None

# Startup checks
def run_startup_checks():
    """Run all startup checks"""
    print("\n" + "="*60)
    print("EDGE CASE PROTECTION - STARTUP CHECKS")
    print("="*60)
    
    checks_passed = True
    
    # Check FFmpeg
    print("\n[1/2] Checking FFmpeg...")
    if not check_ffmpeg():
        print("❌ FFmpeg is required for video conversion")
        checks_passed = False
    
    # Setup signal handlers
    print("\n[2/2] Setting up signal handlers...")
    try:
        setup_signal_handlers()
    except Exception as e:
        print(f"⚠️ Could not setup signal handlers: {e}")
    
    print("\n" + "="*60)
    if checks_passed:
        print("✓ ALL CHECKS PASSED")
    else:
        print("❌ SOME CHECKS FAILED")
    print("="*60 + "\n")
    
    return checks_passed

if __name__ == "__main__":
    # Test all functions
    run_startup_checks()
