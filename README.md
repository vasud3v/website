# JAV Video Scraper - Integrated Pipeline

Complete automated pipeline for scraping, downloading, and enriching JAV videos from Jable.tv with metadata from JAVDatabase.

## 🌟 Features

### Jable Scraper
- ✅ Scrapes video metadata from Jable.tv
- ✅ Downloads videos (M3U8 → MP4)
- ✅ Uploads to StreamWish with organized folders
- ✅ Automatic retry and error handling
- ✅ Rate limit detection and fallback to LuluStream

### JAVDatabase Integration
- ✅ Automatic metadata enrichment
- ✅ Actress profiles with images
- ✅ High-quality screenshots (10-13 per video)
- ✅ Genres, studio, director, label, series
- ✅ Release dates, runtime, ratings
- ✅ Japanese titles

### Folder Organization
- ✅ Parent folder: `JAV_VIDEOS`
- ✅ Video folders: `JAV_VIDEOS/{VIDEO-CODE}`
- ✅ Automatic folder creation and caching

### GitHub Actions
- ✅ Runs automatically every 6 hours
- ✅ Commits databases automatically
- ✅ Displays statistics in GitHub UI
- ✅ Auto-restart on failures

## 📊 Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    INTEGRATED WORKFLOW                       │
└─────────────────────────────────────────────────────────────┘

1. Scrape Jable.tv
   ↓ (metadata + M3U8 URL)
   
2. Download Video
   ↓ (M3U8 → TS → MP4)
   
3. Upload to StreamWish
   ↓ (JAV_VIDEOS/{CODE}/)
   
4. Save to Jable Database
   ↓ (videos_complete.json)
   
5. ✨ Enrich with JAVDatabase
   ↓ (actress profiles, screenshots, genres, etc.)
   
6. Save Combined Data
   ↓ (combined_videos.json)
   
7. Commit to GitHub
   ↓
   
8. Next Video
```

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.11+
python --version

# Install dependencies
cd jable
pip install -r requirements.txt

cd ../javdatabase
pip install -r requirements.txt
```

### Environment Variables
Create `.env` file in `jable/` directory:
```env
STREAMWISH_API_KEY=your_streamwish_key
LULUSTREAM_API_KEY=your_lulustream_key
```

### Run Locally
```bash
cd jable
python run_continuous.py
```

### GitHub Actions Setup
1. Fork this repository
2. Add secrets in Settings → Secrets and variables → Actions:
   - `STREAMWISH_API_KEY`
   - `LULUSTREAM_API_KEY`
3. Enable GitHub Actions
4. Workflow runs automatically every 6 hours

## 📁 Project Structure

```
.
├── jable/                          # Main scraper
│   ├── run_continuous.py           # Main workflow
│   ├── jable_scraper.py            # Jable scraper
│   ├── javdb_integration.py        # JAVDatabase integration
│   ├── upload_all_hosts.py         # Upload to StreamWish/LuluStream
│   ├── streamwish_folders.py       # Folder management
│   ├── download_with_decrypt_v2.py # Video downloader
│   ├── utils.py                    # Utilities
│   └── database/
│       ├── videos_complete.json    # Jable data
│       └── videos_failed.json      # Failed videos
│
├── javdatabase/                    # Metadata scraper
│   ├── integrated_pipeline.py      # Orchestrator
│   ├── scrape_single.py            # Single video scraper
│   ├── merge_single.py             # Data merger
│   ├── scrape_clean.py             # Clean data scraper
│   ├── test_integration.py         # Test suite
│   └── database/
│       ├── stats.json              # Statistics
│       └── errors.json             # Error log
│
├── database/                       # Combined data
│   └── combined_videos.json        # Merged Jable + JAVDatabase
│
└── .github/workflows/
    └── integrated_scraper.yml      # GitHub Actions workflow
```

## 📊 Database Structure

### Jable Database (`jable/database/videos_complete.json`)
Basic video info from Jable + StreamWish URLs

### Combined Database (`database/combined_videos.json`)
Complete metadata (Jable + JAVDatabase merged):
```json
{
  "code": "MIDA-486",
  "title": "Professional title from JAVDatabase",
  "title_jp": "日本語タイトル",
  "cover_url": "https://javdatabase.com/cover.jpg",
  "screenshots": ["...10-13 high-quality images"],
  "cast": [
    {
      "actress_name": "Actress Name",
      "actress_age": 25,
      "actress_height_cm": 160,
      "actress_image_url": "https://javdatabase.com/actress.jpg",
      ...
    }
  ],
  "genres": ["Genre1", "Genre2"],
  "studio": "Studio Name",
  "director": "Director Name",
  "hosting": {
    "streamwish": {
      "embed_url": "https://hglink.to/e/...",
      "watch_url": "https://hglink.to/...",
      "folder": "JAV_VIDEOS/MIDA-486"
    }
  },
  "javdb_available": true
}
```

## 🧪 Testing

### Run Integration Tests
```bash
python javdatabase/test_integration.py
```

### Verify Changes
```bash
python test_changes.py
```

## 📈 Performance

- **Processing time:** ~20-30 minutes per video
- **Success rate:** ~85-90%
- **JAVDatabase coverage:** ~90%

### Breakdown
- Jable scraping: ~1 minute
- Video download: ~5-10 minutes
- Video upload: ~10-20 minutes
- JAVDatabase enrichment: ~1-2 minutes

## 🔧 Configuration

### Folder Structure
Edit `jable/upload_all_hosts.py`:
```python
parent_folder = "JAV_VIDEOS"  # Change parent folder name
folder_name = f"{parent_folder}/{code}"  # Nested structure
```

### Workflow Schedule
Edit `.github/workflows/integrated_scraper.yml`:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours (change as needed)
```

## 🛠️ Error Handling

The pipeline handles these scenarios gracefully:
- ✅ Network timeouts → Retry with exponential backoff
- ✅ Browser crashes → Restart browser
- ✅ Rate limiting → Wait and retry, fallback to LuluStream
- ✅ Video not found → Use Jable data only
- ✅ Invalid data → Validate and fallback

## 📊 Monitoring

### Check Statistics
```bash
cat javdatabase/database/stats.json
```

### View Logs
```bash
tail -f jable/pipeline.log
```

### GitHub Actions
View workflow runs: `Actions` tab in GitHub

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is for educational purposes only. Respect copyright laws and terms of service.

## ⚠️ Disclaimer

This tool is provided as-is for educational purposes. Users are responsible for:
- Complying with all applicable laws
- Respecting website terms of service
- Ensuring proper content licensing
- Using the tool ethically and legally

## 🔗 Links

- **Jable.tv:** https://jable.tv
- **JAVDatabase:** https://javdatabase.com
- **StreamWish:** https://streamwish.com
- **LuluStream:** https://lulustream.com

## 📧 Support

For issues and questions:
1. Check existing issues
2. Review documentation
3. Create a new issue with details

---

**Version:** 1.0.0  
**Last Updated:** 2026-01-21  
**Status:** 🟢 Production Ready
