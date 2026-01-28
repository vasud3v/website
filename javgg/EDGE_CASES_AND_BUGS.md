# Edge Cases and Potential Bugs

## CRITICAL BUGS FOUND:

### 1. ❌ Browser Not Initialized in scrape_new_videos
**Location:** `complete_workflow.py` line ~100
**Problem:** Removed `scraper._init_driver()` call but browser may not be initialized
**Impact:** Will crash on first scrape
**Fix:** Ensure `get_scraper()` always returns initialized browser

### 2. ❌ Scraper Not Closed on Exceptions
**Location:** Multiple methods
**Problem:** If exception occurs, browser stays open
**Impact:** Memory leak, zombie processes
**Fix:** Add try-finally blocks

### 3. ❌ Git Commit Skipped for Last Videos
**Location:** `process_video()` - batched commits
**Problem:** If workflow stops at video 1,2,3,4 - no commit happens
**Impact:** Data loss if workflow crashes
**Fix:** Always commit on workflow end

### 4. ❌ File Size Calculation Before Validation
**Location:** `process_video()` - preview generation
**Problem:** Gets file size before checking if file exists
**Impact:** Crash if download failed but returned path
**Fix:** Check file exists first

## EDGE CASES:

### 5. ⚠️ Browser Crashes Mid-Workflow
**Scenario:** Browser crashes after processing 10 videos
**Current:** Workflow fails completely
**Fix:** Detect crash, recreate browser, continue

### 6. ⚠️ Network Timeout During Download
**Scenario:** Download times out after 10 minutes
**Current:** Video marked as failed
**Fix:** Retry with exponential backoff

### 7. ⚠️ Disk Full During Download
**Scenario:** 2GB video but only 1GB space left
**Current:** Partial file, workflow continues
**Fix:** Check disk space before download

### 8. ⚠️ Cloudflare Blocks After 100 Requests
**Scenario:** Processing many videos, Cloudflare rate limits
**Current:** All subsequent videos fail
**Fix:** Detect rate limit, wait and retry

### 9. ⚠️ Database Corruption
**Scenario:** Power loss during database write
**Current:** Database becomes invalid JSON
**Fix:** Atomic writes with temp file + rename

### 10. ⚠️ Duplicate Video Codes
**Scenario:** Same video appears on multiple pages
**Current:** Processed twice
**Fix:** Already handled with seen_codes

### 11. ⚠️ Invalid Video URLs
**Scenario:** URL format changes or malformed
**Current:** Regex fails, returns None
**Fix:** Better URL validation and error messages

### 12. ⚠️ Upload Fails for All Hosts
**Scenario:** All 5 upload hosts are down
**Current:** Video processed but no URLs saved
**Fix:** Mark as "pending upload" for retry

### 13. ⚠️ Preview Generation Hangs
**Scenario:** Corrupted video causes ffmpeg to hang
**Current:** Workflow stuck forever
**Fix:** Timeout on preview generation (already has timeout)

### 14. ⚠️ JAVDatabase Down
**Scenario:** JAVDatabase website is offline
**Current:** All videos fail enrichment
**Fix:** Already handled - uses JavaGG data only

### 15. ⚠️ Memory Leak from Browser
**Scenario:** Browser accumulates memory over 100+ videos
**Current:** Eventually crashes
**Fix:** Restart browser every 50 videos

## RACE CONDITIONS:

### 16. ⚠️ Multiple Workflow Instances
**Scenario:** Two GitHub Actions run simultaneously
**Current:** Both process same videos, conflicts
**Fix:** Lock file mechanism

### 17. ⚠️ Database Write Conflicts
**Scenario:** Two processes write to database simultaneously
**Current:** Data corruption
**Fix:** File locking or database transactions

## DATA INTEGRITY:

### 18. ⚠️ Partial Downloads
**Scenario:** Download interrupted at 90%
**Current:** Partial file treated as complete
**Fix:** Validate file size matches expected

### 19. ⚠️ Corrupted Preview Files
**Scenario:** Preview generation fails mid-way
**Current:** Partial preview file left behind
**Fix:** Write to temp file, rename on success

### 20. ⚠️ Failed Videos Not Retried
**Scenario:** Temporary network issue causes failure
**Current:** Video permanently marked as failed
**Fix:** Retry failed videos after N days

## PERFORMANCE EDGE CASES:

### 21. ⚠️ Very Large Files (>10GB)
**Scenario:** 4K video is 15GB
**Current:** Download takes 30+ minutes, times out
**Fix:** Skip videos over size limit

### 22. ⚠️ Very Long Videos (>4 hours)
**Scenario:** Compilation video is 5 hours
**Current:** Preview generation takes 10+ minutes
**Fix:** Already handled - skip large files

### 23. ⚠️ Slow Upload Speeds
**Scenario:** Upload takes 20 minutes per host
**Current:** Workflow times out
**Fix:** Timeout per host, continue with others

## SECURITY:

### 24. ⚠️ Malicious Video Files
**Scenario:** Video contains exploit code
**Current:** ffmpeg processes it
**Fix:** Sandbox ffmpeg execution

### 25. ⚠️ XSS in Video Titles
**Scenario:** Title contains <script> tags
**Current:** Saved to database as-is
**Fix:** Sanitize all user input
