#!/usr/bin/env python3
"""
Clean up duplicate video uploads on StreamWish
Keeps only the most recent upload for each video code
"""
import os
import sys
import requests
import time
from collections import defaultdict
from datetime import datetime

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


def get_all_files():
    """Get all files from StreamWish account"""
    print("\n📋 Fetching all files from StreamWish...")
    
    all_files = []
    page = 1
    per_page = 100
    
    while True:
        try:
            response = requests.get(
                "https://api.streamwish.com/api/file/list",
                params={
                    'key': STREAMWISH_API_KEY,
                    'page': page,
                    'per_page': per_page
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}")
                break
            
            data = response.json()
            
            if data.get('status') != 200:
                print(f"❌ API Error: {data.get('msg', 'Unknown')}")
                break
            
            result = data.get('result', {})
            files = result.get('files', [])
            
            if not files:
                break
            
            all_files.extend(files)
            print(f"   Page {page}: {len(files)} files (Total: {len(all_files)})")
            
            # Check if there are more pages
            total_files = result.get('total', 0)
            if len(all_files) >= total_files:
                break
            
            page += 1
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Error fetching files: {e}")
            break
    
    print(f"\n✓ Found {len(all_files)} total files")
    return all_files


def extract_video_code(title):
    """Extract video code from title"""
    # Video codes are typically at the start: "FNS-149 - Title"
    import re
    
    # Pattern 1: CODE-NUMBER at start
    match = re.match(r'^([A-Z]+[-_]\d+)', title.upper())
    if match:
        return match.group(1).replace('_', '-')
    
    # Pattern 2: CODE-NUMBER anywhere
    match = re.search(r'([A-Z]+[-_]\d+)', title.upper())
    if match:
        return match.group(1).replace('_', '-')
    
    return None


def find_duplicates(files):
    """Find duplicate uploads by video code"""
    print("\n🔍 Analyzing for duplicates...")
    
    # Group files by video code
    by_code = defaultdict(list)
    
    for file_info in files:
        title = file_info.get('title', '')
        code = extract_video_code(title)
        
        if code:
            by_code[code].append(file_info)
    
    # Find codes with duplicates
    duplicates = {}
    for code, file_list in by_code.items():
        if len(file_list) > 1:
            duplicates[code] = file_list
    
    print(f"\n📊 Analysis Results:")
    print(f"   Unique video codes: {len(by_code)}")
    print(f"   Codes with duplicates: {len(duplicates)}")
    
    if duplicates:
        print(f"\n⚠️ Found duplicates:")
        for code, file_list in sorted(duplicates.items()):
            print(f"\n   {code}: {len(file_list)} copies")
            for f in file_list:
                # StreamWish API uses 'file_code' not 'filecode'
                filecode = f.get('file_code') or f.get('filecode', 'N/A')
                title = f.get('title', 'N/A')
                uploaded = f.get('uploaded', 'N/A')
                print(f"      - {filecode}: {title[:50]}... (uploaded: {uploaded})")
    
    return duplicates


def delete_file(filecode):
    """Delete a file from StreamWish"""
    try:
        response = requests.get(
            "https://api.streamwish.com/api/file/delete",
            params={
                'key': STREAMWISH_API_KEY,
                'file_code': filecode
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


def cleanup_duplicates(duplicates, dry_run=True):
    """Clean up duplicate uploads, keeping only the most recent"""
    print(f"\n🧹 Cleaning up duplicates (dry_run={dry_run})...")
    
    total_to_delete = 0
    total_to_keep = 0
    
    for code, file_list in sorted(duplicates.items()):
        # Sort by upload date (newest first)
        # StreamWish returns uploaded as timestamp string
        sorted_files = sorted(file_list, key=lambda x: x.get('uploaded', ''), reverse=True)
        
        # Keep the first (newest), delete the rest
        keep = sorted_files[0]
        delete = sorted_files[1:]
        
        total_to_keep += 1
        total_to_delete += len(delete)
        
        print(f"\n   {code}:")
        # StreamWish API uses 'file_code' not 'filecode'
        keep_code = keep.get('file_code') or keep.get('filecode', 'N/A')
        print(f"      ✓ KEEP: {keep_code} (uploaded: {keep.get('uploaded')})")
        
        for f in delete:
            # StreamWish API uses 'file_code' not 'filecode'
            filecode = f.get('file_code') or f.get('filecode')
            uploaded = f.get('uploaded')
            
            if not filecode:
                print(f"      ⚠️ SKIP: No filecode found for {f.get('title', 'Unknown')}")
                continue
            
            if dry_run:
                print(f"      ❌ WOULD DELETE: {filecode} (uploaded: {uploaded})")
            else:
                print(f"      ❌ DELETING: {filecode} (uploaded: {uploaded})...", end=' ')
                success, msg = delete_file(filecode)
                if success:
                    print("✓")
                else:
                    print(f"FAILED: {msg}")
                time.sleep(1)  # Rate limiting
    
    print(f"\n📊 Summary:")
    print(f"   Files to keep: {total_to_keep}")
    print(f"   Files to delete: {total_to_delete}")
    
    if dry_run:
        print(f"\n⚠️ This was a DRY RUN - no files were deleted")
        print(f"   Run with --execute to actually delete duplicates")
    else:
        print(f"\n✅ Cleanup complete!")


def main():
    """Main function"""
    print("="*60)
    print("StreamWish Duplicate Cleanup Tool")
    print("="*60)
    
    # Check for execute flag
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("\n⚠️ Running in DRY RUN mode (no files will be deleted)")
        print("   Use --execute flag to actually delete duplicates")
    else:
        print("\n⚠️ EXECUTE mode - duplicates will be DELETED!")
        print("   Press Ctrl+C within 5 seconds to cancel...")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            sys.exit(0)
    
    # Get all files
    files = get_all_files()
    
    if not files:
        print("\n❌ No files found")
        sys.exit(1)
    
    # Find duplicates
    duplicates = find_duplicates(files)
    
    if not duplicates:
        print("\n✅ No duplicates found!")
        sys.exit(0)
    
    # Clean up
    cleanup_duplicates(duplicates, dry_run=dry_run)
    
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
