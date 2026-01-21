#!/usr/bin/env python3
"""
StreamWish Folder Management
Handles folder creation and caching with parent folder support
"""
import os
import json
import requests

FOLDER_CACHE_FILE = "database/streamwish_folders.json"
PARENT_FOLDER_NAME = "Jable Scrapes"

def load_folder_cache():
    """Load cached folder IDs"""
    try:
        # Ensure database directory exists
        os.makedirs("database", exist_ok=True)
        
        if os.path.exists(FOLDER_CACHE_FILE):
            with open(FOLDER_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_folder_cache(cache):
    """Save folder cache"""
    try:
        # Ensure database directory exists
        os.makedirs("database", exist_ok=True)
        
        with open(FOLDER_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def get_or_create_parent_folder(api_key):
    """Get or create the parent folder "Jable Scrapes"
    """
    if not api_key:
        return None
    
    cache = load_folder_cache()
    cache_key = f"_parent_{PARENT_FOLDER_NAME}"
    
    if cache_key in cache:
        folder_id = cache[cache_key]
        # Verify it still exists
        try:
            folders = list_folders(api_key)
            for folder in folders:
                if str(folder.get('fld_id')) == str(folder_id):
                    print(f"   [Folder] Using cached parent folder ID: {folder_id}")
                    return folder_id
            print(f"   [Folder] Cached parent folder no longer exists")
            del cache[cache_key]
            save_folder_cache(cache)
        except:
            pass
    
    print(f"   [Folder] Checking if parent folder '{PARENT_FOLDER_NAME}' exists...")
    try:
        folders = list_folders(api_key)
        for folder in folders:
            if folder.get('name') == PARENT_FOLDER_NAME:
                folder_id = str(folder.get('fld_id'))
                print(f"   [Folder] ✅ Found existing parent folder: {folder_id}")
                cache[cache_key] = folder_id
                save_folder_cache(cache)
                return folder_id
    except Exception as e:
        print(f"   [Folder] ⚠️ Could not check existing folders: {e}")
    
    print(f"   [Folder] Creating new parent folder '{PARENT_FOLDER_NAME}'...")
    
    try:
        r = requests.get("https://api.streamwish.com/api/folder/create",
                        params={
                            'key': api_key,
                            'name': PARENT_FOLDER_NAME
                        }, timeout=10)
        
        if r.status_code == 200:
            result = r.json()
            if result.get('status') == 200:
                folder_id = result.get('result', {}).get('fld_id')
                if folder_id:
                    folder_id = str(folder_id)
                    cache[cache_key] = folder_id
                    save_folder_cache(cache)
                    print(f"   [Folder] ✅ Created parent folder with ID: {folder_id}")
                    return folder_id
            else:
                error_msg = result.get('msg', 'Unknown error')
                if 'already' in error_msg.lower() or 'exist' in error_msg.lower():
                    print(f"   [Folder] Parent folder already exists, fetching...")
                    folders = list_folders(api_key)
                    for folder in folders:
                        if folder.get('name') == PARENT_FOLDER_NAME:
                            folder_id = str(folder.get('fld_id'))
                            cache[cache_key] = folder_id
                            save_folder_cache(cache)
                            print(f"   [Folder] ✅ Found parent folder ID: {folder_id}")
                            return folder_id
        
        print(f"   [Folder] ⚠️ Failed to create parent folder: {r.text[:100]}")
    except Exception as e:
        print(f"   [Folder] ❌ Error creating parent folder: {e}")
    
    return None

def normalize_folder_name(name):
    """Normalize folder name for consistent matching"""
    if not name or not isinstance(name, str):
        return ""
    
    import re
    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name.strip())
    # Title case for consistency
    name = name.title()
    # Remove any trailing/leading special chars
    name = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', name).strip()
    return name if name else ""

def get_or_create_folder(folder_name, api_key):
    """
    Get folder ID for a folder name, create if doesn't exist
    Supports nested folder paths like "PARENT/CHILD" by creating a single folder with that name
    
    Note: StreamWish API doesn't support true nested folders, so we use the full path as folder name
    Example: "JAV_VIDEOS/MIDA-486" creates a folder named "JAV_VIDEOS/MIDA-486"
    """
    if not folder_name or not api_key:
        return None
    
    # Don't normalize if it contains a path separator - keep the full path
    if '/' in folder_name:
        # Keep the path structure as-is for nested folders
        cache_key = folder_name
        display_name = folder_name
    else:
        # Normalize single folder names
        folder_name = normalize_folder_name(folder_name)
        cache_key = folder_name
        display_name = folder_name
    
    cache = load_folder_cache()
    if cache_key in cache:
        folder_id = cache[cache_key]
        # Verify cached folder still exists
        try:
            folders = list_folders(api_key)
            for folder in folders:
                if str(folder.get('fld_id')) == str(folder_id):
                    print(f"   [Folder] Using cached ID for '{display_name}': {folder_id}")
                    return folder_id
            # Cached folder doesn't exist anymore, remove from cache
            print(f"   [Folder] Cached folder no longer exists, will recreate")
            del cache[cache_key]
            save_folder_cache(cache)
        except:
            pass
    
    print(f"   [Folder] Checking if folder '{display_name}' exists...")
    try:
        folders = list_folders(api_key)
        for folder in folders:
            server_folder_name = folder.get('name', '')
            folder_id = str(folder.get('fld_id'))
            
            # Exact match for nested paths, normalized match for single folders
            if '/' in folder_name:
                # Exact match for paths
                if server_folder_name == display_name:
                    print(f"   [Folder] ✅ Found existing folder: {folder_id}")
                    cache[cache_key] = folder_id
                    save_folder_cache(cache)
                    return folder_id
            else:
                # Normalized match for single folders
                if normalize_folder_name(server_folder_name) == folder_name:
                    print(f"   [Folder] ✅ Found existing folder: {folder_id}")
                    cache[cache_key] = folder_id
                    save_folder_cache(cache)
                    return folder_id
    except Exception as e:
        print(f"   [Folder] ⚠️ Could not check existing folders: {e}")
    
    print(f"   [Folder] Creating new folder '{display_name}'...")
    
    try:
        params = {
            'key': api_key,
            'name': display_name  # Use full path as folder name
        }
        
        r = requests.get("https://api.streamwish.com/api/folder/create",
                        params=params, timeout=10)
        
        if r.status_code == 200:
            result = r.json()
            if result.get('status') == 200:
                folder_id = result.get('result', {}).get('fld_id')
                if folder_id:
                    folder_id = str(folder_id)
                    cache[cache_key] = folder_id
                    save_folder_cache(cache)
                    print(f"   [Folder] ✅ Created folder '{display_name}' with ID: {folder_id}")
                    return folder_id
            else:
                error_msg = result.get('msg', 'Unknown error')
                # Check if folder already exists error
                if 'already' in error_msg.lower() or 'exist' in error_msg.lower():
                    print(f"   [Folder] Folder already exists, fetching ID...")
                    # Refresh folder list and find it
                    folders = list_folders(api_key)
                    for folder in folders:
                        if folder.get('name', '') == display_name:
                            folder_id = str(folder.get('fld_id'))
                            cache[cache_key] = folder_id
                            save_folder_cache(cache)
                            print(f"   [Folder] ✅ Found folder ID: {folder_id}")
                            return folder_id
                print(f"   [Folder] ⚠️ API returned: {result.get('status')} - {error_msg}")
        else:
            print(f"   [Folder] ⚠️ HTTP error: {r.status_code}")
        
        print(f"   [Folder] Response: {r.text[:200]}")
    except Exception as e:
        print(f"   [Folder] ❌ Error: {e}")
    
    return None

def list_folders(api_key):
    """List all folders"""
    try:
        r = requests.get("https://api.streamwish.com/api/folder/list",
                        params={'key': api_key}, timeout=10)
        
        if r.status_code == 200:
            result = r.json()
            if result.get('status') == 200:
                return result.get('result', {}).get('folders', [])
    except:
        pass
    return []

if __name__ == "__main__":
    # Test
    if os.path.exists('.env'):
        from load_env import load_env
        load_env()
    
    api_key = os.getenv('STREAMWISH_API_KEY')
    
    print("Testing folder management...")
    
    # Test creating a folder
    folder_id = get_or_create_folder("TEST", api_key)
    print(f"\nFolder ID: {folder_id}")
    
    # Test getting it again (should use cache)
    folder_id2 = get_or_create_folder("TEST", api_key)
    print(f"Folder ID (cached): {folder_id2}")
    
    # List all folders
    folders = list_folders(api_key)
    print(f"\nAll folders:")
    for f in folders:
        print(f"  - {f.get('name')}: {f.get('fld_id')}")
