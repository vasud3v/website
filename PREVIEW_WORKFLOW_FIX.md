# Preview Workflow Fix - Video Files Not Available

## Problem Identified

The preview generation workflow was not working because:

1. **Scraper deletes videos immediately** after upload (Step 6)
2. **Preview generation runs AFTER** scraper completes
3. **By the time preview generation runs**, all video files are already deleted from `jable/temp_downloads`
4. **Result**: No videos found to generate previews from

## Root Cause

```
Timeline:
1. Scraper downloads video → temp_downloads/VIDEO-CODE.mp4
2. Scraper uploads to StreamWish/LuluStream/Streamtape
3. Scraper DELETES video file ← Problem!
4. Scraper commits database
5. Preview generation step runs
6. Preview generation looks for videos in temp_downloads
7. No videos found! ← Files already deleted
```

## Solution Implemented

### Fix #1: Skip Deletion in GitHub Actions

**File:** `jable/run_continuous.py`

Modified Step 6 to check if running in GitHub Actions:

```python
# BEFORE
# STEP 6: Delete video file
cleanup_and_release(code)
log("✅ Deleted video file")

# AFTER
# STEP 6: Delete video file (skip in GitHub Actions for preview generation)
is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'

if is_github_actions:
    log("ℹ️ Running in GitHub Actions - keeping video file for preview generation")
    # Don't cleanup yet - let the preview generation step handle it
else:
    # Local run - cleanup immediately
    cleanup_and_release(code)
    log("✅ Deleted video file")
```

**Result:** Video files are kept in `temp_downloads` when running in GitHub Actions

---

### Fix #2: Cleanup After Preview Generation

**File:** `.github/workflows/integrated_scraper.yml`

Added cleanup code after preview generation:

```python
# After processing previews
print(f"\nCleaning up video files...")
for video_info in videos_needing_preview[:max_previews]:
    try:
        video_file = Path(video_info['file'])
        if video_file.exists():
            video_file.unlink()
            print(f"✓ Deleted: {video_file.name}")
    except Exception as e:
        print(f"⚠️ Could not delete {video_info['file']}: {e}")
```

**Result:** Video files are cleaned up AFTER previews are generated

---

### Fix #3: Add Debugging

**File:** `.github/workflows/integrated_scraper.yml`

Added logging to see what files exist:

```bash
echo "Checking temp_downloads directory..."
if [ -d "jable/temp_downloads" ]; then
  echo "Files in temp_downloads:"
  ls -lh jable/temp_downloads/
else
  echo "temp_downloads directory does not exist"
fi
```

**Result:** Can see what files are available for preview generation

---

## New Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Scraper (jable/run_continuous.py)                       │
│    - Downloads video to temp_downloads/                    │
│    - Uploads to StreamWish/LuluStream/Streamtape          │
│    - Saves metadata to database                            │
│    - KEEPS video file (GitHub Actions only) ← NEW!        │
│    - Commits database                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Preview Generation (GitHub Actions)                      │
│    - Checks temp_downloads/ for video files ← Files exist! │
│    - Generates 30-second previews                          │
│    - Uploads to Internet Archive                           │
│    - Updates database with preview URLs                    │
│    - DELETES video files ← NEW!                           │
│    - Commits database                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Frontend                                                 │
│    - Loads videos with preview URLs                        │
│    - Shows hover preview from Internet Archive             │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

1. ✅ **Video files available** for preview generation
2. ✅ **Automatic cleanup** after previews are generated
3. ✅ **Local runs unaffected** - still cleanup immediately
4. ✅ **Disk space managed** - files deleted after use
5. ✅ **Debugging enabled** - can see what files exist

## Testing

After this fix:

1. **Scraper runs** and keeps video files in GitHub Actions
2. **Preview generation finds** video files in temp_downloads
3. **Previews are generated** and uploaded to Internet Archive
4. **Database is updated** with preview_ia field
5. **Video files are deleted** after preview generation
6. **Frontend shows** hover previews

## Verification

Check GitHub Actions logs for:

```
GENERATING VIDEO PREVIEWS
========================================
Checking temp_downloads directory...
Files in temp_downloads:
-rw-r--r-- 1 runner docker 1.2G Jan 24 12:00 VIDEO-CODE.mp4  ← Files exist!

Found 1 videos needing previews
Processing: VIDEO-CODE
✓ Preview generated and uploaded: VIDEO-CODE
Processed 1/1 previews

Cleaning up video files...
✓ Deleted: VIDEO-CODE.mp4
✓ Cleanup complete
```

## Local Development

When running locally (not in GitHub Actions):
- Videos are still deleted immediately after upload
- No change to local behavior
- Preview generation must be done manually if needed

## Summary

**Problem:** Videos deleted before preview generation
**Solution:** Keep videos in GitHub Actions, delete after previews
**Result:** Preview generation now works end-to-end

The workflow will now successfully generate and upload previews for all new videos!
