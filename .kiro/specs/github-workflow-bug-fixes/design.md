# Design Document

## Overview

This design addresses 15 critical bugs and edge cases in the GitHub Actions workflow and Python scraping pipeline. The fixes are organized into five major categories:

1. **Workflow Syntax and Logic Fixes** - Correct YAML syntax errors and time-based edge cases
2. **Resource Management** - Atomic disk space reservation and proper cleanup
3. **Data Integrity** - File locking, deduplication, and transaction safety
4. **Error Handling and Resilience** - Retry logic, backoff strategies, and graceful degradation
5. **Security and Observability** - Credential masking and improved logging

The design maintains backward compatibility with existing database structures while adding robustness through defensive programming, proper resource management, and comprehensive error handling.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                   │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │ Determine      │→ │ Scrape and   │→ │ Status Report   │ │
│  │ Action Job     │  │ Upload Job   │  │ Job             │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Python Scraping Pipeline                   │
│  ┌────────────┐  ┌──────────┐  ┌────────┐  ┌─────────────┐ │
│  │ Discovery  │→ │ Download │→ │ Upload │→ │ Database    │ │
│  │ (Browser)  │  │ (HLS)    │  │ (API)  │  │ Commit      │ │
│  └────────────┘  └──────────┘  └────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Database Manager (Enhanced)                 │
│  ┌────────────┐  ┌──────────┐  ┌────────┐  ┌─────────────┐ │
│  │ File       │  │ URL      │  │ Atomic │  │ Transaction │ │
│  │ Locking    │  │ Normalize│  │ Writes │  │ Safety      │ │
│  └────────────┘  └──────────┘  └────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Workflow Trigger** → Determine if scraping should run
2. **Discovery Phase** → Browser scrapes video URLs from pages
3. **Processing Phase** → For each video: download → upload → save → cleanup
4. **Commit Phase** → Atomic database write → git commit → git push with retry
5. **Cleanup Phase** → Remove temp files, close browser, release locks

## Components and Interfaces

### 1. Workflow YAML Fixes

**File:** `.github/workflows/integrated_scraper.yml`

**Changes:**

```yaml
# BEFORE (Line 127 - SYNTAX ERROR):
else:
  echo "should_scrape=false" >> $GITHUB_OUTPUT

# AFTER (CORRECT):
else
  echo "should_scrape=false" >> $GITHUB_OUTPUT
fi
```

**Time Extraction Fix:**

```bash
# BEFORE (FAILS AT MIDNIGHT/TOP OF HOUR):
CURRENT_MINUTE=$(date +%M | sed 's/^0//')
CURRENT_HOUR=$(date +%H | sed 's/^0//')

# AFTER (HANDLES 00 CORRECTLY):
CURRENT_MINUTE=$(date +%M | sed 's/^0*$/0/' | sed 's/^0\([1-9]\)/\1/')
CURRENT_HOUR=$(date +%H | sed 's/^0*$/0/' | sed 's/^0\([1-9]\)/\1/')

# Alternative (more robust):
CURRENT_MINUTE=$((10#$(date +%M)))
CURRENT_HOUR=$((10#$(date +%H)))
```

**Timeout Alignment:**

```yaml
# BEFORE:
timeout-minutes: 350  # 5h 50m
# Python script: TIME_LIMIT = 5.5 * 3600  # 5h 30m (330 min)

# AFTER:
timeout-minutes: 360  # 6h 0m (safe margin)
# Python script: TIME_LIMIT = 5.25 * 3600  # 5h 15m (315 min)
# Gap: 45 minutes for cleanup and commit
```

### 2. Disk Space Reservation Module

**New File:** `jable/disk_space_manager.py`

**Interface:**

```python
class DiskSpaceManager:
    """Atomic disk space reservation to prevent race conditions"""
    
    def __init__(self, reservation_file: str = "database/disk_reservations.json"):
        self.reservation_file = reservation_file
        self.lock = FileLock(reservation_file + ".lock")
    
    def reserve_space(self, size_gb: float, video_code: str) -> bool:
        """
        Atomically reserve disk space for a download.
        Returns True if reservation successful, False if insufficient space.
        """
        pass
    
    def release_space(self, video_code: str):
        """Release reserved space after download completes or fails"""
        pass
    
    def get_available_space(self) -> float:
        """Get actual available space minus all reservations"""
        pass
    
    def cleanup_stale_reservations(self, max_age_hours: int = 2):
        """Remove reservations older than max_age_hours"""
        pass
```

**Algorithm:**

1. Acquire exclusive lock on reservation file
2. Read current reservations
3. Calculate: `available = disk_free - sum(active_reservations)`
4. If `available >= requested_size`:
   - Add reservation: `{video_code: {size: size_gb, timestamp: now()}}`
   - Write reservations atomically
   - Release lock
   - Return True
5. Else:
   - Release lock
   - Return False

### 3. Database File Locking

**Enhancement to:** `database_manager.py`

**New Dependency:** `filelock` library

**Interface:**

```python
from filelock import FileLock, Timeout
import time

class DatabaseManager:
    def __init__(self):
        self.locks = {}  # filepath -> FileLock instance
        self.lock_timeout = 30  # seconds
        self.max_retries = 3
    
    def _get_lock(self, filepath: str) -> FileLock:
        """Get or create lock for a file"""
        if filepath not in self.locks:
            self.locks[filepath] = FileLock(filepath + ".lock", timeout=self.lock_timeout)
        return self.locks[filepath]
    
    def _read_json_locked(self, filepath: str, default: Any = None) -> Any:
        """Read JSON with shared lock (multiple readers allowed)"""
        lock = self._get_lock(filepath)
        for attempt in range(self.max_retries):
            try:
                with lock.acquire(timeout=self.lock_timeout):
                    return self._read_json(filepath, default)
            except Timeout:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    raise
    
    def _write_json_locked(self, filepath: str, data: Any) -> bool:
        """Write JSON with exclusive lock"""
        lock = self._get_lock(filepath)
        for attempt in range(self.max_retries):
            try:
                with lock.acquire(timeout=self.lock_timeout):
                    return self._write_json(filepath, data)
            except Timeout:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise
```

### 4. Git Push Retry Logic

**Enhancement to:** `run_continuous.py` - `commit_database()` function

**Strategy:**

```python
def commit_database_with_retry(max_retries: int = 3) -> bool:
    """Commit and push with exponential backoff retry"""
    
    for attempt in range(1, max_retries + 1):
        try:
            # Stage files
            subprocess.run(['git', 'add', 'database/'], check=True, timeout=10)
            
            # Check for changes
            result = subprocess.run(['git', 'diff', '--staged', '--quiet'], 
                                   capture_output=True, timeout=5)
            if result.returncode == 0:
                log("No changes to commit")
                return True
            
            # Commit
            commit_msg = f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True, timeout=10)
            
            # Pull with rebase (handle remote changes)
            try:
                subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], 
                             check=True, timeout=60)
            except subprocess.CalledProcessError as e:
                log(f"Pull failed: {e}, attempting to continue")
            
            # Push
            subprocess.run(['git', 'push', 'origin', 'main'], check=True, timeout=120)
            
            log(f"✅ Push successful on attempt {attempt}")
            return True
            
        except subprocess.TimeoutExpired:
            log(f"⚠️ Timeout on attempt {attempt}/{max_retries}")
            if attempt < max_retries:
                wait_time = 2 ** attempt  # 2, 4, 8 seconds
                time.sleep(wait_time)
            else:
                log("❌ All push attempts timed out")
                return False
                
        except subprocess.CalledProcessError as e:
            log(f"⚠️ Push failed on attempt {attempt}/{max_retries}: {e}")
            
            # Check if it's a conflict
            if "rejected" in str(e.stderr) or "non-fast-forward" in str(e.stderr):
                log("Conflict detected, pulling and retrying...")
                try:
                    subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], 
                                 check=True, timeout=60)
                except:
                    pass
            
            if attempt < max_retries:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                log("❌ All push attempts failed")
                # Save local backup
                backup_path = f"database/backup_{int(time.time())}.json"
                shutil.copy2(COMBINED_DB, backup_path)
                log(f"💾 Saved local backup: {backup_path}")
                return False
    
    return False
```

### 5. Cleanup on Crash

**Enhancement to:** `run_continuous.py`

**Signal Handlers:**

```python
import signal
import atexit

class CleanupManager:
    """Manage cleanup on normal exit and crashes"""
    
    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        self.current_video_code = None
        self.browser = None
        
        # Register cleanup handlers
        atexit.register(self.cleanup_all)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle termination signals"""
        log(f"⚠️ Received signal {signum}, cleaning up...")
        self.cleanup_all()
        sys.exit(1)
    
    def cleanup_all(self):
        """Clean up all resources"""
        # Close browser
        if self.browser:
            try:
                self.browser.quit()
                log("✓ Browser closed")
            except:
                pass
        
        # Clean up current video
        if self.current_video_code:
            cleanup_temp_files(self.current_video_code, self.temp_dir)
        
        # Clean up orphaned files
        self.cleanup_orphaned_files()
    
    def cleanup_orphaned_files(self):
        """Remove orphaned temp files and segment folders"""
        try:
            # Remove old temp files (older than 2 hours)
            cutoff_time = time.time() - (2 * 3600)
            
            for item in os.listdir(self.temp_dir):
                item_path = os.path.join(self.temp_dir, item)
                
                try:
                    # Check modification time
                    if os.path.getmtime(item_path) < cutoff_time:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                            log(f"🗑️ Removed orphaned file: {item}")
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            log(f"🗑️ Removed orphaned directory: {item}")
                except Exception as e:
                    log(f"⚠️ Could not remove {item}: {e}")
            
            # Remove segment folders matching pattern
            for item in os.listdir(self.temp_dir):
                if item.endswith('_segments'):
                    segment_path = os.path.join(self.temp_dir, item)
                    try:
                        shutil.rmtree(segment_path)
                        log(f"🗑️ Removed segment folder: {item}")
                    except Exception as e:
                        log(f"⚠️ Could not remove segment folder: {e}")
                        
        except Exception as e:
            log(f"⚠️ Cleanup error: {e}")
```

**Workflow Cleanup:**

```yaml
# Add to workflow after main steps
- name: Emergency cleanup
  if: always()  # Run even if workflow is cancelled
  run: |
    echo "Cleaning up temp files..."
    rm -rf jable/temp_downloads/* || true
    rm -rf jable/temp_downloads/.*_segments || true
    
    # Commit any pending changes
    git add database/ || true
    if ! git diff --staged --quiet; then
      git commit -m "Emergency save: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" || true
      git push || true
    fi
```

### 6. URL Normalization and Deduplication

**Enhancement to:** `database_manager.py`

**Normalization Function:**

```python
def _normalize_url(self, url: str) -> str:
    """
    Normalize URL for comparison to prevent duplicates.
    
    Rules:
    - Convert to lowercase
    - Use https:// protocol
    - Remove trailing slashes
    - Remove query parameters (?key=value)
    - Remove fragments (#section)
    - Remove www. prefix
    """
    if not url:
        return ""
    
    url = url.lower().strip()
    
    # Normalize protocol
    url = url.replace('http://', 'https://')
    
    # Remove www
    url = url.replace('https://www.', 'https://')
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    # Remove query parameters
    if '?' in url:
        url = url.split('?')[0]
    
    # Remove fragments
    if '#' in url:
        url = url.split('#')[0]
    
    return url
```

**Deduplication Check:**

```python
def is_processed(self, code: str = None, url: str = None) -> bool:
    """Check if video already processed (with URL normalization)"""
    videos = self.get_all_videos()
    
    if code:
        # Check by code
        for v in videos:
            if v.get('code') == code and v.get('hosting'):
                return True
    
    if url:
        # Check by normalized URL
        normalized_url = self._normalize_url(url)
        for v in videos:
            if self._normalize_url(v.get('source_url', '')) == normalized_url:
                if v.get('hosting'):
                    return True
    
    return False
```

### 7. API Key Validation

**New Step in Workflow:**

```yaml
- name: Validate API keys
  run: |
    echo "🔑 Validating API keys..."
    
    # Check if keys are set
    if [ -z "$STREAMWISH_API_KEY" ]; then
      echo "❌ STREAMWISH_API_KEY not set"
      exit 1
    fi
    
    if [ -z "$LULUSTREAM_API_KEY" ]; then
      echo "⚠️ LULUSTREAM_API_KEY not set (optional)"
    fi
    
    if [ -z "$STREAMTAPE_LOGIN" ] || [ -z "$STREAMTAPE_API_KEY" ]; then
      echo "⚠️ STREAMTAPE credentials not set (optional)"
    fi
    
    # Test API calls
    echo "Testing StreamWish API..."
    python -c "
    import os
    import requests
    api_key = os.getenv('STREAMWISH_API_KEY')
    response = requests.get(f'https://api.streamwish.com/api/account/info?key={api_key}', timeout=10)
    if response.status_code == 200:
        print('✅ StreamWish API key valid')
    else:
        print(f'❌ StreamWish API key invalid: {response.status_code}')
        exit(1)
    "
    
    echo "✅ API validation complete"
  env:
    STREAMWISH_API_KEY: ${{ secrets.STREAMWISH_API_KEY }}
    LULUSTREAM_API_KEY: ${{ secrets.LULUSTREAM_API_KEY }}
    STREAMTAPE_LOGIN: ${{ secrets.STREAMTAPE_LOGIN }}
    STREAMTAPE_API_KEY: ${{ secrets.STREAMTAPE_API_KEY }}
```

### 8. Browser Memory Leak Prevention

**Enhancement to:** `run_continuous.py`

**Browser Lifecycle Management:**

```python
class BrowserManager:
    """Manage browser lifecycle to prevent memory leaks"""
    
    def __init__(self):
        self.scraper = None
        self.videos_processed = 0
        self.restart_interval = 5  # Restart every N videos
    
    def get_scraper(self) -> JableScraper:
        """Get scraper, creating or restarting as needed"""
        if self.scraper is None:
            self.scraper = JableScraper(headless=True)
            self.videos_processed = 0
            log("✅ Browser started")
        elif self.videos_processed >= self.restart_interval:
            log(f"🔄 Restarting browser after {self.videos_processed} videos")
            self.close()
            self.scraper = JableScraper(headless=True)
            self.videos_processed = 0
            log("✅ Browser restarted")
        
        return self.scraper
    
    def close(self):
        """Close browser and verify process termination"""
        if self.scraper:
            try:
                # Close browser
                self.scraper.close()
                
                # Verify process is dead
                if hasattr(self.scraper, 'driver') and self.scraper.driver:
                    pid = self.scraper.driver.service.process.pid
                    
                    # Wait for process to die
                    for _ in range(10):
                        if not psutil.pid_exists(pid):
                            break
                        time.sleep(0.5)
                    
                    # Force kill if still alive
                    if psutil.pid_exists(pid):
                        os.kill(pid, signal.SIGKILL)
                        log("⚠️ Force killed browser process")
                
                log("✓ Browser closed")
            except Exception as e:
                log(f"⚠️ Browser close error: {e}")
            finally:
                self.scraper = None
    
    def increment_counter(self):
        """Increment videos processed counter"""
        self.videos_processed += 1
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
```

**Usage in main loop:**

```python
browser_manager = BrowserManager()

try:
    for video_url in video_urls:
        scraper = browser_manager.get_scraper()
        
        try:
            result = process_one_video(scraper, video_url, i, total)
            if result:
                browser_manager.increment_counter()
        except Exception as e:
            log(f"❌ Video processing error: {e}")
            # Browser will be restarted on next iteration
finally:
    browser_manager.close()
```

### 9. Discovery Failure Backoff

**Enhancement to:** `run_continuous.py` - main loop

**Backoff Strategy:**

```python
class DiscoveryBackoff:
    """Exponential backoff for discovery failures"""
    
    def __init__(self):
        self.failure_count = 0
        self.max_failures = 10
        self.backoff_schedule = {
            3: 60,    # After 3 failures: wait 60s
            5: 300,   # After 5 failures: wait 5min
            7: 900,   # After 7 failures: wait 15min
            10: None  # After 10 failures: exit
        }
    
    def record_failure(self) -> bool:
        """
        Record a discovery failure.
        Returns True if should continue, False if should exit.
        """
        self.failure_count += 1
        log(f"⚠️ Discovery failure #{self.failure_count}")
        
        # Check if should exit
        if self.failure_count >= self.max_failures:
            log(f"❌ Too many discovery failures ({self.failure_count}), exiting")
            return False
        
        # Check if should wait
        for threshold, wait_time in self.backoff_schedule.items():
            if self.failure_count == threshold and wait_time:
                log(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                break
        
        return True
    
    def record_success(self):
        """Record a successful discovery (reset counter)"""
        if self.failure_count > 0:
            log(f"✅ Discovery recovered after {self.failure_count} failures")
        self.failure_count = 0
```

**Usage:**

```python
backoff = DiscoveryBackoff()

while True:
    try:
        links = scraper.get_video_links_from_page(url)
        
        if not links:
            if not backoff.record_failure():
                break  # Exit on too many failures
            continue
        
        backoff.record_success()
        # Process videos...
        
    except Exception as e:
        log(f"❌ Page load error: {e}")
        if not backoff.record_failure():
            break
```

### 10. Credential Masking

**Enhancement to:** `run_continuous.py` - `commit_database()` function

**Masking Function:**

```python
def mask_credentials(text: str) -> str:
    """Mask sensitive credentials in log output"""
    # Get tokens from environment
    github_token = os.getenv('GITHUB_TOKEN', '')
    streamwish_key = os.getenv('STREAMWISH_API_KEY', '')
    lulustream_key = os.getenv('LULUSTREAM_API_KEY', '')
    streamtape_key = os.getenv('STREAMTAPE_API_KEY', '')
    
    # Mask each token
    for token in [github_token, streamwish_key, lulustream_key, streamtape_key]:
        if token and len(token) > 8:
            text = text.replace(token, '***TOKEN***')
    
    # Mask common patterns
    import re
    
    # Mask URLs with tokens: https://TOKEN@github.com
    text = re.sub(r'https://[^@\s]+@github\.com', 'https://***TOKEN***@github.com', text)
    
    # Mask API keys in URLs: ?key=TOKEN
    text = re.sub(r'[?&]key=[^&\s]+', '?key=***TOKEN***', text)
    
    return text

def log(msg: str):
    """Log with credential masking"""
    masked_msg = mask_credentials(msg)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {masked_msg}", flush=True)
```

### 11. Workflow Cancellation Handling

**Enhancement to Workflow:**

```yaml
- name: Commit and push results
  if: always()  # Run even on cancellation
  run: |
    # Use trap to handle cancellation
    trap 'echo "⚠️ Caught cancellation signal"; git stash; exit 0' SIGTERM SIGINT
    
    git config --local user.email "github-actions[bot]@users.noreply.github.com"
    git config --local user.name "github-actions[bot]"
    
    # Check for uncommitted changes
    if ! git diff --quiet || ! git diff --staged --quiet; then
      echo "📝 Uncommitted changes detected"
      
      # Stash changes
      git stash push -m "Auto-stash: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
      echo "✓ Changes stashed"
      
      # Try to commit stashed changes
      git stash pop || true
      git add database/ || true
      
      if ! git diff --staged --quiet; then
        git commit -m "Auto-save on cancellation: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" || true
        git push || echo "⚠️ Push failed, changes are committed locally"
      fi
    fi
```

### 12. JAVDatabase Integration Fallback

**Enhancement to:** `run_continuous.py` - JAVDatabase enrichment section

**Fallback Logic:**

```python
class JAVDatabaseClient:
    """JAVDatabase client with availability tracking"""
    
    def __init__(self):
        self.consecutive_failures = 0
        self.max_failures_before_skip = 5
        self.is_available = True
    
    def enrich_video(self, jable_data: dict, max_retries: int = 2) -> bool:
        """
        Enrich video with JAVDatabase data.
        Returns True if successful, False otherwise.
        """
        # Skip if consistently failing
        if not self.is_available:
            log("⏭️ Skipping JAVDatabase (marked unavailable)")
            return False
        
        for attempt in range(1, max_retries + 1):
            try:
                success = enrich_with_javdb(jable_data, headless=True)
                
                if success:
                    self.consecutive_failures = 0
                    log(f"✅ JAVDatabase enrichment successful")
                    return True
                else:
                    log(f"⚠️ JAVDatabase enrichment failed (attempt {attempt}/{max_retries})")
                    
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                    
            except Exception as e:
                log(f"❌ JAVDatabase error (attempt {attempt}/{max_retries}): {e}")
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        
        # All retries failed
        self.consecutive_failures += 1
        log(f"⚠️ JAVDatabase consecutive failures: {self.consecutive_failures}")
        
        # Mark as unavailable if too many failures
        if self.consecutive_failures >= self.max_failures_before_skip:
            self.is_available = False
            log(f"❌ JAVDatabase marked unavailable after {self.consecutive_failures} failures")
        
        return False
```

## Data Models

### Disk Reservation Entry

```python
{
    "video_code": str,           # Video identifier
    "size_gb": float,            # Reserved space in GB
    "timestamp": float,          # Unix timestamp of reservation
    "pid": int                   # Process ID that made reservation
}
```

### Database Lock Metadata

```python
{
    "filepath": str,             # Path to locked file
    "lock_acquired": float,      # Timestamp when lock acquired
    "lock_holder": int,          # Process ID holding lock
    "lock_type": str             # "read" or "write"
}
```

### Git Push Retry State

```python
{
    "attempt": int,              # Current retry attempt (1-3)
    "last_error": str,           # Last error message
    "backoff_seconds": int,      # Current backoff duration
    "local_backup": str          # Path to local backup if all retries fail
}
```

### Discovery Backoff State

```python
{
    "failure_count": int,        # Number of consecutive failures
    "last_failure_time": float,  # Timestamp of last failure
    "next_retry_time": float,    # Timestamp when next retry allowed
    "should_exit": bool          # True if max failures reached
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: YAML Syntax Validity
*For any* workflow YAML file, parsing it with a YAML parser should not raise syntax errors, and all bash script blocks should use correct conditional syntax (`else` not `else:`)
**Validates: Requirements 1.1, 1.2**

### Property 2: Time Extraction Robustness
*For any* time value including "00", the time extraction function should return a valid numeric value (0 for "00") and never return an empty string
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 3: Atomic Disk Space Reservation
*For any* concurrent disk space reservation attempts, if the total requested space exceeds available space, then at most one reservation should succeed, and the available space calculation should always exclude all active reservations
**Validates: Requirements 3.1, 3.2**

### Property 4: Reservation Cleanup
*For any* download operation (successful or failed), the disk space reservation should be released after the operation completes
**Validates: Requirements 3.3**

### Property 5: File Lock Acquisition
*For any* database read or write operation, an appropriate file lock (shared for reads, exclusive for writes) should be acquired before the operation and released after
**Validates: Requirements 4.1, 4.2**

### Property 6: Lock Retry with Backoff
*For any* lock acquisition that times out, the operation should retry with exponentially increasing wait times (2^attempt seconds) up to the maximum retry count
**Validates: Requirements 4.3**

### Property 7: Time-Based Video Acceptance
*For any* video in the processing queue, if less than 30 minutes remain before the workflow timeout, the video should not be started
**Validates: Requirements 5.2**

### Property 8: Git Push Retry
*For any* git push operation that fails, the operation should be retried up to 3 times with exponential backoff (2^attempt seconds)
**Validates: Requirements 6.1**

### Property 9: Temporary File Cleanup
*For any* video processing operation (successful, failed, or interrupted), all temporary files and segment folders associated with that video should be removed after the operation completes
**Validates: Requirements 7.2, 15.1, 15.2**

### Property 10: URL Normalization Consistency
*For any* URL comparison operation, both URLs should be normalized using the same rules (lowercase, https, remove query params, remove fragments, remove trailing slashes) before comparison
**Validates: Requirements 8.1, 8.2, 8.3**

### Property 11: Browser Lifecycle Management
*For any* exception during scraping, the browser should be closed in a finally block, and the browser process should be verified as terminated
**Validates: Requirements 10.1, 10.2**

### Property 12: Browser Restart Policy
*For any* sequence of N successful video processing operations (where N is the restart interval), the browser should be restarted after the Nth video to prevent memory accumulation
**Validates: Requirements 10.4**

### Property 13: Discovery Failure Counter
*For any* video discovery failure, the failure counter should be incremented, and for any successful discovery, the counter should be reset to zero
**Validates: Requirements 11.1**

### Property 14: Credential Masking
*For any* log message containing sensitive credentials (GitHub tokens, API keys), the credentials should be replaced with "***TOKEN***" before logging
**Validates: Requirements 12.1, 12.2, 12.3**

### Property 15: JAVDatabase Retry
*For any* JAVDatabase API call that fails, the operation should be retried up to 2 times with exponential backoff (2^attempt seconds)
**Validates: Requirements 14.2**

### Property 16: JAVDatabase Availability Tracking
*For any* sequence of N consecutive JAVDatabase failures (where N is the threshold), the service should be marked as unavailable and enrichment should be skipped for subsequent videos until a success occurs
**Validates: Requirements 14.4**

## Error Handling

### Error Categories

1. **Syntax Errors** (Requirement 1)
   - Detection: YAML parsing at workflow validation time
   - Handling: Fail workflow immediately with clear error message
   - Recovery: Fix YAML syntax and re-trigger

2. **Time Extraction Errors** (Requirement 2)
   - Detection: Empty string or invalid numeric value from time extraction
   - Handling: Use fallback value of 0 or current time
   - Recovery: Log warning and continue with fallback

3. **Disk Space Errors** (Requirement 3)
   - Detection: Reservation fails due to insufficient space
   - Handling: Skip video, log reason, continue to next video
   - Recovery: Wait for space to be freed by cleanup

4. **Lock Timeout Errors** (Requirement 4)
   - Detection: Lock acquisition times out after max retries
   - Handling: Log error, skip operation, continue
   - Recovery: Retry on next iteration

5. **Git Push Errors** (Requirement 6)
   - Detection: Push fails with network error or conflict
   - Handling: Retry with backoff, pull-rebase on conflict
   - Recovery: Save local backup if all retries fail

6. **Browser Errors** (Requirement 10)
   - Detection: Browser crash, memory leak, or process hang
   - Handling: Force kill process, restart browser
   - Recovery: Continue with fresh browser instance

7. **API Validation Errors** (Requirement 9)
   - Detection: API key missing or test call fails
   - Handling: Fail workflow immediately
   - Recovery: Fix API keys and re-trigger

8. **JAVDatabase Errors** (Requirement 14)
   - Detection: API call fails or times out
   - Handling: Retry with backoff, fallback to Jable data only
   - Recovery: Mark service unavailable after repeated failures

### Error Logging

All errors should be logged with:
- Timestamp
- Error category
- Error message (with credentials masked)
- Context (video code, operation, attempt number)
- Recovery action taken

### Error Metrics

Track and report:
- Total errors by category
- Retry success rate
- Average recovery time
- Videos skipped due to errors

## Testing Strategy

### Unit Testing

**Test Framework:** pytest for Python, shellcheck for bash scripts

**Unit Test Coverage:**

1. **Time Extraction** (Requirement 2)
   - Test with "00", "01", "09", "10", "23"
   - Verify no empty strings returned
   - Verify correct numeric conversion

2. **URL Normalization** (Requirement 8)
   - Test with various URL formats
   - Verify query params removed
   - Verify fragments removed
   - Verify trailing slashes removed
   - Verify case normalization

3. **Credential Masking** (Requirement 12)
   - Test with various token formats
   - Verify tokens replaced with "***TOKEN***"
   - Verify URL patterns masked
   - Verify API key patterns masked

4. **Backoff Calculation** (Requirements 6, 11, 14)
   - Test exponential backoff formula
   - Verify wait times: 2s, 4s, 8s
   - Verify max retries respected

5. **Lock Acquisition** (Requirement 4)
   - Test lock acquisition and release
   - Test timeout behavior
   - Test retry logic

### Property-Based Testing

**Test Framework:** Hypothesis for Python

**Property Test Configuration:**
- Minimum 100 iterations per test
- Each test tagged with: `Feature: github-workflow-bug-fixes, Property N: [property text]`

**Property Tests:**

1. **Property 2: Time Extraction Robustness**
   - Generate: Random time strings (00-23 for hours, 00-59 for minutes)
   - Assert: Result is numeric and not empty string
   - Tag: `Feature: github-workflow-bug-fixes, Property 2: Time extraction returns valid numeric values`

2. **Property 3: Atomic Disk Space Reservation**
   - Generate: Random reservation requests with varying sizes
   - Assert: Total reserved space never exceeds available space
   - Tag: `Feature: github-workflow-bug-fixes, Property 3: Atomic disk space reservation`

3. **Property 4: Reservation Cleanup**
   - Generate: Random download operations (success/failure)
   - Assert: Reservation released after operation
   - Tag: `Feature: github-workflow-bug-fixes, Property 4: Reservation cleanup`

4. **Property 5: File Lock Acquisition**
   - Generate: Random read/write operations
   - Assert: Appropriate lock acquired before operation
   - Tag: `Feature: github-workflow-bug-fixes, Property 5: File lock acquisition`

5. **Property 6: Lock Retry with Backoff**
   - Generate: Random lock timeout scenarios
   - Assert: Retry count and backoff times correct
   - Tag: `Feature: github-workflow-bug-fixes, Property 6: Lock retry with backoff`

6. **Property 8: Git Push Retry**
   - Generate: Random push failure scenarios
   - Assert: Retry count and backoff times correct
   - Tag: `Feature: github-workflow-bug-fixes, Property 8: Git push retry`

7. **Property 9: Temporary File Cleanup**
   - Generate: Random video processing operations
   - Assert: All temp files removed after operation
   - Tag: `Feature: github-workflow-bug-fixes, Property 9: Temporary file cleanup`

8. **Property 10: URL Normalization Consistency**
   - Generate: Random URL pairs with variations
   - Assert: Normalized URLs match when they should
   - Tag: `Feature: github-workflow-bug-fixes, Property 10: URL normalization consistency`

9. **Property 11: Browser Lifecycle Management**
   - Generate: Random scraping operations with exceptions
   - Assert: Browser closed in finally block
   - Tag: `Feature: github-workflow-bug-fixes, Property 11: Browser lifecycle management`

10. **Property 13: Discovery Failure Counter**
    - Generate: Random sequences of success/failure
    - Assert: Counter increments on failure, resets on success
    - Tag: `Feature: github-workflow-bug-fixes, Property 13: Discovery failure counter`

11. **Property 14: Credential Masking**
    - Generate: Random log messages with tokens
    - Assert: All tokens masked in output
    - Tag: `Feature: github-workflow-bug-fixes, Property 14: Credential masking`

12. **Property 15: JAVDatabase Retry**
    - Generate: Random API failure scenarios
    - Assert: Retry count and backoff times correct
    - Tag: `Feature: github-workflow-bug-fixes, Property 15: JAVDatabase retry`

### Integration Testing

**Integration Test Scenarios:**

1. **End-to-End Workflow** (All Requirements)
   - Run complete workflow in test environment
   - Verify all fixes work together
   - Check for regressions

2. **Concurrent Access** (Requirements 3, 4)
   - Run multiple scraper instances
   - Verify disk reservations don't conflict
   - Verify database locks prevent corruption

3. **Failure Recovery** (Requirements 6, 7, 10, 11, 14)
   - Simulate various failure scenarios
   - Verify retry logic works
   - Verify cleanup happens
   - Verify graceful degradation

4. **Workflow Cancellation** (Requirement 13)
   - Cancel workflow at various stages
   - Verify cleanup happens
   - Verify data saved

### Manual Testing

**Manual Test Cases:**

1. **API Key Validation** (Requirement 9)
   - Test with missing keys
   - Test with invalid keys
   - Verify workflow fails fast

2. **Time-Based Scheduling** (Requirement 2)
   - Trigger workflow at midnight
   - Trigger at top of hour
   - Verify correct execution

3. **Git Push Conflicts** (Requirement 6)
   - Create manual commits during workflow
   - Verify conflict resolution works

4. **Memory Leak Prevention** (Requirement 10)
   - Run workflow for extended period
   - Monitor memory usage
   - Verify browser restarts prevent leaks
