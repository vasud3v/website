# JAVDatabase Scraper

Complete metadata scraper for JAVDatabase.com including actress profile images.

## Features

- Scrapes complete video metadata from JAVDatabase
- Gets actress profile images automatically
- Caches actress data to avoid duplicate requests
- Exports to JSON format compatible with frontend

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Scrape Single Video

```bash
python javdb_scraper.py --code "MIDA-486"
```

### Scrape Latest Videos

```bash
# Scrape first page (latest videos)
python javdb_scraper.py --pages 1

# Scrape first 5 pages
python javdb_scraper.py --pages 5 --headless
```

### Output

Data is saved to `database/javdb_metadata.json` with structure:

```json
[
  {
    "code": "MIDA-486",
    "title": "Video Title",
    "actresses": ["Actress 1", "Actress 2"],
    "actress_images": {
      "Actress 1": "https://www.javdatabase.com/idolimages/...",
      "Actress 2": "https://www.javdatabase.com/idolimages/..."
    },
    "cover_url": "https://...",
    "release_date": "2026-01-15",
    ...
  }
]
```

## Integration with Jable

1. Use this scraper to get metadata and actress images from JAVDatabase
2. Use Jable scraper to get M3U8 video URLs
3. Merge the data using video codes as keys

## Workflow

```bash
# 1. Scrape metadata from JAVDatabase
cd javdatabase
python javdb_scraper.py --pages 5 --headless

# 2. Download videos from Jable (in jable folder)
cd ../jable
python jable_scraper.py

# 3. Merge metadata (TODO: create merge script)
```

## Notes

- JAVDatabase has better metadata and actress images
- Jable has the actual video M3U8 URLs
- Best approach: metadata from JAVDatabase + videos from Jable
