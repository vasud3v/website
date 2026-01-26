#!/usr/bin/env python3
"""Manager for saving and retrieving uploaded video URLs"""

import json
import os
from datetime import datetime
from pathlib import Path

class VideoURLManager:
    def __init__(self, storage_file=None):
        # Default to database folder with specific name
        if storage_file is None:
            storage_file = "../database/seekstreaming_host.json"
        self.storage_file = storage_file
        self.data = self._load_data()
    
    def _load_data(self):
        """Load existing data from JSON file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load {self.storage_file}: {e}")
                return self._get_empty_structure()
        return self._get_empty_structure()
    
    def _get_empty_structure(self):
        """Get empty database structure"""
        return {
            "videos": [],
            "stats": {
                "total_videos": 0,
                "total_size_mb": 0
            }
        }
    
    def _save_data(self):
        """Save data to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_file) if os.path.dirname(self.storage_file) else '.', exist_ok=True)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving to {self.storage_file}: {e}")
            return False
    
    def add_video(self, video_info, upload_result):
        """Add a video with only embed URLs needed for website"""
        if not upload_result.get('success'):
            return False
        
        # Extract only the URLs we need
        all_urls = upload_result.get('all_urls', {})
        
        # Create simple video entry with only what's needed
        video_entry = {
            "id": len(self.data["videos"]) + 1,
            "title": video_info.get('title', 'Untitled'),
            "filename": video_info.get('filename', ''),
            "file_size_mb": round(video_info.get('file_size_mb', 0), 2),
            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "video_player": all_urls.get('video_player', ''),
            "video_downloader": all_urls.get('video_downloader', ''),
            "embed_code": all_urls.get('embed_code', ''),
        }
        
        # Add to videos list
        self.data["videos"].append(video_entry)
        
        # Update stats
        self.data["stats"]["total_videos"] = len(self.data["videos"])
        total_size = sum(v.get("file_size_mb", 0) for v in self.data["videos"])
        self.data["stats"]["total_size_mb"] = round(total_size, 2)
        
        # Save to file
        return self._save_data()
    
    def get_all_videos(self):
        """Get all uploaded videos"""
        return self.data["videos"]
    
    def get_video_by_id(self, video_id):
        """Get a specific video by ID"""
        for video in self.data["videos"]:
            if video["id"] == video_id:
                return video
        return None
    
    def get_videos_by_host(self, host):
        """Get all videos from a specific host"""
        return [v for v in self.data["videos"] if v["host"].lower() == host.lower()]
    
    def search_videos(self, query):
        """Search videos by title or filename"""
        query = query.lower()
        return [v for v in self.data["videos"] 
                if query in v["title"].lower() or query in v["original_filename"].lower()]
    
    def get_stats(self):
        """Get upload statistics"""
        return self.data["stats"]


# Example usage
if __name__ == "__main__":
    manager = VideoURLManager()
    
    # Display stats
    stats = manager.get_stats()
    print(f"Total uploads: {stats['total_uploads']}")
    print(f"Total hosts: {stats['total_hosts']}")
    
    # Export for website
    manager.export_for_website()
    manager.generate_html_embed_codes()
