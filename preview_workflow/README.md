# Complete Preview Workflow

Automated workflow to generate preview videos and upload to Internet Archive.

## 🎯 What It Does

1. ✅ **Generates preview video** from full video (10 clips × 3 seconds)
2. ✅ **Uploads to Internet Archive** (unlimited free hosting)
3. ✅ **Updates database** with preview URL
4. ✅ **Cleans up** temporary files
5. ✅ **Frontend automatically shows** preview on hover

## 🚀 Quick Start

### Single Video

```bash
cd preview_workflow
python generate_and_upload_preview.py <video_file> <video_code> [title]
```

Example:
```bash
python generate_and_upload_preview.py ../MIDA-479.mp4 MIDA-479 "MIDA-479 Title"
```

### Batch Processing

```bash
python generate_and_upload_preview.py --batch <video_directory> [database_path]
```

Example:
```bash
python generate_and_upload_preview.py --batch ../videos ../database/combined_videos.json
```

## 📋 Prerequisites

### 1. Install Dependencies

```bash
# Preview generator dependencies
pip install opencv-python numpy ffmpeg-python

# Internet Archive
pip install internetarchive

# Already installed
pip install requests
```

### 2. Configure Internet Archive

Already done! Your credentials are in `internet_archive_upload/.env`

## 📊 Workflow Steps

### Step 1: Generate Preview
- Analyzes video for best scenes
- Extracts 10 clips (3 seconds each)
- Combines into 30-second preview
- Compresses to 480p for fast loading
- Output: `{CODE}_preview.mp4`

### Step 2: Upload to Internet Archive
- Uploads preview to IA
- Gets permanent direct URL
- Format: `https://archive.org/download/javcore-preview-{code}/{code}_preview.mp4`

### Step 3: Update Database
- Adds `preview_ia` to video entry:
```json
{
  "code": "MIDA-479",
  "preview_ia": {
    "identifier": "javcore-preview-mida-479",
    "direct_url": "https://archive.org/download/javcore-preview-mida-479/MIDA-479_preview.mp4",
    "details_url": "https://archive.org/details/javcore-preview-mida-479",
    "filename": "MIDA-479_preview.mp4",
    "file_size_mb": 15.4,
    "uploaded_at": "2026-01-24T12:00:00",
    "generated_at": "2026-01-24T12:00:00"
  }
}
```

### Step 4: Cleanup
- Removes local preview file
- Keeps only the IA URL

## 🎬 Frontend Integration

**Already working!** No code changes needed.

When user hovers over video card:
1. Frontend calls: `GET /api/preview/{code}/direct-url`
2. Backend returns: `{"direct_url": "https://archive.org/download/...", "source": "internet_archive"}`
3. Video plays in `<video>` tag

## 📁 File Structure

```
preview_workflow/
├── generate_and_upload_preview.py  # Main workflow script
└── README.md                       # This file

preview_generator/
├── preview_generator.py            # Preview generation logic
├── scene_detector.py              # Scene detection
└── ...

internet_archive_upload/
├── upload_to_ia.py                # IA upload logic
├── .env                           # Your credentials
└── ...

database/
└── combined_videos.json           # Video database (auto-updated)
```

## 💡 Usage Examples

### Example 1: Process Downloaded Video

```bash
# After downloading a video
python generate_and_upload_preview.py /path/to/MIDA-479.mp4 MIDA-479
```

Output:
```
============================================================
PREVIEW GENERATION & UPLOAD WORKFLOW
============================================================
Video Code: MIDA-479
Video Path: /path/to/MIDA-479.mp4
============================================================

[1/3] Generating preview video...
------------------------------------------------------------
✓ Preview generated: MIDA-479_preview.mp4
  Size: 15.23 MB
  Duration: ~30 seconds

[2/3] Uploading to Internet Archive...
------------------------------------------------------------
✓ Uploaded to Internet Archive
  Direct URL: https://archive.org/download/javcore-preview-mida-479/MIDA-479_preview.mp4

[3/3] Updating database...
------------------------------------------------------------
✓ Updated database for MIDA-479
✓ Database saved
✓ Cleaned up local preview file

============================================================
✓ WORKFLOW COMPLETE!
============================================================
Preview URL: https://archive.org/download/javcore-preview-mida-479/MIDA-479_preview.mp4
Video Code: MIDA-479
============================================================
```

### Example 2: Batch Process All Videos

```bash
# Process all videos in a folder
python generate_and_upload_preview.py --batch ../downloaded_videos
```

Output:
```
Found 10 video files
============================================================

[1/10] Processing: MIDA-479.mp4
... (workflow for each video)

============================================================
BATCH PROCESSING SUMMARY
============================================================
Total: 10
Successful: 9
Failed: 1

✓ Successful:
  - MIDA-479: https://archive.org/download/javcore-preview-mida-479/MIDA-479_preview.mp4
  - FNS-149: https://archive.org/download/javcore-preview-fns-149/FNS-149_preview.mp4
  ...

❌ Failed:
  - BAD-001: Preview generation error: File corrupted
============================================================
```

## 🔧 Integration with Existing Workflow

### Option 1: Manual Processing

After downloading videos:
```bash
python generate_and_upload_preview.py video.mp4 CODE-123
```

### Option 2: Automated in Download Script

Add to your download script:
```python
# After downloading video
from preview_workflow.generate_and_upload_preview import generate_and_upload_preview

result = generate_and_upload_preview(
    video_path=downloaded_file,
    video_code=code,
    video_title=title
)

if result['success']:
    print(f"✓ Preview ready: {result['preview_url']}")
```

### Option 3: Batch Process Existing Videos

```bash
# Process all videos that don't have previews yet
python generate_and_upload_preview.py --batch ../videos
```

## ⚙️ Configuration

### Preview Settings

Edit `generate_and_upload_preview.py`:

```python
# Preview generation settings
generator.generate_preview(
    output_path=preview_output,
    num_clips=10,              # Number of clips (default: 10)
    clip_duration=3,           # Seconds per clip (default: 3)
    target_resolution=(854, 480),  # Resolution (default: 480p)
    create_gif=False           # Don't create GIF
)
```

### Adjust for Your Needs

**Shorter previews (faster loading):**
```python
num_clips=5,
clip_duration=2,
# Result: 10-second preview
```

**Higher quality:**
```python
target_resolution=(1280, 720),  # 720p
# Result: Larger file, better quality
```

**Lower quality (faster loading):**
```python
target_resolution=(640, 360),  # 360p
# Result: Smaller file, faster loading
```

## 🎯 Best Practices

1. **Process videos after download** - Generate previews immediately
2. **Use 480p resolution** - Good balance of quality and size
3. **Keep previews short** - 30 seconds is enough for hover preview
4. **Batch process** - More efficient for multiple videos
5. **Monitor IA uploads** - Check if videos stay up

## 🐛 Troubleshooting

### "Preview generation failed"
- Check if video file is valid
- Install: `pip install opencv-python ffmpeg-python`
- Check video codec compatibility

### "Internet Archive upload failed"
- Check credentials in `internet_archive_upload/.env`
- Check internet connection
- Verify account is active

### "Database not updated"
- Check `database/combined_videos.json` exists
- Verify video code exists in database
- Check file permissions

### "Frontend not showing preview"
- Check backend is running (port 8000)
- Verify API returns preview URL
- Check browser console for errors
- Wait 5-10 minutes for IA processing

## 📊 Performance

- **Preview generation**: 1-5 minutes per video (depends on length)
- **Upload to IA**: 10-60 seconds (depends on file size)
- **Database update**: < 1 second
- **Total**: ~2-6 minutes per video

**Batch processing 100 videos**: ~3-10 hours

## 🎉 Success Indicators

✅ Preview file generated locally  
✅ Upload to IA successful  
✅ Direct URL accessible  
✅ Database updated  
✅ Backend API returns URL  
✅ Frontend shows preview on hover  

## 📚 Related Documentation

- Preview Generator: `preview_generator/README.md`
- Internet Archive Upload: `internet_archive_upload/README.md`
- Backend API: `backend/app/api/v1/endpoints/preview.py`
- Frontend Component: `frontend/src/components/VideoCard.tsx`
