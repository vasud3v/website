# Known Issues

## 1. Preview Generation Fails - Video Detected as PNG
**Status:** Non-critical (workflow continues)

**Symptom:**
```
[AdultDetector] Format data: {'format_name': 'png_pipe', ...}
✗ Failed to get video info
❌ Preview generation failed
```

**Cause:**
The downloaded video file is being detected as PNG images instead of MP4. This happens when:
- yt-dlp couldn't properly merge M3U8 fragments
- The stream is encrypted or protected
- Download was incomplete

**Impact:**
- Preview video is not generated
- Main video still uploads successfully
- Workflow continues normally

**Workaround:**
- Preview generation is optional
- Full video is still uploaded to all hosts
- Users can watch the full video

**Future Fix:**
- Try alternative download methods
- Validate video file after download
- Use ffmpeg to re-encode if needed

## 2. JAVDatabase Not Available for New Releases
**Status:** Expected behavior

**Symptom:**
```
❌ Code mismatch in title
⚠️  Video not found on JAVDatabase
```

**Cause:**
- New releases take 2-7 days to be indexed on JAVDatabase

**Solution:**
- Video is added to retry queue
- Will automatically retry after 2 days
- Uses JavaGG data in the meantime

## 3. Some Embed URLs Not Supported
**Status:** Limitation of yt-dlp

**Symptom:**
```
❌ yt-dlp failed
⚠️ Download not supported for this embed type
```

**Cause:**
- Some video hosts use custom encryption
- yt-dlp doesn't support all embed types

**Workaround:**
- Video is marked as failed
- Will be skipped in future runs
- Manual download may be needed
