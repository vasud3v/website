#!/usr/bin/env python3
"""
Database Viewer - View and analyze videos_complete.json
"""
import json
import os
from datetime import datetime

DB_FILE = "database/videos_complete.json"

def load_database():
    """Load database"""
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def analyze_database():
    """Analyze and display database statistics"""
    videos = load_database()
    
    print("="*60)
    print(f"DATABASE ANALYSIS: {DB_FILE}")
    print("="*60)
    
    if not videos:
        print("Database is empty!")
        return
    
    print(f"\nTotal videos: {len(videos)}")
    
    # Count by hosting service
    hosting_counts = {}
    for video in videos:
        for service in video.get('hosting', {}).keys():
            hosting_counts[service] = hosting_counts.get(service, 0) + 1
    
    print(f"\nHosting services:")
    for service, count in hosting_counts.items():
        print(f"  - {service}: {count} videos")
    
    # Count by model
    model_counts = {}
    for video in videos:
        for model in video.get('models', []):
            model_counts[model] = model_counts.get(model, 0) + 1
    
    if model_counts:
        print(f"\nTop 10 models:")
        sorted_models = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for model, count in sorted_models:
            print(f"  - {model}: {count} videos")
    
    # Count by category
    category_counts = {}
    for video in videos:
        for cat in video.get('categories', []):
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    if category_counts:
        print(f"\nTop categories:")
        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, count in sorted_cats:
            print(f"  - {cat}: {count} videos")
    
    # Recent videos
    print(f"\nMost recent videos:")
    sorted_videos = sorted(videos, key=lambda x: x.get('processed_at', ''), reverse=True)[:5]
    for video in sorted_videos:
        code = video.get('code', 'Unknown')
        title = video.get('title', 'No title')[:50]
        processed = video.get('processed_at', '')[:19]
        print(f"  - {code}: {title}... ({processed})")
    
    # Total file size
    total_size = sum(video.get('file_size', 0) for video in videos)
    if total_size > 0:
        print(f"\nTotal file size: {total_size / (1024**3):.2f} GB")
    
    print("\n" + "="*60)

def list_videos(limit=10):
    """List videos with details"""
    videos = load_database()
    
    if not videos:
        print("No videos in database!")
        return
    
    print(f"\nShowing {min(limit, len(videos))} of {len(videos)} videos:")
    print("="*60)
    
    for i, video in enumerate(videos[:limit], 1):
        print(f"\n{i}. {video.get('code', 'Unknown')}")
        print(f"   Title: {video.get('title', 'No title')}")
        print(f"   Models: {', '.join(video.get('models', []))}")
        print(f"   Duration: {video.get('duration', 'Unknown')}")
        print(f"   Views: {video.get('views', 'Unknown')}")
        
        hosting = video.get('hosting', {})
        if hosting:
            print(f"   Hosting:")
            for service, data in hosting.items():
                print(f"     - {service}: {data.get('embed_url', 'N/A')}")
        
        print(f"   Processed: {video.get('processed_at', 'Unknown')[:19]}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        list_videos(limit)
    else:
        analyze_database()
