"""
Utility functions for safe file operations and validation
"""
import os
import json
import time
import re
import shutil
import sys

# Import fcntl only on Unix systems
if sys.platform != 'win32':
    import fcntl
    import errno
else:
    fcntl = None
    errno = None


def normalize_url(url):
    """
    Normalize URL for comparison (fix duplicate detection)
    
    Args:
        url: URL string to normalize
        
    Returns:
        Normalized URL string
    """
    if not url:
        return ""
    
    # Convert to lowercase
    url = url.lower()
    
    # Remove query parameters
    if '?' in url:
        url = url.split('?')[0]
    
    # Remove fragment
    if '#' in url:
        url = url.split('#')[0]
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Normalize http/https
    url = url.replace('http://', 'https://')
    
    return url


def sanitize_filename(filename):
    """
    Sanitize filename to remove invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename string
    """
    if not filename:
        return "unnamed"
    
    # Remove invalid filesystem characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length (leave room for extension)
    if len(filename) > 200:
        filename = filename[:200]
    # Ensure not empty
    if not filename:
        filename = "unnamed"
    
    return filename


def validate_url(url, max_length=2000):
    """
    Validate URL format
    
    Args:
        url: URL string to validate
        max_length: Maximum allowed URL length
        
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    if not url.startswith(('http://', 'https://')):
        return False
    
    if len(url) > max_length:
        return False
    
    return True


class FileLock:
    """
    Improved file locking for safe concurrent access
    Works on Unix-like systems (Linux, macOS) and Windows
    Fixes race condition in Windows implementation
    """
    def __init__(self, filepath, timeout=300):  # Increased from 120s to 300s (5 minutes)
        self.filepath = filepath
        self.lockfile = filepath + '.lock'
        self.timeout = timeout
        self.lock_fd = None
        self.is_windows = sys.platform == 'win32'
        self.pid = os.getpid()
    
    def acquire(self):
        """Acquire lock with timeout and proper atomic operations"""
        if self.is_windows:
            # Windows: Use atomic file creation with exclusive access
            start_time = time.time()
            while True:
                try:
                    # Try to create lock file with exclusive access (atomic operation)
                    # This prevents race condition where two processes both see file doesn't exist
                    try:
                        # Open with exclusive creation flag
                        fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                        os.write(fd, f"{self.pid}:{time.time()}".encode())
                        os.close(fd)
                        return True
                    except FileExistsError:
                        # Lock file exists, check if it's stale
                        if os.path.exists(self.lockfile):
                            try:
                                # Read lock file to get PID and timestamp
                                with open(self.lockfile, 'r') as f:
                                    lock_data = f.read().strip()
                                    if ':' in lock_data:
                                        lock_pid, lock_time = lock_data.split(':', 1)
                                        lock_age = time.time() - float(lock_time)
                                    else:
                                        # Old format, use file modification time
                                        lock_age = time.time() - os.path.getmtime(self.lockfile)
                                
                                # Check if lock is stale (older than timeout)
                                if lock_age > self.timeout:
                                    print(f"⚠️ Removing stale lock (age: {lock_age:.1f}s)")
                                    try:
                                        os.remove(self.lockfile)
                                        continue  # Try again
                                    except Exception as e:
                                        print(f"⚠️ Could not remove stale lock: {e}")
                            except Exception as e:
                                print(f"⚠️ Error checking lock file: {e}")
                    
                    if time.time() - start_time > self.timeout:
                        raise TimeoutError(f"Could not acquire lock on {self.filepath} after {self.timeout}s")
                    
                    time.sleep(0.1)
                except TimeoutError:
                    raise
                except Exception as e:
                    if time.time() - start_time > self.timeout:
                        raise TimeoutError(f"Could not acquire lock on {self.filepath} after {self.timeout}s")
                    time.sleep(0.1)
        else:
            # Unix: Use fcntl (already atomic)
            start_time = time.time()
            
            while True:
                try:
                    # Open lock file
                    self.lock_fd = open(self.lockfile, 'w')
                    # Write PID and timestamp
                    self.lock_fd.write(f"{self.pid}:{time.time()}")
                    self.lock_fd.flush()
                    # Try to acquire exclusive lock (non-blocking)
                    fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return True
                except IOError as e:
                    if e.errno != errno.EAGAIN:
                        raise
                    
                    # Lock is held by another process
                    if time.time() - start_time > self.timeout:
                        if self.lock_fd:
                            self.lock_fd.close()
                        raise TimeoutError(f"Could not acquire lock on {self.filepath} after {self.timeout}s")
                    
                    time.sleep(0.1)
    
    def release(self):
        """Release lock with proper cleanup"""
        if self.is_windows:
            # Windows: Remove lock file
            try:
                if os.path.exists(self.lockfile):
                    # Verify it's our lock before removing
                    try:
                        with open(self.lockfile, 'r') as f:
                            lock_data = f.read().strip()
                            if ':' in lock_data:
                                lock_pid = int(lock_data.split(':', 1)[0])
                                if lock_pid == self.pid:
                                    os.remove(self.lockfile)
                                else:
                                    print(f"⚠️ Lock file owned by different process (PID {lock_pid})")
                            else:
                                # Old format, remove anyway
                                os.remove(self.lockfile)
                    except:
                        # If we can't read it, try to remove anyway
                        os.remove(self.lockfile)
            except Exception as e:
                print(f"⚠️ Could not release lock: {e}")
        else:
            # Unix: Release fcntl lock
            if self.lock_fd:
                try:
                    fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                    self.lock_fd.close()
                except Exception as e:
                    print(f"⚠️ Could not release fcntl lock: {e}")
                finally:
                    self.lock_fd = None
                
                # Remove lock file
                try:
                    if os.path.exists(self.lockfile):
                        os.remove(self.lockfile)
                except Exception as e:
                    print(f"⚠️ Could not remove lock file: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - always release lock"""
        self.release()
        return False


def load_json_safe(filepath, default=None):
    """
    Safely load JSON file with error handling
    
    Args:
        filepath: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Parsed JSON data or default value
    """
    if default is None:
        default = []
    
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON decode error in {filepath}: {e}")
        # Try to load backup
        backup = filepath + '.backup'
        if os.path.exists(backup):
            print(f"   Attempting to load backup...")
            try:
                with open(backup, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as backup_error:
                print(f"⚠️ Backup also failed: {backup_error}")
                pass
    except Exception as e:
        print(f"⚠️ Error loading {filepath}: {e}")
    
    return default


def save_json_safe(filepath, data, use_lock=True):
    """
    Safely save JSON file with atomic write and optional locking
    
    Args:
        filepath: Path to JSON file
        data: Data to save
        use_lock: Whether to use file locking (default: True)
        
    Returns:
        True if successful, False otherwise
    """
    lock = None
    try:
        # Create directory if needed
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Use file lock if requested
        if use_lock:
            lock = FileLock(filepath)
            lock.acquire()
        
        try:
            # Create backup if file exists
            if os.path.exists(filepath):
                backup = filepath + '.backup'
                try:
                    shutil.copy2(filepath, backup)
                except Exception as backup_error:
                    print(f"⚠️ Could not create backup: {backup_error}")
            
            # Write to temp file first (atomic write)
            temp_file = filepath + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Rename temp to actual file (atomic on most systems)
            if os.path.exists(filepath):
                os.remove(filepath)
            os.rename(temp_file, filepath)
            
            return True
            
        finally:
            if use_lock and lock:
                lock.release()
        
    except Exception as e:
        print(f"❌ Error saving {filepath}: {e}")
        import traceback
        traceback.print_exc()
        # Clean up temp file
        temp_file = filepath + '.tmp'
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as cleanup_error:
                print(f"⚠️ Could not remove temp file: {cleanup_error}")
        return False


def check_disk_space(required_bytes=None, path='.', min_free_gb=5):
    """
    Check if enough disk space is available
    
    Args:
        required_bytes: Required bytes (optional)
        path: Path to check
        min_free_gb: Minimum free space in GB
        
    Returns:
        Tuple of (has_space, available_gb, required_gb)
    """
    try:
        stat = shutil.disk_usage(path)
        available_gb = stat.free / (1024**3)
        
        if required_bytes:
            # Add 10% buffer
            required_gb = (required_bytes * 1.1) / (1024**3)
            has_space = available_gb > required_gb
        else:
            required_gb = min_free_gb
            has_space = available_gb > min_free_gb
        
        return has_space, available_gb, required_gb
    except Exception as e:
        print(f"⚠️ Could not check disk space: {e}")
        return True, 0, 0  # Assume OK if can't check


def verify_video_file(filepath, min_size_mb=1):
    """
    Verify video file exists and has reasonable size
    
    Args:
        filepath: Path to video file
        min_size_mb: Minimum expected size in MB
        
    Returns:
        True if valid, False otherwise
    """
    if not os.path.exists(filepath):
        print(f"❌ File does not exist: {filepath}")
        return False
    
    size_mb = os.path.getsize(filepath) / (1024**2)
    
    if size_mb < min_size_mb:
        print(f"❌ File too small ({size_mb:.2f} MB): {filepath}")
        return False
    
    return True


def cleanup_temp_files(code, temp_dir="temp_downloads"):
    """
    Clean up temporary files for a video
    
    Args:
        code: Video code
        temp_dir: Temporary directory path
    """
    files_to_delete = [
        f"{temp_dir}/{code}.mp4",
        f"{temp_dir}/{code}.ts",
        f"{temp_dir}/{code}_test.mp4",
        f"{temp_dir}/{code}_test.ts",
    ]
    
    dirs_to_delete = [
        f"{temp_dir}/{code}.ts_segments",
        f"{temp_dir}/{code}.mp4_segments",
    ]
    
    deleted_files = 0
    deleted_dirs = 0
    
    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files += 1
        except Exception as e:
            print(f"⚠️ Could not delete {file_path}: {e}")
    
    for dir_path in dirs_to_delete:
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                deleted_dirs += 1
        except Exception as e:
            print(f"⚠️ Could not delete {dir_path}: {e}")
    
    if deleted_files > 0 or deleted_dirs > 0:
        print(f"   🗑️ Cleaned up {deleted_files} files, {deleted_dirs} folders")


def rate_limit(last_request_time, min_delay=2.0):
    """
    Simple rate limiting
    
    Args:
        last_request_time: Timestamp of last request
        min_delay: Minimum delay between requests in seconds
        
    Returns:
        Current timestamp
    """
    if last_request_time:
        elapsed = time.time() - last_request_time
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
    
    return time.time()


def create_process_lock(lock_name="run_continuous"):
    """
    Create a process lock file to prevent multiple instances
    
    Args:
        lock_name: Name of the lock file
        
    Returns:
        Lock file path if successful, None if another process is running
    """
    lock_file = f".{lock_name}.lock"
    
    try:
        if os.path.exists(lock_file):
            # Check if lock is stale
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is still running
            if sys.platform == 'win32':
                import subprocess
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                      capture_output=True, text=True)
                if str(pid) not in result.stdout:
                    # Process not running, remove stale lock
                    os.remove(lock_file)
                else:
                    print(f"⚠️ Another instance is already running (PID: {pid})")
                    return None
            else:
                try:
                    os.kill(pid, 0)  # Check if process exists
                    print(f"⚠️ Another instance is already running (PID: {pid})")
                    return None
                except OSError:
                    # Process not running, remove stale lock
                    os.remove(lock_file)
        
        # Create lock file with current PID
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        return lock_file
    except Exception as e:
        print(f"⚠️ Could not create process lock: {e}")
        return None


def remove_process_lock(lock_file):
    """Remove process lock file"""
    try:
        if lock_file and os.path.exists(lock_file):
            os.remove(lock_file)
    except Exception as e:
        print(f"⚠️ Could not remove lock file: {e}")
        pass


def fix_video_title(video_data):
    """
    Fix title fields in video data
    Handles cases where title is just the code or fields are swapped
    
    Args:
        video_data: Dictionary with video information
        
    Returns:
        Fixed video_data dictionary
    """
    code = video_data.get('code', '')
    title = video_data.get('title', '')
    title_japanese = video_data.get('title_japanese', '')
    
    # Issue 1: Title is just the code
    if title == code or not title:
        # Try to extract from title_japanese
        if title_japanese and ' - ' in title_japanese:
            parts = title_japanese.split(' - ', 1)
            if parts[0].strip() == code:
                # Format: "CODE - English title"
                title = parts[1].strip()
                title_japanese = ''  # No actual Japanese text
        elif title_japanese and title_japanese != code:
            # Use title_japanese as title if it's not the code
            title = title_japanese
            title_japanese = ''
    
    # Issue 2: Detect if title_japanese is actually English
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    if title_japanese and not japanese_pattern.search(title_japanese):
        # It's not Japanese, move to title if title is empty
        if not title or title == code:
            title = title_japanese
        title_japanese = ''
    
    # Update video data
    video_data['title'] = title
    video_data['title_japanese'] = title_japanese
    
    # Add explicit English field
    if 'title_english' not in video_data:
        video_data['title_english'] = title
    
    return video_data
