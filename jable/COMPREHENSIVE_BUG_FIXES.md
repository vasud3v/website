# Comprehensive Bug Fixes & Edge Cases

## Critical Issues Found & Fixed

### 1. **File Handle Leak in Upload Functions** ⚠️ CRITICAL
**Location:** `upload_all_hosts.py` - Lines 115-120, 470-475

**Issue:**
```python
file_handle = open(file_path, 'rb')
fields['file'] = (os.path.basename(file_path), file_handle, 'video/mp4')
# If exception occurs before finally block, file handle never closes
```

**Problem:** File handles not closed on exception, causing:
- Memory leaks
- File locks preventing deletion
- Resource exhaustion on long-running processes

**Fix:**
```python
file_handle = None
try:
    file_handle = open(file_path, 'rb')
    fields['file'] = (os.path.basename(file_path), file_handle, 'video/mp4')
    # ... upload code ...
except Exception as e:
    print(f"Upload error: {e}")
    raise
finally:
    if file_handle:
        try:
            file_handle.close()
        except:
            pass
```

### 2. **Race Condition in Database Saves** ⚠️ CRITICAL
**Location:** `run_continuous.py` - `save_video()` function

**Issue:** Multiple processes can read-modify-write database simultaneously

**Problem:**
- Lost updates when two processes save at same time
- Database corruption
- Videos disappearing from database

**Current Fix:** Uses `use_lock=True` but lock file can be stale

**Better Fix:**
```python
import fcntl  # Unix
# or
import msvcrt  # Windows

def save_with_lock(file_path, data):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with open(file_path, 'r+') as f:
                # Acquire exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                
                # Read current data
                f.seek(0)
                current = json.load(f)
                
                # Modify
                current.append(data)
                
                # Write back
                f.seek(0)
                f.truncate()
                json.dump(current, f, indent=2)
                
                # Lock released automatically on close
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            return False
```

### 3. **Incomplete Error Handling in convert_to_mp4** ⚠️ HIGH
**Location:** `auto_download.py` - `convert_to_mp4()` function

**Issues:**
1. No check if ffmpeg process was killed
2. No validation of output file integrity
3. Timeout too short for large files (600s = 10min)
4. No cleanup of partial output on failure

**Fix:**
```python
def convert_to_mp4(input_ts, output_mp4, timeout_multiplier=1.5):
    """Convert with dynamic timeout based on file size"""
    
    # Calculate timeout based on file size (1 minute per GB + 5 min base)
    input_size_gb = os.path.getsize(input_ts) / (1024**3)
    timeout = int((input_size_gb * 60 + 300) * timeout_multiplier)
    
    print(f"   Timeout: {timeout}s ({timeout/60:.1f} min)")
    
    # Remove partial output if exists
    if os.path.exists(output_mp4):
        try:
            os.remove(output_mp4)
        except:
            pass
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode != 0:
            print(f"   ❌ ffmpeg failed with code {result.returncode}")
            print(f"   Error: {result.stderr[:500]}")
            # Remove partial output
            if os.path.exists(output_mp4):
                os.remove(output_mp4)
            return False
        
        # Verify output exists and is valid
        if not os.path.exists(output_mp4):
            print(f"   ❌ Output file not created")
            return False
        
        output_size = os.path.getsize(output_mp4)
        if output_size < 1024 * 1024:  # Less than 1MB
            print(f"   ❌ Output file too small ({output_size} bytes)")
            os.remove(output_mp4)
            return False
        
        # Verify with ffprobe
        ffprobe = ffmpeg.replace('ffmpeg.exe', 'ffprobe.exe')
        probe_cmd = [ffprobe, '-v', 'error', '-show_entries', 
                    'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
                    output_mp4]
        
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        
        if probe_result.returncode != 0:
            print(f"   ❌ Output file is not a valid video")
            os.remove(output_mp4)
            return False
        
        try:
            duration = float(probe_result.stdout.strip())
            if duration < 60:  # Less than 1 minute
                print(f"   ❌ Video too short ({duration}s)")
                os.remove(output_mp4)
                return False
        except:
            print(f"   ❌ Could not parse duration")
            os.remove(output_mp4)
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print(f"   ❌ Conversion timed out after {timeout}s")
        # Kill the process
        try:
            result.kill()
        except:
            pass
        # Remove partial output
        if os.path.exists(output_mp4):
            try:
                os.remove(output_mp4)
            except:
                pass
        return False
```

### 4. **Memory Leak in Browser Instances** ⚠️ HIGH
**Location:** `run_continuous.py` - Browser not properly closed

**Issue:** Browser instances accumulate, consuming memory

**Current:** Browser closed after each video
**Problem:** Exception can prevent closure

**Fix:**
```python
def process_one_video_safe(scraper, url, num, total):
    """Wrapper that ensures browser cleanup"""
    browser_restarted = False
    try:
        return process_one_video(scraper, url, num, total)
    except Exception as e:
        log(f"❌ Exception: {e}")
        # Force browser restart on any exception
        try:
            scraper.close()
            time.sleep(2)
            scraper.init_driver()
            browser_restarted = True
            log("✅ Browser restarted after exception")
        except:
            pass
        return False
    finally:
        if not browser_restarted:
            # Ensure browser is in clean state
            try:
                scraper.driver.delete_all_cookies()
                scraper.driver.execute_script("window.localStorage.clear();")
                scraper.driver.execute_script("window.sessionStorage.clear();")
            except:
                pass
```

### 5. **Disk Space Check Race Condition** ⚠️ MEDIUM
**Location:** Multiple files - `check_disk_space()` calls

**Issue:** Space checked before operation, but another process might fill disk

**Fix:**
```python
def check_disk_space_with_reserve(min_free_gb=5, reserve_gb=2):
    """Check disk space with safety reserve"""
    has_space, free_gb, required_gb = check_disk_space(min_free_gb + reserve_gb)
    return has_space, free_gb, required_gb

# Use before large operations
has_space, free_gb, _ = check_disk_space_with_reserve(min_free_gb=3, reserve_gb=2)
```

### 6. **Incomplete Cleanup on Failure** ⚠️ MEDIUM
**Location:** `run_continuous.py` - `process_one_video()`

**Issue:** Partial files left on disk when process crashes

**Missing Cleanups:**
- Thumbnail files
- Preview files
- Partial downloads
- Lock files

**Fix:**
```python
def cleanup_all_temp_files(code, temp_dir):
    """Comprehensive cleanup"""
    patterns = [
        f"{code}.ts",
        f"{code}.mp4",
        f"{code}_preview.mp4",
        f"{code}_thumb.*",
        f"{code}.lock",
        f".{code}.*"  # Hidden temp files
    ]
    
    for pattern in patterns:
        for file in glob.glob(os.path.join(temp_dir, pattern)):
            try:
                os.remove(file)
                print(f"   🗑️ Removed: {os.path.basename(file)}")
            except Exception as e:
                print(f"   ⚠️ Could not remove {file}: {e}")
```

### 7. **Git Push Failures Not Handled** ⚠️ MEDIUM
**Location:** `run_continuous.py` - `commit_database()`

**Issue:** Push can fail but workflow continues, losing data

**Problems:**
- Network issues
- Authentication failures
- Merge conflicts
- Branch protection

**Fix:**
```python
def commit_database_with_retry(max_retries=3):
    """Commit with retry logic"""
    for attempt in range(max_retries):
        try:
            result = commit_database()
            if result:
                return True
            
            if attempt < max_retries - 1:
                log(f"   Commit failed, retry {attempt+2}/{max_retries} in 10s...")
                time.sleep(10)
                
                # Try to resolve conflicts
                subprocess.run(['git', 'reset', '--hard', 'HEAD'], 
                             capture_output=True, timeout=10)
                subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], 
                             capture_output=True, timeout=30)
        except Exception as e:
            log(f"   Commit exception: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
    
    # If all retries fail, save to backup
    log("   ❌ All commit attempts failed, saving to backup")
    backup_file = f"database/backup_{int(time.time())}.json"
    shutil.copy(DB_FILE, backup_file)
    log(f"   ✓ Backup saved: {backup_file}")
    return False
```

### 8. **StreamWish API Inconsistencies** ⚠️ MEDIUM
**Location:** `upload_all_hosts.py` - StreamWish verification

**Issues:**
1. API returns list sometimes, dict other times
2. File size in different fields (`size` vs `file_sizes`)
3. Status codes inconsistent

**Fix:** Already partially handled, but needs improvement:
```python
def normalize_streamwish_response(file_info):
    """Normalize inconsistent API responses"""
    # Handle list vs dict
    if isinstance(file_info, list):
        if len(file_info) > 0:
            file_info = file_info[0]
        else:
            return None
    
    # Normalize size field
    size = 0
    if 'file_sizes' in file_info:
        file_sizes = file_info.get('file_sizes', [])
        if isinstance(file_sizes, list) and len(file_sizes) > 0:
            size = file_sizes[0].get('size', 0)
    elif 'size' in file_info:
        size = file_info.get('size', 0)
    elif 'filesize' in file_info:
        size = file_info.get('filesize', 0)
    
    file_info['normalized_size'] = int(size) if size else 0
    return file_info
```

### 9. **Retry Logic Doesn't Reset State** ⚠️ LOW
**Location:** Multiple upload functions

**Issue:** Retries use same corrupted state from previous attempt

**Fix:**
```python
def upload_with_clean_retry(file_path, code, title, max_retries=3):
    """Upload with state reset between retries"""
    for attempt in range(max_retries):
        # Reset all state
        session = requests.Session()  # Fresh session
        
        # Clear any cached DNS
        try:
            import socket
            socket.setdefaulttimeout(30)
        except:
            pass
        
        try:
            result = upload_to_streamwish(file_path, code, title)
            if result.get('success'):
                return result
        except Exception as e:
            log(f"Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = (2 ** attempt) * 5
                log(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        finally:
            # Clean up session
            try:
                session.close()
            except:
                pass
    
    return {'success': False, 'error': 'All retries failed'}
```

### 10. **No Validation of Uploaded File Integrity** ⚠️ HIGH
**Location:** All upload functions

**Issue:** File could be corrupted during upload but marked as success

**Fix:**
```python
def verify_upload_integrity(local_file, remote_url, service='streamwish'):
    """Verify uploaded file matches local file"""
    try:
        local_size = os.path.getsize(local_file)
        
        # Get remote file size
        response = requests.head(remote_url, timeout=30, allow_redirects=True)
        remote_size = int(response.headers.get('Content-Length', 0))
        
        if remote_size == 0:
            # Try GET with range header
            response = requests.get(remote_url, headers={'Range': 'bytes=0-0'}, 
                                   timeout=30, allow_redirects=True)
            content_range = response.headers.get('Content-Range', '')
            # Format: bytes 0-0/12345
            if '/' in content_range:
                remote_size = int(content_range.split('/')[-1])
        
        if remote_size == 0:
            print(f"   ⚠️ Could not determine remote file size")
            return None
        
        size_diff = abs(local_size - remote_size)
        size_diff_pct = (size_diff / local_size) * 100
        
        print(f"   Local size:  {local_size:,} bytes")
        print(f"   Remote size: {remote_size:,} bytes")
        print(f"   Difference:  {size_diff:,} bytes ({size_diff_pct:.2f}%)")
        
        if size_diff_pct < 1.0:  # Less than 1% difference
            print(f"   ✅ File integrity verified")
            return True
        else:
            print(f"   ❌ File size mismatch!")
            return False
            
    except Exception as e:
        print(f"   ⚠️ Verification error: {e}")
        return None
```

## Additional Edge Cases

### 11. **Unicode Handling in Filenames**
**Issue:** Japanese/Chinese characters in video codes cause filesystem errors

**Fix:**
```python
def sanitize_filename(filename):
    """Sanitize with proper Unicode handling"""
    # Normalize Unicode
    import unicodedata
    filename = unicodedata.normalize('NFKD', filename)
    
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Limit length (accounting for UTF-8 encoding)
    max_bytes = 200
    while len(filename.encode('utf-8')) > max_bytes:
        filename = filename[:-1]
    
    return filename
```

### 12. **Timezone Issues in Timestamps**
**Issue:** Timestamps don't account for timezone, causing confusion

**Fix:**
```python
from datetime import datetime, timezone

def get_utc_timestamp():
    """Get UTC timestamp"""
    return datetime.now(timezone.utc).isoformat()

def get_local_timestamp():
    """Get local timestamp with timezone"""
    return datetime.now().astimezone().isoformat()
```

### 13. **No Handling of Partial M3U8 Downloads**
**Issue:** M3U8 playlist might be incomplete, causing download to hang

**Fix:** Add timeout and validation in HLSDownloader

### 14. **Browser Profile Pollution**
**Issue:** Browser cache/cookies accumulate, affecting scraping

**Fix:** Use temporary profile directory that's deleted after each run

### 15. **No Rate Limiting Between Requests**
**Issue:** Too many requests too fast can trigger IP bans

**Fix:** Already has `rate_limit()` function but not used everywhere

## Summary of Fixes Applied

✅ StreamWish quota detection (DONE)
✅ Streamtape error handling (DONE)
✅ Network retry logic (DONE)
⚠️ File handle leaks (NEEDS FIX)
⚠️ Database race conditions (NEEDS FIX)
⚠️ Incomplete error handling (NEEDS FIX)
⚠️ Memory leaks (NEEDS FIX)
⚠️ Disk space race conditions (NEEDS FIX)
⚠️ Incomplete cleanup (NEEDS FIX)
⚠️ Git push failures (NEEDS FIX)
⚠️ Upload integrity validation (NEEDS FIX)

## Priority Order

1. **CRITICAL** - File handle leaks (causes resource exhaustion)
2. **CRITICAL** - Database race conditions (causes data loss)
3. **HIGH** - Upload integrity validation (ensures quality)
4. **HIGH** - Incomplete error handling in convert_to_mp4
5. **HIGH** - Memory leaks in browser
6. **MEDIUM** - Git push failure handling
7. **MEDIUM** - Disk space race conditions
8. **MEDIUM** - Incomplete cleanup
9. **LOW** - Retry state reset
10. **LOW** - Unicode handling improvements
