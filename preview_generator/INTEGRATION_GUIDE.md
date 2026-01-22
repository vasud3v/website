# Preview Generator - Integration Guide

## Overview

Advanced video preview generation system integrated with GitHub Actions workflow. Automatically creates smart previews with scene detection and uploads them to hosting.

## Features

✅ **Automatic Scene Detection** - Finds interesting moments
✅ **Motion Analysis** - Identifies high-action segments
✅ **Parallel Processing** - Fast multi-core extraction
✅ **Auto Upload** - Uploads to StreamWish automatically
✅ **Metadata Integration** - Saves preview URLs in database
✅ **GitHub Actions Ready** - Works in CI/CD pipeline
✅ **Fallback Support** - Falls back to simple preview if advanced fails

## How It Works in Workflow

### 1. Video Processing Pipeline

```
Download Video → Convert to MP4 → Generate Preview → Upload Main Video → Upload Preview → Save Metadata
```

### 2. Preview Generation Steps

1. **Analyze Video** - Detects scenes and motion (parallel)
2. **Extract Clips** - Gets 10 clips × 3 seconds (parallel)
3. **Create Preview** - Concatenates into 30-second preview
4. **Upload Preview** - Uploads to same folder as main video
5. **Save Metadata** - Stores preview URL in database

### 3. Metadata Saved

```json
{
  "code": "START-451",
  "title": "Video Title",
  "preview_video_url": "https://streamwish.com/e/abc123",
  "preview_gif_url": "https://streamwish.com/e/abc456",
  "preview_duration": 30.0,
  "preview_clips": 10,
  "preview_file_size_mb": 18.5,
  "preview_generated": true
}
```

## Integration in run_continuous.py

### Import

```python
# Advanced preview (with scene detection)
from workflow_integration import integrate_with_workflow
ADVANCED_PREVIEW_AVAILABLE = True

# Fallback to simple preview
from create_video_preview import create_preview
PREVIEW_CREATION_AVAILABLE = True
```

### Usage

```python
# After MP4 conversion, before main video upload
preview_result = integrate_with_workflow(
    video_path=mp4_file,
    video_code=code,
    video_title=video_data.title,
    upload_function=upload_to_streamwish,
    folder_name=f"JAV_VIDEOS/{code}",
    enable_preview=True,
    enable_gif=False  # Optional GIF
)

# Save with metadata
save_video(video_data, upload_results, thumbnail_url, preview_result)
```

## Configuration

### Preview Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `num_clips` | 10 | Number of clips to extract |
| `clip_duration` | 3.0 | Duration of each clip (seconds) |
| `resolution` | 720 | Target height (width auto) |
| `crf` | 28 | Compression (18=best, 28=smaller) |
| `fps` | 30 | Frame rate |
| `parallel` | True | Use multi-core processing |
| `create_gif` | False | Also create GIF version |

### Folder Structure

```
JAV_VIDEOS/
  ├── START-451/
  │   ├── START-451.mp4 (main video)
  │   └── START-451 - PREVIEW.mp4 (preview)
  └── PRED-842/
      ├── PRED-842.mp4
      └── PRED-842 - PREVIEW.mp4
```

## Performance

### Processing Time

| Video Length | Preview Time | Speedup (Parallel) |
|--------------|--------------|-------------------|
| 30 minutes | ~2-3 minutes | 3-4x faster |
| 60 minutes | ~4-6 minutes | 3-4x faster |
| 120 minutes | ~8-12 minutes | 3-4x faster |

### File Sizes

| Resolution | Duration | Typical Size |
|------------|----------|--------------|
| 720p | 30s | 15-20 MB |
| 480p | 30s | 8-12 MB |
| GIF 480px | 30s | 5-10 MB |

## GitHub Actions

### Workflow Integration

The preview generator works automatically in GitHub Actions:

1. **FFmpeg Available** - Pre-installed in ubuntu-latest
2. **Parallel Processing** - Uses all available CPU cores
3. **Memory Efficient** - Cleans up temp files
4. **Error Handling** - Continues if preview fails
5. **Logging** - Detailed progress output

### Environment Variables

No special environment variables needed. Uses same API keys as main upload:

- `STREAMWISH_API_KEY`
- `LULUSTREAM_API_KEY` (fallback)

## Error Handling

### Graceful Degradation

1. **Advanced Preview Fails** → Falls back to simple preview
2. **Simple Preview Fails** → Continues without preview
3. **Upload Fails** → Logs error, continues workflow
4. **Scene Detection Fails** → Uses evenly spaced clips

### Logs

```
[1/5] Analyzing video...
✓ Video: 3455.7s, 1920x1080, 30.00fps

[2/5] Detecting scenes and analyzing motion...
[SceneDetector] Using 12 parallel workers
✓ Generated 10 smart timestamps

[3/5] Extracting clips...
[ClipExtractor] Using 10 parallel workers
✓ Extracted 10 clips

[4/5] Creating preview video...
✓ Preview created: video_preview.mp4 (18.5 MB)

[5/5] Skipping GIF creation
```

## Troubleshooting

### "Advanced preview not available"

- Check if `preview_generator` folder exists
- Verify Python can import modules
- Falls back to simple preview automatically

### "Preview generation failed"

- Check FFmpeg is installed
- Verify video file is valid
- Check disk space (needs ~2GB free)
- Workflow continues without preview

### "Preview upload failed"

- Check API keys are set
- Verify StreamWish quota
- Falls back to LuluStream if needed
- Workflow continues without preview URL

## Comparison with Industry

| Feature | This System | Pornhub | Xvideos |
|---------|-------------|---------|---------|
| Scene Detection | ✅ Auto | ✅ Auto | ✅ Auto |
| Motion Analysis | ✅ Yes | ✅ Yes | ✅ Yes |
| Parallel Processing | ✅ Yes | ✅ Yes | ✅ Yes |
| Smart Selection | ✅ Yes | ✅ Yes | ✅ Yes |
| Auto Upload | ✅ Yes | ✅ Yes | ✅ Yes |
| Metadata Integration | ✅ Yes | ✅ Yes | ✅ Yes |
| GIF Support | ✅ Optional | ✅ Yes | ✅ Yes |
| Quality | 720p/30fps | 720p/30fps | 480p/24fps |
| File Size | 15-20 MB | 15-25 MB | 10-15 MB |

## Testing

### Local Testing

```bash
# Test preview generation
cd preview_generator
python preview_generator.py ../video.mp4 --clips 10 --duration 3

# Test workflow integration
python workflow_integration.py ../video.mp4 START-451 "Video Title"
```

### In Workflow

Preview generation runs automatically after MP4 conversion. Check logs for:

```
🎬 Step 3.5: Creating and uploading preview video...
✓ Preview created and uploaded
   URL: https://streamwish.com/e/abc123
   Size: 18.5 MB
   Duration: 30.0s
   Clips: 10
```

## Future Enhancements

- [ ] AI-based scene scoring
- [ ] Face detection for better clip selection
- [ ] Audio analysis for interesting moments
- [ ] Multiple quality versions (480p, 720p, 1080p)
- [ ] Adaptive clip duration based on video length
- [ ] Thumbnail sprite sheet generation
- [ ] WebVTT timeline preview support

## License

MIT License - Free to use and modify
