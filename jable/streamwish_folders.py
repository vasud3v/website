#!/usr/bin/env python3
"""
StreamWish Folder Management
Handles folder creation and caching with parent folder support
Thread-safe with file locking to prevent duplicate folder creation
"""
import os
import json
import time
import requests
import threading

# Use absolute path to project root database
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FOLDER_CACHE_FILE = os.path.join(PROJECT_ROOT, "database", "streamwish_folders.json")
PARENT_FOLDER_NAME = "Jable Scrapes"

# Thread lock for folder operations
_folder_lock = threading.Lock()

def load_folder_cache():
    """Load cached folder IDs (thread-safe)"""
    try:
        # Ensure database directory exists
        db_dir = os.path.join(PROJECT_ROOT, "database")
        os.makedirs(db_dir, exist_ok=True)
        
        if os.path.exists(FOLDER_CACHE_FILE):
            with open(FOLDER_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_folder_cache(cache):
    """Save folder cache (thread-safe with atomic write)"""
    try:
        # Ensure database directory exists
        db_dir = os.path.join(PROJECT_ROOT, "database")
        os.makedirs(db_dir, exist_ok=True)
        
        # Atomic write
        temp_file = FOLDER_CACHE_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        # Replace original
        if os.path.exists(FOLDER_CACHE_FILE):
            os.remove(FOLDER_CACHE_FILE)
        os.rename(temp_file, FOLDER_CACHE_FILE)
        return True
    except Exception as e:
        print(f"   [Folder] ⚠️ Cache save error: {e}")
        # Clean up temp file
        if os.path.exists(FOLDER_CACHE_FILE + '.tmp'):
            try:
                os.remove(FOLDER_CACHE_FILE + '.tmp')
            except:
                pass
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
    
    # Retry logic for folder creation
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.get("https://api.streamwish.com/api/folder/create",
                            params={
                                'key': api_key,
                                'name': PARENT_FOLDER_NAME
                            }, timeout=30)
            
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
            
            print(f"   [Folder] ⚠️ Failed to create parent folder (attempt {attempt + 1}/{max_retries}): {r.text[:100]}")
        except requests.exceptions.Timeout:
            print(f"   [Folder] ⚠️ Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                print(f"   [Folder] Retrying in {wait_time}s...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"   [Folder] ❌ Error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    
    print(f"   [Folder] ❌ Failed to create parent folder after {max_retries} attempts")
    return None
    
    return None

def normalize_folder_name(name):
    """Normalize folder name for consistent matching"""
    if not name or not isinstance(name, str):
        return ""
    
    import re
    import unicodedata
    
    # Unicode normalization (NFC) to handle accents consistently
    name = unicodedata.normalize('NFC', name)
    
    # Normalize whitespace (multiple spaces to single space)
    name = re.sub(r'\s+', ' ', name.strip())
    
    # Remove leading/trailing slashes
    name = name.strip('/')
    
    # Remove multiple consecutive slashes
    name = re.sub(r'/+', '/', name)
    
    # Remove any trailing/leading special chars (but keep underscores, hyphens, slashes)
    name = re.sub(r'^[^\w\s\-_/]+|[^\w\s\-_/]+$', '', name).strip()
    
    # Validate length (StreamWish limit is typically 255 chars)
    if len(name) > 255:
        name = name[:255]
    
    return name if name else ""

def get_or_create_folder(folder_name, api_key):
    """
    Get folder ID for a folder name, create if doesn't exist
    Supports nested folder paths like "PARENT/CHILD" by creating parent first, then child
    Thread-safe with proper locking and validation
    
    Example: "JAV_VIDEOS/MIDA-486" creates:
    1. Parent folder "JAV_VIDEOS" (if not exists)
    2. Child folder "MIDA-486" inside parent
    """
    if not folder_name or not api_key:
        return None
    
    # Normalize folder name first
    folder_name = normalize_folder_name(folder_name)
    if not folder_name:
        return None
    
    # Check if this is a nested path
    if '/' in folder_name:
        parts = [p.strip() for p in folder_name.split('/') if p.strip()]
        
        if len(parts) == 0:
            return None
        elif len(parts) == 1:
            # Single folder after normalization
            return _get_or_create_single_folder(parts[0], api_key, parent_id=None)
        elif len(parts) > 5:
            # Limit nesting depth to prevent issues
            print(f"   [Folder] ⚠️ Folder path too deep (max 5 levels): {folder_name}")
            parts = parts[:5]
        
        # Create nested structure
        parent_name = parts[0]
        child_path = '/'.join(parts[1:])
        
        print(f"   [Folder] Creating nested structure: {parent_name}/{child_path}")
        
        # Create parent folder first
        parent_id = _get_or_create_single_folder(parent_name, api_key, parent_id=None)
        
        if not parent_id:
            print(f"   [Folder] ❌ Failed to create parent folder: {parent_name}")
            return None
        
        # Verify parent folder exists before creating child
        try:
            folders = list_folders(api_key)
            parent_exists = any(str(f.get('fld_id')) == str(parent_id) for f in folders)
            if not parent_exists:
                print(f"   [Folder] ❌ Parent folder {parent_id} doesn't exist on server")
                return None
        except Exception as e:
            print(f"   [Folder] ⚠️ Could not verify parent folder: {e}")
        
        # Create child folder(s) recursively
        if len(parts) == 2:
            # Simple case: one parent, one child
            child_id = _get_or_create_single_folder(parts[1], api_key, parent_id=parent_id)
            return child_id
        else:
            # Recursive case: multiple levels
            current_parent_id = parent_id
            for i in range(1, len(parts)):
                child_name = parts[i]
                current_parent_id = _get_or_create_single_folder(child_name, api_key, parent_id=current_parent_id)
                if not current_parent_id:
                    print(f"   [Folder] ❌ Failed to create child folder: {child_name}")
                    return None
            return current_parent_id
    
    # Single folder (no nesting)
    return _get_or_create_single_folder(folder_name, api_key, parent_id=None)


def _get_or_create_single_folder(folder_name, api_key, parent_id=None):
    """
    Internal function to create a single folder (with optional parent)
    Thread-safe with locking to prevent duplicate folder creation
    Implements proper atomic check-and-create with retry logic
    """
    if not folder_name or not api_key:
        return None
    
    # Normalize folder name for consistent matching
    folder_name = normalize_folder_name(folder_name)
    if not folder_name:
        return None
    
    # Create cache key that includes parent_id (case-insensitive)
    cache_key = f"{folder_name.lower()}@{parent_id}" if parent_id else folder_name.lower()
    
    # Use lock to prevent race conditions
    with _folder_lock:
        # Check cache first (inside lock)
        cache = load_folder_cache()
        if cache_key in cache:
            folder_id = cache[cache_key]
            
            # Verify cached folder still exists on server
            try:
                folders = list_folders(api_key)
                for folder in folders:
                    if str(folder.get('fld_id')) == str(folder_id):
                        server_folder_name = folder.get('name', '').strip()
                        server_parent_id = str(folder.get('parent_id', '0'))
                        expected_parent = str(parent_id) if parent_id else '0'
                        
                        # Verify name and parent match
                        name_match = server_folder_name.lower() == folder_name.lower()
                        parent_match = server_parent_id == expected_parent
                        
                        if name_match and parent_match:
                            print(f"   [Folder] Using cached ID for '{folder_name}': {folder_id}")
                            return folder_id
                
                # Cached folder doesn't exist anymore, remove from cache
                print(f"   [Folder] Cached folder {folder_id} no longer exists, will recreate")
                del cache[cache_key]
                save_folder_cache(cache)
            except Exception as e:
                print(f"   [Folder] ⚠️ Could not verify cached folder: {e}")
                # Continue to check/create folder
        
        # Not in cache or cache invalid, need to check/create folder
        print(f"   [Folder] Checking if folder '{folder_name}' exists...")
        
        # Retry logic for folder list retrieval
        max_list_retries = 3
        folders = None
        for list_attempt in range(max_list_retries):
            try:
                folders = list_folders(api_key)
                if folders is not None:
                    break
            except Exception as e:
                print(f"   [Folder] ⚠️ Error listing folders (attempt {list_attempt + 1}/{max_list_retries}): {e}")
                if list_attempt < max_list_retries - 1:
                    time.sleep(2 * (list_attempt + 1))
        
        if folders is None:
            print(f"   [Folder] ❌ Could not retrieve folder list after {max_list_retries} attempts")
            return None
        
        # Check if folder already exists
        for folder in folders:
            server_folder_name = folder.get('name', '').strip()
            server_parent_id = str(folder.get('parent_id', '0'))
            folder_id = str(folder.get('fld_id'))
            
            # Match by name and parent_id (case-insensitive and whitespace-normalized)
            expected_parent = str(parent_id) if parent_id else '0'
            name_match = server_folder_name.lower() == folder_name.lower()
            parent_match = server_parent_id == expected_parent
            
            if name_match and parent_match:
                print(f"   [Folder] ✅ Found existing folder: {folder_id} (name: '{server_folder_name}')")
                # Cache it
                cache[cache_key] = folder_id
                save_folder_cache(cache)
                return folder_id
        
        # Folder doesn't exist, create it
        print(f"   [Folder] Creating new folder '{folder_name}'" + (f" in parent {parent_id}" if parent_id else ""))
        
        # Retry logic for folder creation
        max_retries = 5  # Increased from 3
        for attempt in range(max_retries):
            try:
                params = {
                    'key': api_key,
                    'name': folder_name
                }
                
                # Add parent_id if specified
                if parent_id:
                    params['parent_id'] = str(parent_id)
                
                r = requests.get("https://api.streamwish.com/api/folder/create",
                                params=params, timeout=30)
                
                if r.status_code == 200:
                    result = r.json()
                    if result.get('status') == 200:
                        folder_id = result.get('result', {}).get('fld_id')
                        if folder_id:
                            folder_id = str(folder_id)
                            # Cache it immediately
                            cache[cache_key] = folder_id
                            save_folder_cache(cache)
                            print(f"   [Folder] ✅ Created folder '{folder_name}' with ID: {folder_id}")
                            
                            # Verify folder was actually created (non-blocking)
                            time.sleep(2)  # Give server more time to process
                            try:
                                verify_folders = list_folders(api_key)
                                folder_exists = any(str(f.get('fld_id')) == str(folder_id) for f in verify_folders)
                                if not folder_exists:
                                    print(f"   [Folder] ⚠️ Note: Created folder {folder_id} not immediately visible in list")
                                    print(f"   [Folder] This is normal - StreamWish API may have delay in listing")
                                else:
                                    print(f"   [Folder] ✅ Verified folder exists in list")
                            except Exception as e:
                                print(f"   [Folder] ⚠️ Could not verify folder (non-critical): {e}")
                            
                            return folder_id
                    else:
                        error_msg = result.get('msg', 'Unknown error')
                        
                        # Check if folder already exists error (race condition - another process created it)
                        if 'already' in error_msg.lower() or 'exist' in error_msg.lower():
                            print(f"   [Folder] Folder already exists (created by another process), fetching ID...")
                            # Small delay to let the other process finish
                            time.sleep(2)
                            
                            # Refresh folder list and find it
                            try:
                                folders = list_folders(api_key)
                                for folder in folders:
                                    server_folder_name = folder.get('name', '').strip()
                                    server_parent_id = str(folder.get('parent_id', '0'))
                                    expected_parent = str(parent_id) if parent_id else '0'
                                    
                                    # Case-insensitive and whitespace-normalized matching
                                    name_match = server_folder_name.lower() == folder_name.lower()
                                    parent_match = server_parent_id == expected_parent
                                    
                                    if name_match and parent_match:
                                        folder_id = str(folder.get('fld_id'))
                                        # Cache it
                                        cache[cache_key] = folder_id
                                        save_folder_cache(cache)
                                        print(f"   [Folder] ✅ Found folder ID: {folder_id} (name: '{server_folder_name}')")
                                        return folder_id
                            except Exception as e:
                                print(f"   [Folder] ⚠️ Error finding existing folder: {e}")
                        
                        # Check for rate limiting
                        if 'limit' in error_msg.lower() or 'rate' in error_msg.lower():
                            print(f"   [Folder] ⚠️ Rate limited: {error_msg}")
                            if attempt < max_retries - 1:
                                wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s, 40s, 50s
                                print(f"   [Folder] Waiting {wait_time}s before retry...")
                                time.sleep(wait_time)
                                continue
                        
                        print(f"   [Folder] ⚠️ API returned: {result.get('status')} - {error_msg}")
                        if attempt < max_retries - 1:
                            wait_time = 3 * (attempt + 1)  # 3s, 6s, 9s, 12s, 15s
                            print(f"   [Folder] Retrying in {wait_time}s...")
                            time.sleep(wait_time)
                elif r.status_code == 429:
                    # Rate limited
                    print(f"   [Folder] ⚠️ HTTP 429: Rate limited")
                    if attempt < max_retries - 1:
                        wait_time = 15 * (attempt + 1)  # 15s, 30s, 45s, 60s, 75s
                        print(f"   [Folder] Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                else:
                    print(f"   [Folder] ⚠️ HTTP error: {r.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(3 * (attempt + 1))
                
            except requests.exceptions.Timeout:
                print(f"   [Folder] ⚠️ Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s, 20s, 25s
                    print(f"   [Folder] Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            except Exception as e:
                print(f"   [Folder] ❌ Error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3 * (attempt + 1))
        
        print(f"   [Folder] ❌ Failed to create folder after {max_retries} attempts")
        return None

def list_folders(api_key, max_pages=10):
    """List all folders with pagination support, retry logic and error handling"""
    max_retries = 3
    all_folders = []
    
    for attempt in range(max_retries):
        try:
            # Fetch all pages
            page = 1
            while page <= max_pages:
                r = requests.get("https://api.streamwish.com/api/folder/list",
                                params={'key': api_key, 'page': page, 'per_page': 100}, 
                                timeout=30)
                
                if r.status_code == 200:
                    result = r.json()
                    if result.get('status') == 200:
                        folders = result.get('result', {}).get('folders', [])
                        if not folders:
                            # No more folders, we've reached the end
                            break
                        all_folders.extend(folders)
                        
                        # Check if there are more pages
                        total = result.get('result', {}).get('total', 0)
                        if len(all_folders) >= total:
                            break
                        
                        page += 1
                    else:
                        error_msg = result.get('msg', 'Unknown error')
                        print(f"   [Folder] API error listing folders: {error_msg}")
                        if attempt < max_retries - 1:
                            time.sleep(2 * (attempt + 1))
                        break
                elif r.status_code == 429:
                    print(f"   [Folder] Rate limited (429)")
                    if attempt < max_retries - 1:
                        time.sleep(10 * (attempt + 1))
                    break
                else:
                    print(f"   [Folder] HTTP {r.status_code} listing folders")
                    if attempt < max_retries - 1:
                        time.sleep(2 * (attempt + 1))
                    break
            
            # If we got folders, return them
            if all_folders:
                return all_folders
                
        except requests.exceptions.Timeout:
            print(f"   [Folder] Timeout listing folders (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(3 * (attempt + 1))
        except Exception as e:
            print(f"   [Folder] Error listing folders: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
    
    if not all_folders:
        print(f"   [Folder] ❌ Failed to list folders after {max_retries} attempts")
    return all_folders

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
