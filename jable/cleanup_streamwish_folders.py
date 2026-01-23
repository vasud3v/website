#!/usr/bin/env python3
"""
Clean up duplicate folders on StreamWish
Consolidates videos from duplicate folders into a single folder per video code
"""
import os
import sys
import requests
import time
from collections import defaultdict

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add jable directory to path for imports
sys.path.insert(0, SCRIPT_DIR)

# Load environment variables from jable/.env
try:
    from load_env import load_env
    env_file = os.path.join(SCRIPT_DIR, '.env')
    load_env(env_file)
except ImportError:
    print("⚠️ Could not import load_env, trying to load .env manually")
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(SCRIPT_DIR, '.env')
        load_dotenv(env_path)
    except:
        pass

# Load API key
STREAMWISH_API_KEY = os.getenv('STREAMWISH_API_KEY')

if not STREAMWISH_API_KEY:
    print("❌ STREAMWISH_API_KEY not set in environment")
    print(f"   Make sure {os.path.join(SCRIPT_DIR, '.env')} file exists with STREAMWISH_API_KEY")
    sys.exit(1)

print(f"StreamWish API Key: {STREAMWISH_API_KEY[:10]}...")


def list_all_folders(api_key):
    """Get all folders from StreamWish"""
    print("\n📋 Fetching all folders from StreamWish...")
    
    try:
        response = requests.get(
            "https://api.streamwish.com/api/folder/list",
            params={'key': api_key},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        if data.get('status') != 200:
            print(f"❌ API Error: {data.get('msg', 'Unknown')}")
            return []
        
        folders = data.get('result', {}).get('folders', [])
        print(f"✓ Found {len(folders)} folders")
        return folders
        
    except Exception as e:
        print(f"❌ Error fetching folders: {e}")
        return []


def list_files_in_folder(api_key, folder_id):
    """List all files in a specific folder"""
    try:
        response = requests.get(
            "https://api.streamwish.com/api/file/list",
            params={
                'key': api_key,
                'fld_id': folder_id,
                'per_page': 1000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 200:
                return data.get('result', {}).get('files', [])
    except:
        pass
    return []


def move_file(api_key, file_code, target_folder_id):
    """Move a file to a different folder"""
    try:
        response = requests.get(
            "https://api.streamwish.com/api/file/set_folder",
            params={
                'key': api_key,
                'file_code': file_code,
                'fld_id': target_folder_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 200:
                return True, "Success"
            else:
                return False, data.get('msg', 'Unknown error')
        else:
            return False, f"HTTP {response.status_code}"
            
    except Exception as e:
        return False, str(e)


def delete_folder(api_key, folder_id):
    """Delete an empty folder"""
    try:
        response = requests.get(
            "https://api.streamwish.com/api/folder/delete",
            params={
                'key': api_key,
                'fld_id': folder_id
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 200:
                return True, "Success"
            else:
                return False, data.get('msg', 'Unknown error')
        else:
            return False, f"HTTP {response.status_code}"
            
    except Exception as e:
        return False, str(e)


def extract_video_code(folder_name):
    """Extract video code from folder name"""
    # Folder names are like: "JAV_VIDEOS/FNS-149" or "JAV_PREVIEWS/FNS-149"
    import re
    
    # Pattern: CODE-NUMBER
    match = re.search(r'([A-Z]+[-_]\d+)', folder_name.upper())
    if match:
        return match.group(1).replace('_', '-')
    
    return None


def find_duplicate_folders(folders):
    """Find folders with the same video code"""
    print("\n🔍 Analyzing folders for duplicates...")
    
    # Group folders by video code
    by_code = defaultdict(list)
    
    for folder in folders:
        folder_name = folder.get('name', '')
        code = extract_video_code(folder_name)
        
        if code:
            by_code[code].append(folder)
    
    # Find codes with multiple folders
    duplicates = {}
    for code, folder_list in by_code.items():
        if len(folder_list) > 1:
            duplicates[code] = folder_list
    
    print(f"\n📊 Analysis Results:")
    print(f"   Unique video codes: {len(by_code)}")
    print(f"   Codes with duplicate folders: {len(duplicates)}")
    
    if duplicates:
        print(f"\n⚠️ Found duplicate folders:")
        for code, folder_list in sorted(duplicates.items()):
            print(f"\n   {code}: {len(folder_list)} folders")
            for f in folder_list:
                folder_id = f.get('fld_id')
                folder_name = f.get('name')
                print(f"      - {folder_id}: {folder_name}")
    
    return duplicates


def consolidate_folders(api_key, duplicates, dry_run=True):
    """Consolidate duplicate folders by moving all files to one folder"""
    print(f"\n🧹 Consolidating duplicate folders (dry_run={dry_run})...")
    
    total_folders_to_delete = 0
    total_files_to_move = 0
    
    for code, folder_list in sorted(duplicates.items()):
        print(f"\n   {code}:")
        
        # Sort folders by creation date or ID (keep the first one)
        sorted_folders = sorted(folder_list, key=lambda x: x.get('fld_id', 0))
        
        # Keep the first folder, consolidate others into it
        target_folder = sorted_folders[0]
        target_id = target_folder.get('fld_id')
        target_name = target_folder.get('name')
        
        print(f"      ✓ KEEP: {target_id} ({target_name})")
        
        # Get files in target folder
        target_files = list_files_in_folder(api_key, target_id)
        print(f"         Current files: {len(target_files)}")
        
        # Process other folders
        for folder in sorted_folders[1:]:
            folder_id = folder.get('fld_id')
            folder_name = folder.get('name')
            
            # Get files in this folder
            files = list_files_in_folder(api_key, folder_id)
            
            if files:
                print(f"      📦 CONSOLIDATE: {folder_id} ({folder_name}) - {len(files)} files")
                
                for file_info in files:
                    file_code = file_info.get('filecode')
                    file_title = file_info.get('title', 'Unknown')
                    
                    total_files_to_move += 1
                    
                    if dry_run:
                        print(f"         WOULD MOVE: {file_code} - {file_title[:50]}")
                    else:
                        print(f"         MOVING: {file_code} - {file_title[:50]}...", end=' ')
                        success, msg = move_file(api_key, file_code, target_id)
                        if success:
                            print("✓")
                        else:
                            print(f"FAILED: {msg}")
                        time.sleep(0.5)  # Rate limiting
            else:
                print(f"      📦 EMPTY: {folder_id} ({folder_name})")
            
            # Delete the now-empty folder
            total_folders_to_delete += 1
            
            if dry_run:
                print(f"         WOULD DELETE FOLDER: {folder_id}")
            else:
                print(f"         DELETING FOLDER: {folder_id}...", end=' ')
                success, msg = delete_folder(api_key, folder_id)
                if success:
                    print("✓")
                else:
                    print(f"FAILED: {msg}")
                time.sleep(0.5)  # Rate limiting
    
    print(f"\n📊 Summary:")
    print(f"   Files to move: {total_files_to_move}")
    print(f"   Folders to delete: {total_folders_to_delete}")
    
    if dry_run:
        print(f"\n⚠️ This was a DRY RUN - no changes were made")
        print(f"   Run with --execute to actually consolidate folders")
    else:
        print(f"\n✅ Consolidation complete!")


def main():
    """Main function"""
    print("="*60)
    print("StreamWish Folder Consolidation Tool")
    print("="*60)
    
    # Check for execute flag
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("\n⚠️ Running in DRY RUN mode (no changes will be made)")
        print("   Use --execute flag to actually consolidate folders")
    else:
        print("\n⚠️ EXECUTE mode - folders will be CONSOLIDATED!")
        print("   Press Ctrl+C within 5 seconds to cancel...")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            sys.exit(0)
    
    # Get all folders
    folders = list_all_folders(STREAMWISH_API_KEY)
    
    if not folders:
        print("\n❌ No folders found")
        sys.exit(1)
    
    # Find duplicates
    duplicates = find_duplicate_folders(folders)
    
    if not duplicates:
        print("\n✅ No duplicate folders found!")
        sys.exit(0)
    
    # Consolidate
    consolidate_folders(STREAMWISH_API_KEY, duplicates, dry_run=dry_run)
    
    print("\n" + "="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
