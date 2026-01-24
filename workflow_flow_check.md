# Complete Workflow Flow Verification

## ✅ WORKFLOW STEPS (run_continuous.py)

### Step 1: Scrape Metadata
- ✅ `scraper.scrape_video(url)` - Gets video data from Jable.tv
- ✅ Returns `VideoData` object with code, title, m3u8_url, etc.

### Step 2: Download Video
- ✅ `HLSDownloader(32).download(m3u8_url, ts_file, code)`
- ✅ Downloads video segments with AES decryption
- ✅ **Browser Restart on 403 Errors:**
  - Detects high failure rate (>50%)
  - Closes browser: `scraper.driver.quit()`
  - Waits 10 seconds
  - Restarts browser: `scraper._init_driver()`
  - Re-scrapes video: `scraper.scrape_video(url)` to get fresh M3U8
  - Retries download up to 3 times total
- ✅ Saves to `temp_downloads/{code}.ts`

### Step 3: Convert to MP4
- ✅ `convert_to_mp4(ts_file, mp4_file)`
- ✅ Converts TS to MP4 format
- ✅ Verifies MP4 integrity

### Step 3.5: Preview Note
- ✅ Logs that preview will be generated after full video upload
- ✅ Sets `preview_result = None`

### Step 4: Upload Full Video to StreamWish
- ✅ `upload_all(mp4_file, code, title, video_data)`
- ✅ Uploads to StreamWish (primary)
- ✅ Falls back to other hosts if StreamWish fails
- ✅ Gets `folder_name` from upload results
- ✅ Returns embed URLs and hosting info

### Step 4.5: Generate and Upload Preview to Internet Archive
- ✅ Checks if `ADVANCED_PREVIEW_AVAILABLE`
- ✅ Calls `generate_and_upload_preview(mp4_file, code, title)`
- ✅ **Preview Generation:**
  - Uses `PreviewGenerator` class
  - Uses `AdultSceneDetector` for intelligent scene selection
  - Multi-factor analysis: 40% skin + 30% motion + 20% audio + 10% complexity
  - Generates 10 clips × 3 seconds = 30 second preview
  - Resolution: 480p for fast loading
- ✅ **Internet Archive Upload:**
  - Uploads preview to IA
  - Gets identifier, direct_url, details_url
- ✅ **Returns:**
  - `success`: True/False
  - `preview_video_url`: Direct URL to preview
  - `preview_file_size_mb`: File size
  - `preview_duration`: Duration in seconds
  - `num_clips`: Number of clips
  - `identifier`: IA identifier
  - `details_url`: IA details page
- ✅ Cleans up local preview file

### Step 5: Save Metadata to Database
- ✅ Checks if `JAVDB_INTEGRATION_AVAILABLE`
- ✅ If JAVDatabase available: Skips initial save (will save merged data)
- ✅ If no JAVDatabase: Saves now with `save_video()`
- ✅ **Saved Fields:**
  - Basic: code, title, source_url, thumbnail_url
  - Metadata: duration, views, likes, release_date
  - Categories: categories[], models[], tags[]
  - Preview: preview_video_url, preview_duration, preview_clips, preview_file_size_mb
  - **Internet Archive:** preview_ia{identifier, direct_url, details_url, file_size_mb}
  - Hosting: hosting{streamwish: {embed_url, watch_url, etc.}}

### Step 5.5: Enrich with JAVDatabase
- ✅ Checks if `JAVDB_INTEGRATION_AVAILABLE`
- ✅ Builds `jable_data` dict with all metadata
- ✅ Calls `enrich_with_javdb(jable_data, headless=True)`
- ✅ **JAVDatabase Enrichment:**
  - Scrapes additional metadata from JAVDatabase.com
  - Gets: actresses with images, studio, series, tags
  - Merges with Jable data
  - Saves to `database/combined_videos.json`
- ✅ **Fallback:** If enrichment fails, saves Jable data only

### Step 6: Cleanup
- ✅ Deletes local MP4 file
- ✅ Releases disk reservation
- ✅ Cleans up temp files

---

## ✅ DATA FLOW

```
Jable.tv
   ↓ (scrape)
VideoData {code, title, m3u8_url, thumbnail, categories, models}
   ↓ (download)
video.ts (encrypted segments)
   ↓ (convert)
video.mp4
   ↓ (upload full)
StreamWish {embed_url, folder_name}
   ↓ (generate preview)
preview.mp4 (30s, 10 clips, intelligent selection)
   ↓ (upload preview)
Internet Archive {identifier, direct_url}
   ↓ (enrich)
JAVDatabase {actresses, studio, series, additional tags}
   ↓ (merge & save)
combined_videos.json {
  code, title, source_url,
  categories[], models[], tags[],
  hosting: {streamwish: {embed_url}},
  preview_video_url, preview_duration, preview_clips,
  preview_ia: {identifier, direct_url, details_url},
  actresses[], studio, series
}
```

---

## ✅ ERROR HANDLING

### 403 Errors (Video Download)
1. ✅ Downloader detects high failure rate (>50%)
2. ✅ Returns False to trigger restart
3. ✅ Workflow closes browser
4. ✅ Waits 10 seconds
5. ✅ Restarts browser with fresh session
6. ✅ Re-scrapes video for fresh M3U8 URL
7. ✅ Retries download (up to 3 attempts total)

### Preview Generation Failure
1. ✅ Logs warning
2. ✅ Sets preview_result = None
3. ✅ Continues with workflow (preview is optional)
4. ✅ Saves video without preview metadata

### JAVDatabase Enrichment Failure
1. ✅ Logs warning
2. ✅ Falls back to saving Jable data only
3. ✅ Video is still saved to database

### Upload Failure
1. ✅ Tries StreamWish first
2. ✅ Falls back to alternative hosts
3. ✅ If all fail: Marks video as failed
4. ✅ Cleans up and moves to next video

---

## ✅ CRITICAL CHECKS PASSED

1. ✅ All core files exist
2. ✅ All preview generator files exist
3. ✅ Workflow integration imports correct
4. ✅ Preview metadata fields implemented
5. ✅ Internet Archive metadata saved
6. ✅ Browser restart logic implemented
7. ✅ Preview workflow returns correct keys
8. ✅ JAVDatabase integration active
9. ✅ Database saving works correctly
10. ✅ Error handling comprehensive

---

## ✅ WORKFLOW IS COMPLETE AND CORRECT

The workflow is properly implemented with:
- ✅ Full video download with 403 error handling
- ✅ Browser restart on persistent errors
- ✅ Intelligent preview generation (AdultSceneDetector)
- ✅ Preview upload to Internet Archive
- ✅ JAVDatabase metadata enrichment
- ✅ Complete metadata saving with preview info
- ✅ Comprehensive error handling
- ✅ Proper cleanup

**Status: READY FOR PRODUCTION** 🚀
