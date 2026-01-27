# JavaGG Automated Workflow

Complete automation pipeline for scraping, enriching, and uploading JAV videos from JavaGG.net

## Features

- **JavaGG Scraper**: Extracts complete metadata (titles, actresses, tags, duration, release date, etc.)
- **JAVDatabase Enrichment**: Adds comprehensive actress profiles, high-quality screenshots, and additional metadata
- **Automated Downloads**: Downloads videos using yt-dlp with multiple server fallback
- **Preview Generation**: Creates 2-minute preview videos
- **Multi-Host Upload**: Uploads to all hosting sites + Internet Archive for previews
- **Progress Tracking**: Never loses data, tracks everything in `database/combined_videos.json`
- **GitHub Actions**: Runs automatically every 6 hours

## Quick Start

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt
pip install yt-dlp

# Run workflow (processes 10 videos)
cd javgg
python complete_workflow.py --max-videos 10
```

### GitHub Actions

The workflow runs automatically every 6 hours. You can also trigger it manually:

1. Go to Actions tab in GitHub
2. Select "JavaGG Complete Workflow"
3. Click "Run workflow"
4. Set max videos (default: 10)

## File Structure

```
javgg/
├── javgg_scraper.py           # JavaGG scraper
├── javdb_scraper_improved.py  # JAVDatabase scraper with actress profiles
├── javdb_enrichment.py        # Enrichment logic
├── save_to_database.py        # Database operations
├── complete_workflow.py       # Main workflow script
├── run_scraper.py             # Simple scraper runner
├── requirements.txt           # Python dependencies
└── WORKFLOW_README.md         # Detailed documentation

database/
├── combined_videos.json       # Main database (ONLY file kept)
├── workflow_progress.json     # Progress tracking
├── failed_videos.json         # Failed videos
├── hosting_status.json        # Hosting service status
└── stats.json                 # Statistics

.github/workflows/
└── javgg-workflow.yml         # GitHub Actions configuration
```

## Workflow Steps

1. **Scrape**: Get new videos from JavaGG homepage
2. **Download**: Download video using yt-dlp (tries multiple servers)
3. **Enrich**: Add JAVDatabase metadata (actress profiles, screenshots)
4. **Preview**: Generate 2-minute preview video
5. **Upload**: Upload full video to all hosts, preview to Internet Archive
6. **Update**: Save all URLs to database
7. **Cleanup**: Delete temporary files (keep only `combined_videos.json`)

## Database Structure

```json
{
  "videos": [
    {
      "code": "SONE-572",
      "title": "Full English Title",
      "title_jp": "Japanese Title",
      "actresses": ["Miru"],
      "actress_details": [{
        "name": "Miru",
        "birthdate": "1994-01-16",
        "age": 32,
        "debut_date": "2016-05-19",
        "debut_age": 22,
        "height": "158 cm",
        "measurements": "92-58-89",
        "cup_size": "E",
        "birthplace": "Tokyo",
        "zodiac_sign": "Capricorn",
        "blood_type": "A",
        "profile_images": ["url1", "url2"]
      }],
      "screenshots": ["url1", "url2", ...],
      "release_date": "2025-01-15",
      "duration": "120 minutes",
      "studio": "S1 NO.1 STYLE",
      "tags": ["tag1", "tag2"],
      "hosting_urls": {
        "streamtape": "https://...",
        "uploady": "https://..."
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

## Progress Tracking

The workflow tracks:
- Processed videos (to avoid duplicates)
- Failed videos (with retry logic)
- Pending enrichment (retries after 2 days if JAVDatabase unavailable)
- Last scraped page

## Error Handling

- **Download failures**: Tries multiple embed servers, logs and continues
- **JAVDatabase unavailable**: Adds to retry queue (2-day delay)
- **Upload failures**: Saves whatever URLs succeeded
- **All errors**: Logged, progress saved, never loses data

## Configuration

Edit `complete_workflow.py` to customize:
- `max_videos`: Videos to process per run (default: 10)
- `headless`: Run browser in headless mode (default: True)
- `fetch_actress_details`: Fetch detailed actress profiles (default: True)

## Monitoring

Check progress:
```bash
cat database/workflow_progress.json
cat database/stats.json
```

View database:
```bash
python view_database.py
```

## Notes

- Only `combined_videos.json` is kept as the main database
- All temporary files are deleted after processing
- Progress is tracked to avoid data loss
- JAVDatabase enrichment retries automatically after 2 days
- GitHub Actions commits database changes automatically

## Troubleshooting

See [WORKFLOW_README.md](WORKFLOW_README.md) for detailed troubleshooting guide.
