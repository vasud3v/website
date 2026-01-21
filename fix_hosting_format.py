#!/usr/bin/env python3
"""
Fix hosting format in combined database
Converts old format to new format
"""

import json
import shutil
from datetime import datetime


def fix_hosting_format():
    """Fix hosting format in combined database"""
    
    path = "database/combined_videos.json"
    
    # Load database
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} videos")
    
    fixed_count = 0
    
    for video in data:
        code = video.get('code', 'UNKNOWN')
        hosting = video.get('hosting', {})
        
        # Check if it's old format
        if isinstance(hosting, dict) and 'service' in hosting:
            print(f"Fixing {code}...")
            
            # Convert to new format
            service_name = hosting.get('service', 'unknown').lower()
            new_hosting = {
                service_name: {
                    'embed_url': hosting.get('embed_url', ''),
                    'watch_url': hosting.get('watch_url', ''),
                    'download_url': hosting.get('download_url', ''),
                    'direct_url': hosting.get('direct_url', ''),
                    'api_url': hosting.get('api_url', ''),
                    'filecode': hosting.get('filecode', ''),
                    'upload_time': hosting.get('time', 0),
                    'uploaded_at': hosting.get('uploaded_at', datetime.now().isoformat())
                }
            }
            
            video['hosting'] = new_hosting
            fixed_count += 1
            print(f"  ✅ Fixed: {service_name}")
    
    if fixed_count > 0:
        # Backup original
        backup_path = f"{path}.backup.{int(datetime.now().timestamp())}"
        shutil.copy(path, backup_path)
        print(f"\n📦 Backed up to: {backup_path}")
        
        # Save fixed version
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Fixed {fixed_count} videos")
    else:
        print("\n✅ No videos needed fixing")


if __name__ == "__main__":
    fix_hosting_format()
