# Complete Edge Case Analysis & Fixes

## Workflow Overview
```
1. Scrape metadata → 2. Download video → 3. Convert to MP4 → 
3.5. Generate preview → Upload to IA → 4. Upload full video to StreamWish → 
5. Save to database → 6. Cleanup
```

---

## 🔴 CRITICAL EDGE CASES

### 1. **Preview Generation Fails But Upload Succeeds**
**Issue**: Preview generation might fail, but we continue with full video upload
**Current**: ✅ HANDLED - Logs warning and continues
**Risk**: Low - Preview is optional, full video is priority

### 2. **Internet Archive Upload Fails**
**Issue**: Preview generated but IA upload fails
**Current**: ⚠️ PARTIAL - Cleanup happens but preview file might remain
**Fix Needed**: Ensure preview file is deleted even if IA upload fails

```python
# In generate_and_upload_preview.py
finally:
    # Always cleanup preview file
    if os.path.exists(preview_output):
        try:
            os.remove(preview_output)
        except:
            pass
```

### 3. **StreamWish Returns Duplicate But Can't Delete**
**Issue**: File exists (0 bytes), delete fails, re-upload rejected as duplicate
**Current**: ✅ FIXED - Returns existing filecode instead of re-uploading
**Status**: RESOLVED

### 4. **Disk Space Runs Out Mid-Download**
**Issue**: Download starts with enough space, but runs out during download
**Current**: ⚠️ NOT HANDLED - Only checks before download
**Fix Needed**: Monitor disk space during download

```python
# In HLSDownloader
def download_with_space_check(self, url, output, code):
    # Check space every 100 segments
    for i, segment in enumerate(segments):
        if i % 100 == 0:
            has_space, free_gb, _ = check_disk_space(min_free_gb=1)
            if not has_space:
                raise DiskSpaceError(f"Disk space low: {free_gb}GB")
        download_segment(segment)
```

### 5. **Conversion Fails Leaving Partial MP4**
**Issue**: FFmpeg crashes mid-conversion, leaves corrupted MP4
**Current**: ⚠️ PARTIAL - Checks if conversion succeeded but doesn't verify file
**Fix Needed**: Verify MP4 file integrity after conversion

```python
# After conversion
if not verify_video_file(mp4_file):
    raise ConversionError("MP4 file corrupted")
```

### 6. **Upload Succeeds But Database Save Fails**
**Issue**: Video uploaded to StreamWish but database save fails
**Current**: ⚠️ CRITICAL - Video is uploaded but not tracked
**Fix Needed**: Retry database save with exponential backoff

```python
# In save_video
max_retries = 3
for attempt in range(max_retries):
    try:
        result = db_manager.add_or_update_video(entry)
        if result:
            break
    except Exception as e:
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
        else:
            # Last resort: save to backup file
            backup_file = f"database/backup_{code}_{int(time.time())}.json"
            with open(backup_file, 'w') as f:
                json.dump(entry, f)
```

### 7. **Process Crashes Mid-Upload**
**Issue**: Process killed while uploading, leaves temp files and disk reservation
**Current**: ⚠️ PARTIAL - Cleanup on normal exit only
**Fix Needed**: Signal handlers for graceful shutdown

```python
import signal
import atexit

def cleanup_handler(signum, frame):
    log("⚠️ Process interrupted, cleaning up...")
    cleanup_and_release(current_video_code)
    sys.exit(1)

signal.signal(signal.SIGTERM, cleanup_handler)
signal.signal(signal.SIGINT, cleanup_handler)
atexit.register(lambda: cleanup_and_release(current_video_code))
```

### 8. **Browser Crashes During Scraping**
**Issue**: Selenium browser crashes, leaves zombie processes
**Current**: ✅ HANDLED - Browser restart on failure
**Status**: RESOLVED

### 9. **Network Timeout During Upload**
**Issue**: Upload times out after 2 hours, partial upload
**Current**: ⚠️ NOT HANDLED - No timeout on upload
**Fix Needed**: Add timeout to upload requests

```python
# In upload_to_streamwish
response = requests.post(
    upload_server,
    data=monitor,
    headers={'Content-Type': encoder.content_type},
    timeout=7200  # 2 hour timeout
)
```

### 10. **Duplicate Video Codes**
**Issue**: Two different videos with same code (rare but possible)
**Current**: ⚠️ NOT HANDLED - Overwrites existing entry
**Fix Needed**: Check URL in addition to code

```python
# In save_video
for v in videos:
    if v.get('code') == entry['code'] and v.get('source_url') == entry['source_url']:
        # Same video, update it
        videos[i] = entry
        found = True
        break
```

---

## 🟡 MEDIUM PRIORITY EDGE CASES

### 11. **Preview Generation Takes Too Long**
**Issue**: Preview generation takes 10+ minutes for long videos
**Current**: ⚠️ NOT HANDLED - No timeout
**Fix Needed**: Add timeout to preview generation

### 12. **Internet Archive Rate Limiting**
**Issue**: IA might rate limit if uploading too many previews
**Current**: ⚠️ NOT HANDLED
**Fix Needed**: Add retry with exponential backoff

### 13. **StreamWish Folder Creation Fails**
**Issue**: Folder API fails but upload continues
**Current**: ✅ HANDLED - Falls back to root folder
**Status**: RESOLVED

### 14. **Video Has No M3U8 URL**
**Issue**: Scraper finds video but no download link
**Current**: ✅ HANDLED - Returns None, marked as failed
**Status**: RESOLVED

### 15. **FFmpeg Not Installed**
**Issue**: convert_to_mp4 fails if FFmpeg missing
**Current**: ⚠️ NOT HANDLED - Crashes with unclear error
**Fix Needed**: Check FFmpeg availability at startup

```python
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except:
        return False

if not check_ffmpeg():
    log("❌ FFmpeg not installed!")
    sys.exit(1)
```

---

## 🟢 LOW PRIORITY EDGE CASES

### 16. **Video Title Has Special Characters**
**Issue**: Title with emojis or special chars might break filename
**Current**: ✅ HANDLED - sanitize_filename() cleans it
**Status**: RESOLVED

### 17. **Very Long Video Titles**
**Issue**: Title > 255 chars breaks filesystem
**Current**: ✅ HANDLED - Truncated to 100 chars in upload
**Status**: RESOLVED

### 18. **Video Duration is 0 or Invalid**
**Issue**: Scraper gets invalid duration
**Current**: ✅ HANDLED - Stored as-is, doesn't break workflow
**Status**: RESOLVED

### 19. **No Categories or Models**
**Issue**: Video has empty categories/models arrays
**Current**: ✅ HANDLED - Stored as empty arrays
**Status**: RESOLVED

### 20. **Thumbnail URL is Invalid**
**Issue**: Thumbnail URL returns 404
**Current**: ✅ HANDLED - Stored as-is, frontend handles broken images
**Status**: RESOLVED

---

## 🔧 FIXES TO IMPLEMENT

### Priority 1 (Critical)
1. ✅ Add disk space monitoring during download
2. ✅ Add MP4 file integrity verification
3. ✅ Add database save retry with backup
4. ✅ Add signal handlers for graceful shutdown
5. ✅ Add upload timeout

### Priority 2 (Medium)
6. ✅ Add preview generation timeout
7. ✅ Add IA upload retry logic
8. ✅ Add FFmpeg availability check

### Priority 3 (Low)
9. ✅ Add duplicate URL checking
10. ✅ Add better error messages

---

## 📊 Current Status

| Category | Total | Fixed | Partial | Not Fixed |
|----------|-------|-------|---------|-----------|
| Critical | 10 | 3 | 5 | 2 |
| Medium | 5 | 1 | 0 | 4 |
| Low | 5 | 5 | 0 | 0 |
| **TOTAL** | **20** | **9** | **5** | **6** |

---

## 🎯 Implementation Plan

### Phase 1: Critical Fixes (Today)
- [ ] Disk space monitoring during download
- [ ] MP4 integrity verification
- [ ] Database save retry + backup
- [ ] Signal handlers
- [ ] Upload timeout

### Phase 2: Medium Fixes (Tomorrow)
- [ ] Preview generation timeout
- [ ] IA upload retry
- [ ] FFmpeg check

### Phase 3: Testing (Day 3)
- [ ] Test all edge cases
- [ ] Verify fixes work
- [ ] Update documentation

