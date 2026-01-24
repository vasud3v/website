"""
Clean up duplicate files on StreamWish
Keeps only the largest/newest file for each video code
"""
import os
import requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

STREAMWISH_API_KEY = os.getenv('STREAMWISH_API_KEY')

def get_all_files():
    """Get all files from StreamWish"""
    print("Fetching all files from StreamWish...")
    all_files = []
    page = 1
    
    while True:
        response = requests.get(
            "https://api.streamwish.com/api/file/list",
            params={'key': STREAMWISH_API_KEY, 'per_page': 100, 'page': page},
            timeout=30
        )
        
        if response.status_code != 200:
            break
            
        data = response.json()
        if data.get('status') != 200 or 'result' not in data:
            break
            
        files = data['result'].get('files', [])
        if not files:
            break
            
        all_files.extend(files)
        print(f"  Page {page}: {len(files)} files")
        
        # Check if we've reached the end
        total = data['result'].get('total', 0)
        if len(all_files) >= total:
            break
            
        page += 1
    
    print(f"\nTotal files: {len(all_files)}")
    return all_files

def extract_video_code(title):
    """Extract video code from title"""
    # Common patterns: "SNOS-052", "SNOS-052 - Title", "Preview - SNOS-052"
    import re
    
    # Remove "Preview - " prefix
    title = title.replace("Preview - ", "").replace("PREVIEW - ", "")
    
    # Extract code pattern (XXXX-NNN)
    match = re.match(r'^([A-Z]+-\d+)', title.upper())
    if match:
        return match.group(1)
    
    return None

def find_duplicates(files):
    """Find duplicate files by video code"""
    print("\nAnalyzing for duplicates...")
    
    # Group files by video code
    by_code = defaultdict(list)
    
    for file_info in files:
        title = file_info.get('title', '')
        code = extract_video_code(title)
        
        if code:
            by_code[code].append(file_info)
    
    # Find codes with duplicates
    duplicates = {code: files for code, files in by_code.items() if len(files) > 1}
    
    print(f"Found {len(duplicates)} video codes with duplicates:")
    for code, files in sorted(duplicates.items()):
        print(f"  {code}: {len(files)} copies")
    
    return duplicates

def delete_duplicates(duplicates, dry_run=True):
    """Delete duplicate files, keeping the best one"""
    print(f"\n{'DRY RUN - ' if dry_run else ''}Cleaning up duplicates...")
    
    total_to_delete = 0
    total_deleted = 0
    
    for code, files in sorted(duplicates.items()):
        print(f"\n{code}: {len(files)} copies")
        
        # Sort by size (largest first), then by upload date (newest first)
        files_sorted = sorted(
            files,
            key=lambda f: (f.get('size', 0), f.get('uploaded', '')),
            reverse=True
        )
        
        # Keep the first one (largest/newest)
        keep = files_sorted[0]
        delete = files_sorted[1:]
        
        print(f"  KEEP: {keep.get('title', 'N/A')[:60]}")
        print(f"        Size: {keep.get('size', 0) / (1024*1024):.1f} MB")
        print(f"        Code: {keep.get('file_code', 'N/A')}")
        
        for file_info in delete:
            total_to_delete += 1
            title = file_info.get('title', 'N/A')
            size_mb = file_info.get('size', 0) / (1024*1024)
            filecode = file_info.get('file_code', 'N/A')
            
            print(f"  DELETE: {title[:60]}")
            print(f"          Size: {size_mb:.1f} MB")
            print(f"          Code: {filecode}")
            
            if not dry_run:
                try:
                    response = requests.get(
                        "https://api.streamwish.com/api/file/delete",
                        params={'key': STREAMWISH_API_KEY, 'file_code': filecode},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 200:
                            print(f"          ✅ Deleted")
                            total_deleted += 1
                        else:
                            print(f"          ❌ Failed: {data.get('msg', 'Unknown')}")
                    else:
                        print(f"          ❌ Failed: HTTP {response.status_code}")
                except Exception as e:
                    print(f"          ❌ Error: {str(e)[:50]}")
    
    print(f"\n{'Would delete' if dry_run else 'Deleted'} {total_deleted if not dry_run else total_to_delete} duplicate files")
    print(f"Kept {len(duplicates)} unique videos")
    
    return total_deleted if not dry_run else total_to_delete

def main():
    """Main function"""
    if not STREAMWISH_API_KEY:
        print("❌ STREAMWISH_API_KEY not set in environment")
        return
    
    print("="*60)
    print("STREAMWISH DUPLICATE CLEANUP")
    print("="*60)
    
    # Get all files
    files = get_all_files()
    
    if not files:
        print("No files found")
        return
    
    # Find duplicates
    duplicates = find_duplicates(files)
    
    if not duplicates:
        print("\n✅ No duplicates found!")
        return
    
    # Dry run first
    print("\n" + "="*60)
    print("DRY RUN - No files will be deleted")
    print("="*60)
    delete_duplicates(duplicates, dry_run=True)
    
    # Ask for confirmation
    print("\n" + "="*60)
    response = input("\nProceed with deletion? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n" + "="*60)
        print("DELETING DUPLICATES")
        print("="*60)
        delete_duplicates(duplicates, dry_run=False)
        print("\n✅ Cleanup complete!")
    else:
        print("\n❌ Cancelled")

if __name__ == "__main__":
    main()
