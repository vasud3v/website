#!/usr/bin/env python3
"""
StreamWish Folder Management
Handles folder creation and caching with parent folder support
"""
import os
import json
import requests

# Use absolute path to project root database
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FOLDER_CACHE_FILE = os.path.join(PROJECT_ROOT, "database", "streamwish_folders.json")
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
            server_name = folder.get('name', '').strip()
            # Case-insensitive matching
            if server_name.lower() == PARENT_FOLDER_NAME.lower():
                folder_id = str(folder.get('fld_id'))
                print(f"   [Folder] ✅ Found existing parent folder: {folder_id} (name: '{server_name}')")
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
                        server_name = folder.get('name', '').strip()
                        # Case-insensitive matching
                        if server_name.lower() == PARENT_FOLDER_NAME.lower():
                            folder_id = str(folder.get('fld_id'))
                            cache[cache_key] = folder_id
                            save_folder_cache(cache)
                            print(f"   [Folder] ✅ Found parent folder ID: {folder_id} (name: '{server_name}')")
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
    # Normalize whitespace only - DON'T change case
    name = re.sub(r'\s+', ' ', name.strip())
    # Remove any trailing/leading special chars (but keep underscores, hyphens, slashes)
    name = re.sub(r'^[^\w\s\-_/]+|[^\w\s\-_/]+$', '', name).strip()
    return name if name else ""

def get_or_create_folder(folder_name, api_key):
    """
    Get folder ID for a folder name, create if doesn't exist
    Supports nested folder paths like "PARENT/CHILD" by creating parent first, then child
    
    Example: "JAV_VIDEOS/MIDA-486" creates:
    1. Parent folder "JAV_VIDEOS" (if not exists)
    2. Child folder "MIDA-486" inside parent
    """
    if not folder_name or not api_key:
        return None
    
    # Check if this is a nested path
    if '/' in folder_name:
        parts = folder_name.split('/', 1)
        parent_name = parts[0]
        child_name = parts[1] if len(parts) > 1 else None
        
        if child_name:
            # Create parent folder first
            print(f"   [Folder] Creating nested structure: {parent_name}/{child_name}")
            parent_id = _get_or_create_single_folder(parent_name, api_key, parent_id=None)
            
            if not parent_id:
                print(f"   [Folder] ❌ Failed to create parent folder")
                return None
            
            # Create child folder inside parent
            child_id = _get_or_create_single_folder(child_name, api_key, parent_id=parent_id)
            return child_id
    
    # Single folder (no nesting)
    return _get_or_create_single_folder(folder_name, api_key, parent_id=None)


def _get_or_create_single_folder(folder_name, api_key, parent_id=None):
    """
    Internal function to create a single folder (with optional parent)
    """
    if not folder_name or not api_key:
        return None
    
    # Create cache key that includes parent_id
    cache_key = f"{folder_name}@{parent_id}" if parent_id else folder_name
    
    cache = load_folder_cache()
    if cache_key in cache:
        folder_id = cache[cache_key]
        # Verify cached folder still exists
        try:
            folders = list_folders(api_key)
            for folder in folders:
                if str(folder.get('fld_id')) == str(folder_id):
                    print(f"   [Folder] Using cached ID for '{folder_name}': {folder_id}")
                    return folder_id
            # Cached folder doesn't exist anymore, remove from cache
            print(f"   [Folder] Cached folder no longer exists, will recreate")
            del cache[cache_key]
            save_folder_cache(cache)
        except:
            pass
    
    print(f"   [Folder] Checking if folder '{folder_name}' exists...")
    try:
        folders = list_folders(api_key)
        for folder in folders:
            server_folder_name = folder.get('name', '').strip()
            server_parent_id = str(folder.get('parent_id', '0'))
            folder_id = str(folder.get('fld_id'))
            
            # Match by name and parent_id (case-insensitive and whitespace-normalized)
            expected_parent = str(parent_id) if parent_id else '0'
            name_match = server_folder_name.lower() == folder_name.lower().strip()
            parent_match = server_parent_id == expected_parent
            
            if name_match and parent_match:
                print(f"   [Folder] ✅ Found existing folder: {folder_id} (name: '{server_folder_name}')")
                cache[cache_key] = folder_id
                save_folder_cache(cache)
                return folder_id
    except Exception as e:
        print(f"   [Folder] ⚠️ Could not check existing folders: {e}")
    
    print(f"   [Folder] Creating new folder '{folder_name}'" + (f" in parent {parent_id}" if parent_id else ""))
    
    try:
        params = {
            'key': api_key,
            'name': folder_name
        }
        
        # Add parent_id if specified
        if parent_id:
            params['parent_id'] = str(parent_id)
        
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
                    print(f"   [Folder] ✅ Created folder '{folder_name}' with ID: {folder_id}")
                    return folder_id
            else:
                error_msg = result.get('msg', 'Unknown error')
                # Check if folder already exists error
                if 'already' in error_msg.lower() or 'exist' in error_msg.lower():
                    print(f"   [Folder] Folder already exists, fetching ID...")
                    # Refresh folder list and find it
                    folders = list_folders(api_key)
                    for folder in folders:
                        server_folder_name = folder.get('name', '').strip()
                        server_parent_id = str(folder.get('parent_id', '0'))
                        expected_parent = str(parent_id) if parent_id else '0'
                        
                        # Case-insensitive and whitespace-normalized matching
                        name_match = server_folder_name.lower() == folder_name.lower().strip()
                        parent_match = server_parent_id == expected_parent
                        
                        if name_match and parent_match:
                            folder_id = str(folder.get('fld_id'))
                            cache[cache_key] = folder_id
                            save_folder_cache(cache)
                            print(f"   [Folder] ✅ Found folder ID: {folder_id} (name: '{server_folder_name}')")
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
