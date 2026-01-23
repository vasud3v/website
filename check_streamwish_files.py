#!/usr/bin/env python3
"""
Check StreamWish files and folders - see what's actually there
"""
import os
import sys
import requests

# Add jable directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jable'))

from load_env import load_env

def main():
    # Load environment
    load_env()
    api_key = os.getenv('STREAMWISH_API_KEY')
    
    if not api_key:
        print("❌ STREAMWISH_API_KEY not found in environment")
        return
    
    print("=" * 70)
    print("StreamWish Files & Folders Diagnostic")
    print("=" * 70)
    
    # List all folders
    print("\n📁 Fetching folders...")
    try:
        r = requests.get("https://api.streamwish.com/api/folder/list",
                        params={'key': api_key, 'page': 1, 'per_page': 100},
                        timeout=30)
        
        if r.status_code == 200:
            result = r.json()
            if result.get('status') == 200:
                folders = result.get('result', {}).get('folders', [])
                print(f"✅ Found {len(folders)} folders\n")
                
                for folder in folders:
                    fld_id = folder.get('fld_id')
                    name = folder.get('name', 'Unnamed')
                    parent_id = folder.get('parent_id', 0)
                    print(f"  📁 {name}")
                    print(f"     ID: {fld_id}, Parent: {parent_id}")
            else:
                print(f"❌ API Error: {result.get('msg')}")
        else:
            print(f"❌ HTTP Error: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # List all files
    print("\n" + "=" * 70)
    print("📹 Fetching files...")
    try:
        r = requests.get("https://api.streamwish.com/api/file/list",
                        params={'key': api_key, 'page': 1, 'per_page': 100},
                        timeout=30)
        
        if r.status_code == 200:
            result = r.json()
            if result.get('status') == 200:
                files = result.get('result', {}).get('files', [])
                print(f"✅ Found {len(files)} files\n")
                
                # Group by folder
                files_by_folder = {}
                for file_info in files:
                    folder_id = file_info.get('file_fld_id', 0)
                    if folder_id not in files_by_folder:
                        files_by_folder[folder_id] = []
                    files_by_folder[folder_id].append(file_info)
                
                # Display
                for folder_id, file_list in sorted(files_by_folder.items()):
                    if folder_id == 0:
                        print(f"  📂 Root (no folder)")
                    else:
                        print(f"  📂 Folder ID: {folder_id}")
                    
                    for file_info in file_list:
                        title = file_info.get('title', 'Untitled')
                        filecode = file_info.get('filecode', 'N/A')
                        size = file_info.get('size', 0)
                        size_mb = size / (1024 * 1024) if size > 0 else 0
                        
                        print(f"     📹 {title}")
                        print(f"        Code: {filecode}, Size: {size_mb:.1f} MB")
            else:
                print(f"❌ API Error: {result.get('msg')}")
        else:
            print(f"❌ HTTP Error: {r.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Check specific video
    print("\n" + "=" * 70)
    video_code = input("Enter video code to search (e.g., MVSD-673) or press Enter to skip: ").strip()
    
    if video_code:
        print(f"\n🔍 Searching for files matching '{video_code}'...")
        try:
            r = requests.get("https://api.streamwish.com/api/file/list",
                            params={'key': api_key, 'per_page': 100},
                            timeout=30)
            
            if r.status_code == 200:
                result = r.json()
                if result.get('status') == 200:
                    files = result.get('result', {}).get('files', [])
                    matches = []
                    
                    for file_info in files:
                        title = file_info.get('title', '')
                        if video_code.upper() in title.upper():
                            matches.append(file_info)
                    
                    if matches:
                        print(f"✅ Found {len(matches)} matching files:\n")
                        for file_info in matches:
                            title = file_info.get('title', 'Untitled')
                            filecode = file_info.get('filecode', 'N/A')
                            size = file_info.get('size', 0)
                            size_mb = size / (1024 * 1024) if size > 0 else 0
                            folder_id = file_info.get('file_fld_id', 0)
                            
                            print(f"  📹 {title}")
                            print(f"     Code: {filecode}")
                            print(f"     Size: {size_mb:.1f} MB")
                            print(f"     Folder ID: {folder_id}")
                            print(f"     URL: https://hglink.to/e/{filecode}")
                            print()
                    else:
                        print(f"❌ No files found matching '{video_code}'")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
