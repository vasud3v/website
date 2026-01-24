# Video Previews Directory

This directory stores preview videos/GIFs for hover effects on video cards.

## File Naming Convention

Preview files should be named: `{VIDEO_CODE}_preview.{ext}`

Examples:
- `FNS-149_preview.gif` - GIF preview (recommended for hover)
- `FNS-149_preview.mp4` - MP4 preview
- `FNS-149_preview.webm` - WebM preview

## Priority Order

When a user hovers over a video card, the system checks for previews in this order:
1. GIF (`.gif`) - Best for hover previews, smaller file size
2. MP4 (`.mp4`) - Good quality, widely supported
3. WebM (`.webm`) - Smaller than MP4, good browser support

## Generating Previews

To generate preview GIFs from your preview videos:

```bash
# Using FFmpeg to convert preview MP4 to GIF
ffmpeg -i {VIDEO_CODE}_preview.mp4 -vf "fps=10,scale=480:-1:flags=lanczos" -c:v gif {VIDEO_CODE}_preview.gif

# Or use your existing preview generator with GIF output
python preview_generator/preview_generator.py video.mp4 --gif
```

## API Endpoint

Previews are served via: `GET /api/preview/{VIDEO_CODE}`

The endpoint automatically detects and serves the appropriate format.
