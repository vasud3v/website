# Internet Archive Preview Upload

Upload preview videos to Internet Archive for **unlimited free storage** with direct MP4 URLs.

## Features

✅ **Unlimited storage** - Free forever  
✅ **Unlimited bandwidth** - No limits  
✅ **Direct MP4 URLs** - Works with HTML5 `<video>` tag  
✅ **Permanent hosting** - Videos never expire  
✅ **Fast CDN** - Global delivery  
✅ **No ads, no tracking**  

## Setup

### 1. Install Dependencies

```bash
cd internet_archive_upload
pip install -r requirements.txt
```

### 2. Create Internet Archive Account

1. Go to https://archive.org/account/signup
2. Sign up for a free account (no credit card required)
3. Verify your email

### 3. Configure Credentials

```bash
python setup_ia.py
```

This will:
- Ask for your Internet Archive email and password
- Save credentials to `.env` file
- Configure the Internet Archive library
- Test the connection

## Usage

### Upload Single Preview

```bash
python upload_to_ia.py <video_file> <video_code>
```

Example:
```bash
python upload_to_ia.py FNS-149_preview.mp4 FNS-149
```

Output:
```
============================================================
UPLOADING TO INTERNET ARCHIVE
============================================================
Video Code: FNS-149
File: FNS-149_preview.mp4
File size: 45.23 MB

Identifier: javcore-preview-fns-149
Uploading to Internet Archive...

============================================================
✓ UPLOAD SUCCESSFUL
============================================================
Direct MP4 URL: https://archive.org/download/javcore-preview-fns-149/FNS-149_preview.mp4
Details page: https://archive.org/details/javcore-preview-fns-149
============================================================

✓ Updated database for FNS-149
✓ Database saved
```

### Batch Upload All Previews

```bash
python upload_to_ia.py --batch <preview_directory>
```

Example:
```bash
python upload_to_ia.py --batch ../previews
```

This will:
1. Find all `*_preview.mp4` files in the directory
2. Upload each to Internet Archive
3. Update the database with direct URLs
4. Show a summary report

## Direct URL Format

After upload, videos are available at:
```
https://archive.org/download/javcore-preview-{code}/{code}_preview.mp4
```

Example:
```
https://archive.org/download/javcore-preview-fns-149/FNS-149_preview.mp4
```

## Database Integration

The script automatically updates `database/combined_videos.json` with:

```json
{
  "code": "FNS-149",
  "preview_ia": {
    "identifier": "javcore-preview-fns-149",
    "direct_url": "https://archive.org/download/javcore-preview-fns-149/FNS-149_preview.mp4",
    "details_url": "https://archive.org/details/javcore-preview-fns-149",
    "filename": "FNS-149_preview.mp4",
    "file_size_mb": 45.23,
    "uploaded_at": "2026-01-24T12:00:00Z"
  }
}
```

## Backend Integration

The backend endpoint (`backend/app/api/v1/endpoints/preview.py`) will automatically check for `preview_ia` and return the direct URL:

```python
@router.get("/{code}/direct-url")
async def get_preview_direct_url(code: str):
    # ... load video from database ...
    
    # Check for Internet Archive preview
    preview_ia = video.get('preview_ia', {})
    if preview_ia.get('direct_url'):
        return JSONResponse({
            "direct_url": preview_ia['direct_url'],
            "has_preview": True,
            "source": "internet_archive"
        })
```

## Frontend Usage

The VideoCard component will automatically:
1. Fetch the direct URL from `/api/preview/{code}/direct-url`
2. Play the video on hover using HTML5 `<video>` tag
3. No changes needed - it just works!

## Integration with Preview Generator

Add to your preview generation workflow:

```python
from internet_archive_upload.upload_to_ia import upload_preview_to_internet_archive, update_database_with_ia_url

# After generating preview
preview_file = f"{code}_preview.mp4"

# Upload to Internet Archive
ia_result = upload_preview_to_internet_archive(preview_file, code)

if ia_result['success']:
    # Update database
    update_database_with_ia_url(code, ia_result)
    print(f"✓ Preview uploaded: {ia_result['direct_url']}")
```

## Testing Direct URLs

Test that the URL works:

```bash
# Should download the video
curl -I https://archive.org/download/javcore-preview-fns-149/FNS-149_preview.mp4

# Should play in browser
# Just paste the URL in your browser
```

## Important Notes

### Public Content
- All videos uploaded to Internet Archive are **public**
- Anyone can view and download them
- This is fine for preview videos (they're meant to be public)
- Don't upload full videos or private content

### Permanent Storage
- Videos are **never deleted** (unless you request removal)
- Internet Archive is a digital library - content is archived permanently
- This is perfect for preview videos

### Metadata
Videos are uploaded with:
- Title: `{CODE} - Preview`
- Collection: `opensource_movies`
- License: Creative Commons BY 4.0
- Description: `Preview video for {CODE}`

### Processing Time
- Upload is instant
- Videos may take 5-10 minutes to process
- Direct URLs work immediately after processing

## Troubleshooting

### "Authentication failed"
- Check your email and password in `.env`
- Run `python setup_ia.py` again
- Make sure you verified your email

### "Identifier already exists"
- Each video code can only be uploaded once
- To re-upload, delete the item from Internet Archive first
- Or use a different identifier

### "File not found"
- Check the file path is correct
- Make sure the file exists
- Use absolute paths if needed

### "Database not updated"
- Check `database/combined_videos.json` exists
- Make sure the video code exists in the database
- Check file permissions

## Advantages Over Other Services

| Feature | Internet Archive | Backblaze B2 | Bunny.net |
|---------|-----------------|--------------|-----------|
| Storage | ✅ Unlimited | ⚠️ 10GB free | ❌ 14-day trial |
| Bandwidth | ✅ Unlimited | ⚠️ 1GB/day | ❌ Paid |
| Direct URLs | ✅ Yes | ✅ Yes | ✅ Yes |
| Cost | ✅ Free forever | ⚠️ Free tier | ❌ Paid |
| Privacy | ⚠️ Public only | ✅ Private | ✅ Private |

**Best for**: Preview videos (public content, unlimited storage)

## Support

For issues with:
- **Upload script**: Check this README or code comments
- **Internet Archive**: https://help.archive.org/
- **API integration**: Check backend/frontend code

## License

This upload script is provided as-is for use with your video preview system.
