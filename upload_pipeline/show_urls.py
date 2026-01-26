#!/usr/bin/env python3
"""Display all URLs from the database in a readable format"""

import json

def show_urls():
    db_path = '../database/seekstreaming_host.json'
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("=" * 70)
        print("SEEKSTREAMING VIDEO URLS DATABASE")
        print("=" * 70)
        print()
        
        for video in data['videos']:
            print(f"📹 Video #{video['id']}: {video['title']}")
            print(f"   File: {video['filename']} ({video['file_size_mb']} MB)")
            print(f"   Uploaded: {video['upload_date']}")
            print()
            print("   🎬 VIDEO PLAYER (Embed URL):")
            print(f"      {video['video_player']}")
            print()
            print("   ⬇️  VIDEO DOWNLOADER (Watch URL):")
            print(f"      {video['video_downloader']}")
            print()
            print("   📺 EMBED CODE (iframe):")
            print(f"      {video['embed_code']}")
            print()
            print("-" * 70)
            print()
        
        print(f"📊 Total Videos: {data['stats']['total_videos']}")
        print(f"💾 Total Size: {data['stats']['total_size_mb']} MB")
        print()
        print("=" * 70)
        print()
        print("⚠️  NOTE: Videos need 15-30 minutes to process after upload.")
        print("   If URLs redirect to homepage, the video is still processing.")
        print()
        
    except FileNotFoundError:
        print("❌ Database file not found!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    show_urls()
