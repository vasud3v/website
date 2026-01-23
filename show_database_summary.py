"""
Show comprehensive database summary
"""

import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import db_manager


def show_summary():
    """Show comprehensive database summary"""
    print("\n" + "="*70)
    print("DATABASE SUMMARY")
    print("="*70)
    
    # Get all data
    videos = db_manager.get_all_videos()
    progress = db_manager.get_progress()
    stats = db_manager.get_stats()
    failed = db_manager.get_failed_videos()
    
    # Basic stats
    print(f"\n📊 Overview:")
    print(f"   Total videos: {len(videos)}")
    print(f"   With hosting: {progress.get('total_processed', 0)}")
    print(f"   Without hosting: {len(videos) - progress.get('total_processed', 0)}")
    print(f"   Failed: {len(failed)}")
    print(f"   Success rate: {progress.get('success_rate', 0):.1f}%")
    
    # JAVDatabase enrichment stats
    with_javdb = [v for v in videos if v.get('javdb_available')]
    without_javdb = [v for v in videos if not v.get('javdb_available')]
    
    print(f"\n🎭 JAVDatabase Enrichment:")
    print(f"   With JAVDatabase data: {len(with_javdb)} ({len(with_javdb)/len(videos)*100:.1f}%)")
    print(f"   Without JAVDatabase data: {len(without_javdb)} ({len(without_javdb)/len(videos)*100:.1f}%)")
    
    if without_javdb:
        print(f"\n   Videos without JAVDatabase:")
        for v in without_javdb[:5]:
            code = v.get('code', 'UNKNOWN')
            print(f"      - {code}")
        if len(without_javdb) > 5:
            print(f"      ... and {len(without_javdb) - 5} more")
    
    # Cast stats
    total_cast = sum(len(v.get('cast', [])) for v in videos)
    videos_with_cast = sum(1 for v in videos if len(v.get('cast', [])) > 0)
    
    print(f"\n👥 Cast Information:")
    print(f"   Videos with cast: {videos_with_cast}")
    print(f"   Total actresses: {total_cast}")
    print(f"   Average per video: {total_cast/len(videos):.1f}")
    
    # Screenshots stats
    total_screenshots = sum(len(v.get('screenshots', [])) for v in videos)
    videos_with_screenshots = sum(1 for v in videos if len(v.get('screenshots', [])) > 0)
    
    print(f"\n📸 Screenshots:")
    print(f"   Videos with screenshots: {videos_with_screenshots}")
    print(f"   Total screenshots: {total_screenshots}")
    print(f"   Average per video: {total_screenshots/len(videos):.1f}")
    
    # Hosting stats
    print(f"\n🌐 Hosting Services:")
    for service, count in stats.get('by_hosting', {}).items():
        status = db_manager.get_hosting_status(service)
        available = "✅" if status.get('available') else "❌"
        print(f"   {available} {service}: {count} videos")
    
    # Storage stats
    total_gb = stats.get('total_size_bytes', 0) / (1024**3)
    print(f"\n💾 Storage:")
    print(f"   Total size: {total_gb:.2f} GB")
    if len(videos) > 0:
        avg_gb = total_gb / len(videos)
        print(f"   Average per video: {avg_gb:.2f} GB")
    
    # Studio stats
    studios = {}
    for v in videos:
        studio = v.get('studio')
        if studio:
            studios[studio] = studios.get(studio, 0) + 1
    
    if studios:
        print(f"\n🎬 Top Studios:")
        sorted_studios = sorted(studios.items(), key=lambda x: x[1], reverse=True)
        for studio, count in sorted_studios[:5]:
            print(f"   {studio}: {count} videos")
    
    # Categories stats
    categories = {}
    for v in videos:
        for cat in v.get('categories', []):
            categories[cat] = categories.get(cat, 0) + 1
    
    if categories:
        print(f"\n📁 Top Categories:")
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        for cat, count in sorted_cats[:5]:
            print(f"   {cat}: {count} videos")
    
    # Genres stats (from JAVDatabase)
    genres = {}
    for v in videos:
        for genre in v.get('genres', []):
            genres[genre] = genres.get(genre, 0) + 1
    
    if genres:
        print(f"\n🎭 Top Genres (JAVDatabase):")
        sorted_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)
        for genre, count in sorted_genres[:5]:
            print(f"   {genre}: {count} videos")
    
    # Recent videos
    print(f"\n🆕 Recent Videos:")
    for i, v in enumerate(videos[:5], 1):
        code = v.get('code', 'UNKNOWN')
        title = v.get('title', 'No title')[:50]
        javdb = "✅" if v.get('javdb_available') else "❌"
        hosting = "✅" if v.get('hosting') else "❌"
        print(f"   {i}. {code} - JAVDatabase: {javdb}, Hosting: {hosting}")
        print(f"      {title}...")
    
    # Database files
    print(f"\n📁 Database Files:")
    db_dir = Path(__file__).parent / "database"
    for file in sorted(db_dir.glob("*.json")):
        if not file.name.endswith('.backup'):
            size = file.stat().st_size / 1024
            print(f"   {file.name}: {size:.1f} KB")
    
    # Integrity check
    print(f"\n🔍 Integrity Check:")
    integrity = db_manager.verify_integrity()
    if integrity['healthy']:
        print(f"   ✅ Database is healthy")
    else:
        print(f"   ⚠️  Issues found:")
        for issue in integrity['issues']:
            print(f"      - {issue}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    show_summary()
