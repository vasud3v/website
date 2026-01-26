# SeekStreaming Uploader

Automatic video uploader for SeekStreaming with correct video ID extraction.

## Files

- `seekstreaming_uploader.py` - Main uploader class
- `simple_upload.py` - Simple command-line upload script
- `video_urls_manager.py` - Database manager for video URLs

## Usage

### Simple Upload

```bash
python simple_upload.py <video_path> [title]
```

**Examples:**
```bash
python simple_upload.py ../test.mp4
python simple_upload.py ../video.mp4 "My Video Title"
python simple_upload.py C:\Videos\movie.mp4 "Movie Title"
```

### In Your Code

```python
from seekstreaming_uploader import SeekstreamingUploader
from video_urls_manager import VideoURLManager

# Upload
uploader = SeekstreamingUploader(api_key="your_api_key")
result = uploader.upload("video.mp4", title="My Video")

if result['success']:
    print(f"Video ID: {result['video_id']}")
    print(f"Player URL: {result['all_urls']['video_player']}")
    print(f"Embed Code: {result['all_urls']['embed_code']}")
    
    # Save to database
    video_info = {
        'title': 'My Video',
        'filename': 'video.mp4',
        'file_size_mb': 150
    }
    url_manager = VideoURLManager()
    url_manager.add_video(video_info, result)
```

## Output Format

The uploader automatically extracts the correct video ID and generates URLs using your custom domain:

```json
{
  "success": true,
  "video_id": "abc12",
  "all_urls": {
    "video_player": "https://javcore.embedseek.com/#abc12",
    "video_downloader": "https://javcore.embedseek.com/#abc12",
    "embed_code": "<iframe src=\"https://javcore.embedseek.com/#abc12\" width=\"100%\" height=\"100%\" frameborder=\"0\" allowfullscreen></iframe>"
  }
}
```

## Database

Videos are automatically saved to `database/seekstreaming_host.json`:

```json
{
  "videos": [
    {
      "id": 1,
      "title": "My Video",
      "filename": "video.mp4",
      "file_size_mb": 150.5,
      "upload_date": "2026-01-26 23:13:23",
      "video_player": "https://javcore.embedseek.com/#abc12",
      "video_downloader": "https://javcore.embedseek.com/#abc12",
      "embed_code": "<iframe src=\"https://javcore.embedseek.com/#abc12\" width=\"100%\" height=\"100%\" frameborder=\"0\" allowfullscreen></iframe>"
    }
  ],
  "stats": {
    "total_videos": 1,
    "total_size_mb": 150.5
  }
}
```

## Configuration

Add to `.env` file:

```env
SEEKSTREAMING_API_KEY=your_api_key_here
```

## Features

✅ Automatic video ID extraction from upload response  
✅ Custom domain URLs (javcore.embedseek.com)  
✅ 50 MB chunk size (optimized for SeekStreaming)  
✅ Progress bar with speed and ETA  
✅ Automatic database saving  
✅ Connection pooling for faster uploads  
✅ Retry logic for failed chunks  

## Technical Details

- Uses TUS resumable upload protocol
- Chunk size: 50 MB (52,428,800 bytes)
- Extracts actual video ID from PATCH response body
- Average upload speed: 1.5-2.5 MB/s
