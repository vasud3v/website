# Complete Workflow Guide

## Overview

Your system has **two main scrapers** that work together to build a comprehensive video database:

1. **Jable Scraper** - Gets videos and hosting links
2. **JAVDatabase Scraper** - Enriches videos with metadata

## 🔄 Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 1: JABLE SCRAPER                        │
│                     (jable/ folder)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        Scrapes Jable.tv for new videos
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Video Data Collected:                                          │
│  • Code (e.g., MIDA-486)                                        │
│  • Title                                                        │
│  • Duration                                                     │
│  • Views, Likes                                                 │
│  • Categories, Tags                                             │
│  • Thumbnail                                                    │
│  • Source URL                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 2: VIDEO DOWNLOAD                       │
│              (download_with_decrypt_v2.py)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        Downloads video from Jable.tv
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Downloaded:                                                    │
│  • Full video file (.mp4)                                       │
│  • Saved to: downloaded_files/                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 3: VIDEO UPLOAD                         │
│              (upload_all_hosts.py)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        Uploads to streaming services
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Hosting Services:                                              │
│  • StreamWish                                                   │
│  • LuluStream                                                   │
│  • StreamTape                                                   │
│                                                                 │
│  Gets back:                                                     │
│  • Watch URLs                                                   │
│  • Embed URLs                                                   │
│  • File codes                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                STEP 4: UPDATE JABLE DATA                        │
│         Updates video with hosting information                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        Video data now includes hosting links
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Complete Jable Data:                                           │
│  {                                                              │
│    "code": "MIDA-486",                                          │
│    "title": "Video Title",                                      │
│    "duration": "2:00:00",                                       │
│    "views": "50000",                                            │
│    "likes": "1500",                                             │
│    "hosting": {                                                 │
│      "streamwish": {                                            │
│        "watch_url": "https://...",                              │
│        "embed_url": "https://..."                               │
│      }                                                          │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              STEP 5: JAVDATABASE ENRICHMENT                     │
│                  (javdatabase/ folder)                          │
│              Called via javdb_integration.py                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        Scrapes JAVDatabase.com for metadata
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  JAVDatabase Data Collected:                                    │
│  • Professional title                                           │
│  • Japanese title                                               │
│  • High-quality cover image                                     │
│  • 13+ screenshots (high-res)                                   │
│  • Actress profiles:                                            │
│    - Name (English & Japanese)                                  │
│    - Age, height, measurements                                  │
│    - Cup size, hair color/length                                │
│    - Profile image                                              │
│  • Release date                                                 │
│  • Runtime                                                      │
│  • Studio name                                                  │
│  • Director                                                     │
│  • Series/Label                                                 │
│  • Genres/Categories                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 6: DATA MERGE                           │
│                  (merge_single.py)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        Intelligently merges Jable + JAVDatabase data
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Merge Logic:                                                   │
│  • Title: JAVDatabase (more professional)                       │
│  • Cover: JAVDatabase (higher quality)                          │
│  • Screenshots: JAVDatabase (13+ high-res)                      │
│  • Cast: JAVDatabase (full profiles)                            │
│  • Metadata: JAVDatabase (release date, studio, etc.)           │
│  • Hosting: Jable (streaming links)                             │
│  • Stats: Jable (views, likes)                                  │
│  • Categories: Both (merged)                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                STEP 7: SAVE TO DATABASE                         │
│              (database_manager.py)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        Saves to centralized database
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Database: database/combined_videos.json                        │
│                                                                 │
│  Complete Video Entry:                                          │
│  {                                                              │
│    "code": "MIDA-486",                                          │
│    "title": "Professional Title from JAVDatabase",              │
│    "title_jp": "日本語タイトル",                                  │
│    "cover_url": "https://javdatabase.com/cover.jpg",            │
│    "screenshots": [13 high-quality images],                     │
│    "cast": [                                                    │
│      {                                                          │
│        "actress_name": "Ruru Ukawa",                            │
│        "actress_name_jp": "羽川るる",                            │
│        "actress_height_cm": 165,                                │
│        "actress_cup_size": "G",                                 │
│        "actress_image_url": "https://..."                       │
│      }                                                          │
│    ],                                                           │
│    "release_date": "2026-01-16",                                │
│    "duration": "2:00:00",                                       │
│    "runtime_minutes": 140,                                      │
│    "studio": "MOODYZ",                                          │
│    "genres": ["Big Tits", "Nymphomaniac"],                     │
│    "categories": ["Jable Category"],                            │
│    "views": "50000",                                            │
│    "likes": "1500",                                             │
│    "hosting": {                                                 │
│      "streamwish": {                                            │
│        "watch_url": "https://...",                              │
│        "embed_url": "https://..."                               │
│      }                                                          │
│    },                                                           │
│    "source_jable": "https://jable.tv/...",                      │
│    "source_javdb": "https://javdatabase.com/...",               │
│    "javdb_available": true                                      │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 8: FRONTEND DISPLAY                     │
│                     (frontend/ folder)                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        Backend API serves data to frontend
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Users See:                                                     │
│  • Professional titles                                          │
│  • High-quality cover images                                    │
│  • Actress profiles with photos                                 │
│  • Multiple screenshots                                         │
│  • Streaming links (watch/embed)                                │
│  • Complete metadata                                            │
│  • Views, likes, ratings                                        │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Special Case: Video Not Found in JAVDatabase

```
Jable Video → JAVDatabase Scraper → Not Found
                      ↓
              Add to Retry Queue
              (javdb_retry_queue.json)
                      ↓
              Save with Jable data only
              (javdb_available: false)
                      ↓
              Wait 2 days
                      ↓
              Automatic Retry
                      ↓
              Found? → Update database
              Not Found? → Retry again (max 5 times)
```

## 📁 Key Files & Their Roles

### Jable Scraper (jable/ folder)
```
jable_scraper.py              → Scrapes Jable.tv for videos
download_with_decrypt_v2.py   → Downloads videos
upload_all_hosts.py           → Uploads to streaming services
run_continuous.py             → Main automation script
```

### JAVDatabase Scraper (javdatabase/ folder)
```
scrape_clean.py               → Main scraper (browser automation)
scrape_single.py              → Scrapes single video
merge_single.py               → Merges Jable + JAVDatabase data
integrated_pipeline.py        → Full enrichment pipeline
javdb_integration.py          → Integration hook for Jable
retry_manager.py              → Manages retry queue
```

### Database (database/ folder)
```
combined_videos.json          → Main database (all videos)
javdb_retry_queue.json        → Videos pending JAVDatabase retry
failed_videos.json            → Failed operations log
stats.json                    → Statistics
progress_tracking.json        → Progress tracking
```

### Backend (backend/ folder)
```
backend/app/main.py           → FastAPI server
backend/app/api/v1/           → API endpoints
backend/app/services/         → Business logic
```

### Frontend (frontend/ folder)
```
frontend/src/pages/           → React pages
frontend/src/components/      → React components
frontend/src/lib/api.ts       → API client
```

## 🚀 How to Run the Workflow

### Option 1: Manual Step-by-Step

```cmd
# Step 1: Scrape Jable
cd jable
python jable_scraper.py

# Step 2: Download videos
python download_with_decrypt_v2.py

# Step 3: Upload to hosts
python upload_all_hosts.py

# Step 4: Enrich with JAVDatabase (for each video)
cd ../javdatabase
python scrape_single.py MIDA-486

# Step 5: Start backend
cd ../backend
python -m uvicorn app.main:app --reload

# Step 6: Start frontend
cd ../frontend
npm run dev
```

### Option 2: Automated (Recommended)

```cmd
# Run continuous pipeline (does everything automatically)
cd jable
python run_continuous.py
```

This will:
1. ✅ Scrape new videos from Jable
2. ✅ Download videos
3. ✅ Upload to streaming services
4. ✅ Enrich with JAVDatabase
5. ✅ Save to combined database
6. ✅ Repeat continuously

### Option 3: 24/7 Automation

```cmd
cd jable
START_24_7.bat
```

Runs the pipeline 24/7 with automatic restarts.

## 🔧 Integration Points

### Where Jable Calls JAVDatabase

In `jable/run_continuous.py` (or similar), add:

```python
from javdb_integration import enrich_with_javdb

# After processing each video from Jable:
video_data = {
    "code": "MIDA-486",
    "title": "Video Title",
    "duration": "2:00:00",
    "hosting": {
        "streamwish": {"watch_url": "https://..."}
    },
    # ... other Jable data
}

# Enrich with JAVDatabase
enrich_with_javdb(video_data, headless=True)
```

This automatically:
1. Scrapes JAVDatabase for the video
2. Merges the data
3. Saves to `database/combined_videos.json`
4. Adds to retry queue if not found

## 📊 Data Flow

```
Jable.tv
   ↓
Jable Scraper → Jable Data
   ↓
Download Video
   ↓
Upload to Hosts → Hosting Links
   ↓
JAVDatabase.com
   ↓
JAVDatabase Scraper → JAVDatabase Data
   ↓
Merge → Complete Data
   ↓
database/combined_videos.json
   ↓
Backend API
   ↓
Frontend
   ↓
Users
```

## 🎯 What Each Component Does

### Jable Scraper
- **Input**: Jable.tv website
- **Output**: Video code, title, duration, views, likes, categories
- **Purpose**: Find and download videos

### Video Download
- **Input**: Jable video URL
- **Output**: .mp4 file
- **Purpose**: Get video file for uploading

### Video Upload
- **Input**: .mp4 file
- **Output**: Streaming URLs (watch, embed)
- **Purpose**: Host videos on streaming services

### JAVDatabase Scraper
- **Input**: Video code (e.g., MIDA-486)
- **Output**: Professional metadata, actress profiles, screenshots
- **Purpose**: Enrich videos with high-quality metadata

### Data Merger
- **Input**: Jable data + JAVDatabase data
- **Output**: Complete video entry
- **Purpose**: Combine best of both sources

### Database Manager
- **Input**: Complete video entry
- **Output**: Saved to combined_videos.json
- **Purpose**: Centralized storage

### Backend API
- **Input**: Database queries
- **Output**: JSON responses
- **Purpose**: Serve data to frontend

### Frontend
- **Input**: API responses
- **Output**: Beautiful UI
- **Purpose**: Display videos to users

## 🔄 Retry Queue Workflow

```
Video not found in JAVDatabase
         ↓
Add to retry queue with:
  - Video code
  - Jable data
  - Retry count: 0
  - Next retry: +2 days
         ↓
Save with Jable data only
(javdb_available: false)
         ↓
Daily retry job runs
         ↓
Check if 2 days passed
         ↓
Yes → Try scraping again
         ↓
Found? → Update database
       → Remove from queue
         ↓
Not found? → Increment retry count
           → Next retry: +2 days
           → Max 5 retries
```

### Run Retry Queue Manually

```python
from integrated_pipeline import process_javdb_retry_queue

# Process up to 10 videos from retry queue
results = process_javdb_retry_queue(max_videos=10, headless=True)

print(f"Success: {results['success']}")
print(f"Failed: {results['failed']}")
```

## 📈 Statistics & Monitoring

### Check Stats

```python
from database_manager import db_manager

# Get all videos
videos = db_manager.get_all_videos()
print(f"Total videos: {len(videos)}")

# Get videos with JAVDatabase data
with_javdb = [v for v in videos if v.get('javdb_available')]
print(f"With JAVDatabase: {len(with_javdb)}")

# Get videos with hosting
with_hosting = [v for v in videos if v.get('hosting')]
print(f"With hosting: {len(with_hosting)}")
```

### Check Retry Queue

```python
from integrated_pipeline import get_retry_queue_stats

stats = get_retry_queue_stats()
print(f"Total in queue: {stats['total']}")
print(f"Ready for retry: {stats['ready_for_retry']}")
print(f"Pending: {stats['pending']}")
print(f"Max retries reached: {stats['max_retries_reached']}")
```

## 🎬 Example: Complete Video Journey

### 1. Video Discovered on Jable
```
Code: MIDA-486
Title: "Basic title from Jable"
Duration: 2:22:45
Views: 165,168
Likes: 1,152
```

### 2. Video Downloaded
```
File: MIDA-486.mp4
Size: 2.5 GB
Location: downloaded_files/
```

### 3. Video Uploaded
```
StreamWish: https://streamwish.com/watch/abc123
LuluStream: https://lulustream.com/watch/def456
```

### 4. JAVDatabase Scraped
```
Professional Title: "MIDA-486 - Her reason crumbles! Unstoppable convulsions!..."
Japanese Title: "理性崩壊！止まらない痙攣！..."
Studio: MOODYZ
Release: 2026-01-16
Runtime: 140 min
Cast: Ruru Ukawa (羽川るる)
  - Height: 165cm
  - Cup: G
  - Image: https://...
Screenshots: 13 high-res images
Genres: Big Tits, Nymphomaniac, Orgasm
```

### 5. Data Merged & Saved
```json
{
  "code": "MIDA-486",
  "title": "MIDA-486 - Her reason crumbles! Unstoppable convulsions!...",
  "title_jp": "理性崩壊！止まらない痙攣！...",
  "cover_url": "https://javdatabase.com/covers/mida486.jpg",
  "screenshots": [13 images],
  "cast": [{full actress profile}],
  "release_date": "2026-01-16",
  "duration": "2:22:45",
  "runtime_minutes": 140,
  "studio": "MOODYZ",
  "views": "165168",
  "likes": "1152",
  "hosting": {
    "streamwish": {"watch_url": "https://..."},
    "lulustream": {"watch_url": "https://..."}
  },
  "javdb_available": true
}
```

### 6. Displayed on Frontend
Users see a beautiful video page with:
- Professional title
- High-quality cover
- Actress profile with photo
- 13 screenshots
- Multiple streaming options
- Complete metadata
- Views and likes

## 🛠️ Customization

### Change Retry Delay
In `javdatabase/retry_manager.py`:
```python
self.retry_delay_days = 2  # Change to 1, 3, 5, etc.
```

### Change Max Retries
```python
self.max_retries = 5  # Change to 3, 10, etc.
```

### Add More Streaming Services
In `jable/upload_all_hosts.py`, add new upload functions.

### Customize Merge Logic
In `javdatabase/merge_single.py`, modify `merge_single_video()`.

## 📚 Summary

**The workflow is:**
1. Jable scraper finds videos
2. Videos are downloaded
3. Videos are uploaded to streaming services
4. JAVDatabase enriches with metadata
5. Data is merged intelligently
6. Everything is saved to combined database
7. Backend serves data to frontend
8. Users enjoy high-quality video pages

**Key Benefits:**
- ✅ Automated end-to-end
- ✅ High-quality metadata
- ✅ Multiple streaming options
- ✅ Automatic retry for missing data
- ✅ Centralized database
- ✅ Beautiful frontend display

---

**Need help with a specific part?** Let me know!
