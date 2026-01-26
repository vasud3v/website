# 24/7 Continuous Video Scraper & Uploader

Automated GitHub Actions workflow that runs continuously 24/7 with 5-hour work cycles.

## 🎯 Workflow Overview

The workflow automatically:

1. **🔍 Monitors** for new videos on Javmix.TV
2. **🎬 Scrapes** video metadata and URLs
3. **📥 Downloads** best quality videos (32 parallel workers)
4. **🎞️ Creates** preview videos
5. **📚 Enriches** metadata from JAVDatabase
6. **📤 Uploads** to all configured hosts
7. **💾 Updates** combined_videos.json with all host links

## ⏰ Schedule

- **Runs every 5 hours** automatically
- **290 minutes** of active processing per run
- **10 minutes** buffer for cleanup and state saving
- **Continuous 24/7** operation

## 🚀 Features

### Parallel Processing
- **32 parallel workers** for downloading
- **5 parallel workers** for uploading
- Optimized for maximum throughput

### Smart State Management
- Resumes from last position
- Caches database state between runs
- No duplicate processing

### Comprehensive Workflow
```
New Video Detection
    ↓
Metadata Scraping
    ↓
Video Download (32 workers)
    ↓
Preview Generation
    ↓
Preview Upload to Internet Archive
    ↓
JAVDatabase Enrichment
    ↓
Multi-Host Upload (5 workers)
    ↓
Database Update
```

### Supported Upload Hosts
- SeekStreaming
- Streamtape
- Turboviplay
- Vidoza
- Uploady
- Upload18

## 📋 Setup Instructions

### 1. Configure Secrets

Add these secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

#### Required Secrets:
```
# Upload Hosts
SEEKSTREAMING_API_KEY
STREAMTAPE_USERNAME
STREAMTAPE_PASSWORD
TURBOVIPLAY_EMAIL
TURBOVIPLAY_USERNAME
TURBOVIPLAY_PASSWORD
TURBOVIPLAY_API_KEY
VIDOZA_EMAIL
VIDOZA_PASSWORD
VIDOZA_API_KEY
UPLOADY_EMAIL
UPLOADY_USERNAME
UPLOADY_API_KEY
UPLOAD18_API_KEY

# Internet Archive (for preview videos)
IA_ACCESS_KEY
IA_SECRET_KEY
```

**Get Internet Archive Keys:**
1. Create account at https://archive.org
2. Go to https://archive.org/account/s3.php
3. Copy your Access Key and Secret Key
4. Add them as GitHub secrets

### 2. Enable GitHub Actions

1. Go to **Settings → Actions → General**
2. Enable **"Allow all actions and reusable workflows"**
3. Set **Workflow permissions** to **"Read and write permissions"**

### 3. Manual Trigger (Optional)

You can manually trigger the workflow:

1. Go to **Actions** tab
2. Select **"24/7 Continuous Video Scraper & Uploader"**
3. Click **"Run workflow"**
4. Configure options:
   - **Max videos**: Limit number of videos (0 = unlimited)
   - **Workers**: Number of parallel workers (default: 32)

## 📊 Monitoring

### View Progress

1. Go to **Actions** tab
2. Click on the running workflow
3. View real-time logs

### Check Results

After each run, artifacts are uploaded:
- `workflow-results-{run_number}` contains:
  - Database files
  - Upload results
  - Log files

### Summary Report

Each run generates a summary showing:
- Videos processed
- Videos downloaded
- Videos enriched
- Videos uploaded
- Runtime
- Success rate

## 🔧 Configuration

### Adjust Runtime

Edit `.github/workflows/continuous-scraper.yml`:

```yaml
env:
  MAX_RUNTIME_MINUTES: 290  # Change this value
```

### Adjust Schedule

Edit the cron expression:

```yaml
schedule:
  - cron: '0 */5 * * *'  # Every 5 hours
  # Examples:
  # - cron: '0 */3 * * *'  # Every 3 hours
  # - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 0 * * *'    # Once per day at midnight
```

### Adjust Workers

Edit the workflow file or use manual trigger:

```yaml
workers: 32  # Change number of parallel workers
```

## 📁 Output Structure

### Database Files

```
database/
├── combined_videos.json          # Main database with all videos
├── seekstreaming_host.json       # SeekStreaming uploads
├── streamtape_host.json          # Streamtape uploads
├── turboviplay_host.json         # Turboviplay uploads
├── vidoza_host.json              # Vidoza uploads
├── uploady_host.json             # Uploady uploads
└── internet_archive_previews.json # Internet Archive preview uploads
```

### Combined Videos JSON Structure

```json
{
  "videos": [
    {
      "code": "MIDA-486",
      "title": "Video Title",
      "downloaded": true,
      "download_path": "downloaded_files/MIDA-486.mp4",
      "preview_path": "downloaded_files/MIDA-486_preview.mp4",
      "enriched": true,
      "preview_ia": {
        "identifier": "javmix-preview-mida-486-20260127",
        "direct_mp4_link": "https://archive.org/download/javmix-preview-mida-486-20260127/MIDA-486_preview.mp4",
        "player_link": "https://archive.org/details/javmix-preview-mida-486-20260127",
        "embed_code": "<iframe src=\"https://archive.org/embed/javmix-preview-mida-486-20260127\" width=\"640\" height=\"480\" frameborder=\"0\" allowfullscreen></iframe>",
        "uploaded_at": "2026-01-27T12:00:00"
      },
      "uploaded_hosts": {
        "seekstreaming": {
          "video_player": "https://...",
          "video_downloader": "https://...",
          "embed_code": "<iframe>..."
        },
        "streamtape": {
          "video_player": "https://...",
          "video_downloader": "https://...",
          "embed_code": "<iframe>..."
        }
      },
      "processed_at": "2026-01-27T12:00:00"
    }
  ],
  "stats": {
    "total_videos": 1000,
    "total_processed": 500
  }
}
```

## 🛠️ Troubleshooting

### Workflow Not Running

1. Check if Actions are enabled
2. Verify cron schedule syntax
3. Check workflow permissions

### Upload Failures

1. Verify all secrets are set correctly
2. Check API key validity
3. Review error logs in Actions tab

### Download Failures

1. Check if video URLs are valid
2. Verify ffmpeg installation
3. Check network connectivity

### Out of Storage

GitHub Actions runners have limited storage:
- Videos are deleted after upload
- Only database files are cached
- Artifacts expire after 7 days

## 📈 Performance

### Expected Throughput

With 32 workers and 5-hour runtime:
- **~50-100 videos** per run (depends on video size)
- **~240-480 videos** per day (5 runs)
- **~7,200-14,400 videos** per month

### Optimization Tips

1. **Increase workers** for faster downloads
2. **Adjust runtime** for longer processing
3. **Reduce preview quality** for faster generation
4. **Disable enrichment** if not needed

## 🔒 Security

- All credentials stored as GitHub Secrets
- Secrets never exposed in logs
- Automatic cleanup of sensitive data
- No credentials in repository

## 📝 Logs

Logs include:
- Video scraping progress
- Download status
- Upload results
- Error messages
- Performance metrics

## 🎯 Next Steps

1. **Monitor first run** to ensure everything works
2. **Adjust configuration** based on performance
3. **Check database** for uploaded videos
4. **Review artifacts** for any issues

## 💡 Tips

- Start with a **small max_videos** value to test
- Monitor **storage usage** in Actions
- Check **API rate limits** for upload hosts
- Use **manual trigger** for testing

## 🆘 Support

If you encounter issues:
1. Check the **Actions logs**
2. Review **error messages**
3. Verify **secrets configuration**
4. Test **individual components** locally

---

**Happy Scraping! 🎬**
