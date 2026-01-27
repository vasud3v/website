# JavaGG Complete Workflow

Automated pipeline for scraping, downloading, enriching, and uploading JAV videos from JavaGG.net

## Workflow Steps

### 1. Scrape New Videos
- Scrapes latest videos from JavaGG homepage
- Tracks processed videos to avoid duplicates
- Stores progress in `database/workflow_progress.json`

### 2. Download Video
- Downloads video in highest quality available
- Tries multiple embed servers if one fails
- Uses yt-dlp for reliable downloading
- Saves to `downloaded_files/{CODE}.mp4`

### 3. Enrich Metadata
- Scrapes complete metadata from JavaGG
- Enriches with JAVDatabase (actress profiles, screenshots, etc.)
- If JAVDatabase unavailable, adds to retry queue (2-day delay)
- Saves to `database/combined_videos.json`

### 4. Generate Preview
- Creates 2-minute preview video
- Extracts 6 clips from different parts
- Saves to `downloaded_files/{CODE}_preview.mp4`

### 5. Upload Videos
- **Full Video**: Uploads to all hosting sites (StreamTape, Uploady, etc.)
- **Preview**: Uploads to Internet Archive only
- Collects all embed/download/iframe URLs

### 6. Update Metadata
- Updates `combined_videos.json` with hosting URLs
- Adds `hosting_urls`, `preview_url`, `uploaded_at` fields

### 7. Cleanup
- Deletes downloaded video files
- Deletes preview files
- Deletes temporary JSON files
- Keeps only `combined_videos.json`

## Progress Tracking

### workflow_progress.json
```json
{
  "last_scraped_page": 1,
  "processed_videos": ["CODE1", "CODE2"],
  "failed_videos": ["CODE3"],
  "pending_enrichment": [
    {
      "code": "CODE4",
      "url": "https://javgg.net/jav/code4/",
      "retry_after": 1738123456.789
    }
  ],
  "last_run": "2026-01-28T12:00:00"
}
```

### combined_videos.json Structure
```json
{
  "videos": [
    {
      "code": "SONE-572",
      "title": "...",
      "actresses": ["Miru"],
      "actress_details": [{...}],
      "screenshots": [...],
      "hosting_urls": {
        "streamtape": "https://...",
        "uploady": "https://...",
        ...
      },
      "preview_url": "https://archive.org/...",
      "uploaded_at": "2026-01-28T12:00:00"
    }
  ],
  "stats": {
    "total_videos": 100,
    "last_updated": "2026-01-28T12:00:00"
  }
}
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt
pip install yt-dlp

# Run workflow
cd javgg
python complete_workflow.py --max-videos 10
```

## GitHub Actions

### Automatic Schedule
- Runs every 6 hours automatically
- Processes up to 10 videos per run

### Manual Trigger
1. Go to Actions tab
2. Select "JavaGG Complete Workflow"
3. Click "Run workflow"
4. Set max videos (default: 10)

## Configuration

### Environment Variables
- `MAX_VIDEOS`: Maximum videos to process per run (default: 10)

### Retry Logic
- Videos without JAVDatabase data are retried after 2 days
- Failed downloads are skipped and logged
- Progress is saved after each video

## Error Handling

### Download Failures
- Tries multiple embed servers
- Logs failure and continues to next video
- Adds to `failed_videos` list

### Enrichment Failures
- If JAVDatabase unavailable, adds to `pending_enrichment`
- Retries after 2 days
- Uses JavaGG data only if still unavailable

### Upload Failures
- Continues even if some hosts fail
- Saves whatever URLs were successful
- Logs errors for debugging

## File Structure

```
javgg/
├── complete_workflow.py       # Main workflow script
├── javgg_scraper.py           # JavaGG scraper
├── javdb_enrichment.py        # JAVDatabase enrichment
├── save_to_database.py        # Database operations
└── WORKFLOW_README.md         # This file

database/
├── combined_videos.json       # Main database (KEEP)
├── workflow_progress.json     # Progress tracking
└── stats.json                 # Statistics

downloaded_files/
└── (temporary files - auto-deleted)

tools/preview_generator/
└── preview_generator.py       # Preview generation

upload_pipeline/
├── upload_to_all_hosts.py     # Multi-host uploader
└── internet_archive_uploader.py  # IA uploader
```

## Monitoring

### Check Progress
```bash
cat database/workflow_progress.json
```

### Check Database
```bash
cat database/combined_videos.json | jq '.stats'
```

### View Logs
- GitHub Actions logs available in Actions tab
- Artifacts contain full logs and database snapshots

## Troubleshooting

### Videos Not Downloading
- Check if yt-dlp is installed
- Verify embed URLs are accessible
- Check GitHub Actions logs

### JAVDatabase Enrichment Failing
- Videos will be retried after 2 days
- Check `pending_enrichment` in progress file
- Verify JAVDatabase.com is accessible

### Upload Failures
- Check hosting site credentials
- Verify upload scripts are working
- Check network connectivity

## Maintenance

### Clean Failed Videos
```python
# Remove from failed list to retry
workflow = WorkflowManager()
workflow.progress['failed_videos'] = []
workflow.save_progress()
```

### Reset Progress
```python
# Start from beginning
workflow = WorkflowManager()
workflow.progress = {
    'last_scraped_page': 1,
    'processed_videos': [],
    'failed_videos': [],
    'pending_enrichment': [],
    'last_run': None
}
workflow.save_progress()
```

## Notes

- Only `combined_videos.json` is kept as the main database
- All temporary files are deleted after processing
- Progress is tracked to avoid reprocessing
- Failed videos are logged but don't stop the workflow
- Enrichment retries happen automatically after 2 days
