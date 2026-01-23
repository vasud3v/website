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
    
    # Group files by video code AND type (preview vs full)
    by_code = defaultdict(lambda: {'preview': [], 'full': []})
    
    for file_info in files:
        title = file_info.get('title', '')
        code = extract_video_code(title)
        
        if code:
            # Determine if this is a preview or full video
            is_preview = 'PREVIEW' in title.upper()
            file_type = 'preview' if is_preview else 'full'
            by_code[code][file_type].append(file_info)
    
    # Find codes with duplicates (multiple previews OR multiple full videos)
    duplicates = {}
    for code, file_dict in by_code.items():
        previews = file_dict['preview']
        fulls = file_dict['full']
        
        # Only flag as duplicate if we have multiple of the SAME type
        if len(previews) > 1 or len(fulls) > 1:
            duplicates[code] = {
                'preview': previews,
                'full': fulls
            }
    
    print(f"\n📊 Analysis Results:")
    print(f"   Unique video codes: {len(by_code)}")
    print(f"   Codes with duplicates: {len(duplicates)}")
    
    if duplicates:
        print(f"\n⚠️ Found duplicates:")
        for code, file_dict in sorted(duplicates.items()):
            previews = file_dict['preview']
            fulls = file_dict['full']
            total = len(previews) + len(fulls)
            
            print(f"\n   {code}: {total} copies ({len(previews)} preview, {len(fulls)} full)")
            
            if previews:
                print(f"      PREVIEWS:")
                for f in previews:
                    filecode = f.get('file_code') or f.get('filecode', 'N/A')
                    title = f.get('title', 'N/A')
                    uploaded = f.get('uploaded', 'N/A')
                    print(f"      - {filecode}: {title[:50]}... (uploaded: {uploaded})")
            
            if fulls:
                print(f"      FULL VIDEOS:")
                for f in fulls:
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
    """Clean up duplicate uploads, keeping only the most recent of each type"""
    print(f"\n🧹 Cleaning up duplicates (dry_run={dry_run})...")
    
    total_to_delete = 0
    total_to_keep = 0
    
    for code, file_dict in sorted(duplicates.items()):
        previews = file_dict['preview']
        fulls = file_dict['full']
        
        print(f"\n   {code}:")
        
        # Handle preview duplicates
        if len(previews) > 1:
            sorted_previews = sorted(previews, key=lambda x: x.get('uploaded', ''), reverse=True)
            keep_preview = sorted_previews[0]
            delete_previews = sorted_previews[1:]
            
            total_to_keep += 1
            total_to_delete += len(delete_previews)
            
            keep_code = keep_preview.get('file_code') or keep_preview.get('filecode', 'N/A')
            print(f"      ✓ KEEP PREVIEW: {keep_code} (uploaded: {keep_preview.get('uploaded')})")
            
            for f in delete_previews:
                filecode = f.get('file_code') or f.get('filecode')
                uploaded = f.get('uploaded')
                
                if not filecode:
                    print(f"      ⚠️ SKIP: No filecode found for {f.get('title', 'Unknown')}")
                    continue
                
                if dry_run:
                    print(f"      ❌ WOULD DELETE PREVIEW: {filecode} (uploaded: {uploaded})")
                else:
                    print(f"      ❌ DELETING PREVIEW: {filecode} (uploaded: {uploaded})...", end=' ')
                    success, msg = delete_file(filecode)
                    if success:
                        print("✓")
                    else:
                        print(f"FAILED: {msg}")
                    time.sleep(1)
        elif len(previews) == 1:
            total_to_keep += 1
            keep_code = previews[0].get('file_code') or previews[0].get('filecode', 'N/A')
            print(f"      ✓ KEEP PREVIEW: {keep_code} (uploaded: {previews[0].get('uploaded')})")
        
        # Handle full video duplicates
        if len(fulls) > 1:
            sorted_fulls = sorted(fulls, key=lambda x: x.get('uploaded', ''), reverse=True)
            keep_full = sorted_fulls[0]
            delete_fulls = sorted_fulls[1:]
            
            total_to_keep += 1
            total_to_delete += len(delete_fulls)
            
            keep_code = keep_full.get('file_code') or keep_full.get('filecode', 'N/A')
            print(f"      ✓ KEEP FULL: {keep_code} (uploaded: {keep_full.get('uploaded')})")
            
            for f in delete_fulls:
                filecode = f.get('file_code') or f.get('filecode')
                uploaded = f.get('uploaded')
                
                if not filecode:
                    print(f"      ⚠️ SKIP: No filecode found for {f.get('title', 'Unknown')}")
                    continue
                
                if dry_run:
                    print(f"      ❌ WOULD DELETE FULL: {filecode} (uploaded: {uploaded})")
                else:
                    print(f"      ❌ DELETING FULL: {filecode} (uploaded: {uploaded})...", end=' ')
                    success, msg = delete_file(filecode)
                    if success:
                        print("✓")
                    else:
                        print(f"FAILED: {msg}")
                    time.sleep(1)
        elif len(fulls) == 1:
            total_to_keep += 1
            keep_code = fulls[0].get('file_code') or fulls[0].get('filecode', 'N/A')
            print(f"      ✓ KEEP FULL: {keep_code} (uploaded: {fulls[0].get('uploaded')})")
    
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
