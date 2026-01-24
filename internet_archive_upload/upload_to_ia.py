"""
Upload preview videos to Internet Archive
Provides unlimited free storage with direct MP4 URLs
"""
import os
import sys
import json
from pathlib import Path
from internetarchive import get_item, upload

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def upload_preview_to_internet_archive(video_path, video_code, title=None):
    """
    Upload a preview video to Internet Archive
    
    Args:
        video_path: Path to the preview video file
        video_code: Video code (e.g., FNS-149)
        title: Optional title for the video
    
    Returns:
        dict with success status and direct URL
    """
    print(f"\n{'='*60}")
    print(f"UPLOADING TO INTERNET ARCHIVE")
    print(f"{'='*60}")
    print(f"Video Code: {video_code}")
    print(f"File: {video_path}")
    
    if not os.path.exists(video_path):
        return {
            'success': False,
            'error': f'File not found: {video_path}'
        }
    
    # Create a unique identifier for Internet Archive
    # Format: javcore-preview-{code}
    identifier = f"javcore-preview-{video_code.lower()}"
    
    # Get file info
    file_size = os.path.getsize(video_path)
    file_size_mb = file_size / (1024 * 1024)
    print(f"File size: {file_size_mb:.2f} MB")
    
    # Metadata for Internet Archive
    metadata = {
        'title': title or f'{video_code} - Preview',
        'mediatype': 'movies',  # Required for videos
        'collection': 'opensource_movies',  # Public collection
        'description': f'Preview video for {video_code}',
        'subject': ['preview', 'video', video_code],
        'creator': 'Javcore',
        'language': 'eng',
        'licenseurl': 'https://creativecommons.org/licenses/by/4.0/'  # CC BY 4.0
    }
    
    try:
        print(f"\nIdentifier: {identifier}")
        print(f"Uploading to Internet Archive...")
        
        # Upload the file
        # Internet Archive will automatically make it available via direct URL
        result = upload(
            identifier,
            files=[video_path],
            metadata=metadata,
            verbose=True,
            checksum=True
        )
        
        # Construct direct URL
        # Format: https://archive.org/download/{identifier}/{filename}
        filename = os.path.basename(video_path)
        direct_url = f"https://archive.org/download/{identifier}/{filename}"
        
        # Also provide the details page URL
        details_url = f"https://archive.org/details/{identifier}"
        
        print(f"\n{'='*60}")
        print(f"✓ UPLOAD SUCCESSFUL")
        print(f"{'='*60}")
        print(f"Direct MP4 URL: {direct_url}")
        print(f"Details page: {details_url}")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'identifier': identifier,
            'direct_url': direct_url,
            'details_url': details_url,
            'filename': filename,
            'file_size_mb': file_size_mb
        }
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }
        
        return {
            'success': False,
            'error': str(e)
        }


def update_database_with_ia_url(video_code, ia_result):
    """
    Update the combined_videos.json database with Internet Archive URL
    
    Args:
        video_code: Video code
        ia_result: Result from upload_preview_to_internet_archive
    """
    database_path = Path(__file__).parent.parent / "database" / "combined_videos.json"
    
    if not database_path.exists():
        print(f"❌ Database not found: {database_path}")
        return False
    
    try:
        # Load database
        with open(database_path, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        # Find the video
        video_found = False
        for video in videos:
            if video.get('code') == video_code:
                # Add Internet Archive info
                video['preview_ia'] = {
                    'identifier': ia_result['identifier'],
                    'direct_url': ia_result['direct_url'],
                    'details_url': ia_result['details_url'],
                    'filename': ia_result['filename'],
                    'file_size_mb': ia_result['file_size_mb'],
                    'uploaded_at': None  # Will be set by the calling script
                }
                video_found = True
                print(f"✓ Updated database for {video_code}")
                break
        
        if not video_found:
            print(f"⚠️ Video {video_code} not found in database")
            return False
        
        # Save database
        with open(database_path, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Database saved")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update database: {e}")
        import traceback
        traceback.print_exc()
        return False


def batch_upload_previews(preview_directory):
    """
    Upload all preview videos from a directory to Internet Archive
    
    Args:
        preview_directory: Path to directory containing preview videos
                          Files should be named: {CODE}_preview.mp4
    """
    preview_dir = Path(preview_directory)
    
    if not preview_dir.exists():
        print(f"❌ Directory not found: {preview_dir}")
        return
    
    # Find all preview videos
    preview_files = list(preview_dir.glob("*_preview.mp4"))
    
    if not preview_files:
        print(f"No preview files found in {preview_dir}")
        return
    
    print(f"\nFound {len(preview_files)} preview videos")
    print(f"{'='*60}\n")
    
    results = []
    
    for preview_file in preview_files:
        # Extract video code from filename
        # Format: FNS-149_preview.mp4 -> FNS-149
        video_code = preview_file.stem.replace('_preview', '')
        
        print(f"\nProcessing: {video_code}")
        
        # Upload to Internet Archive
        result = upload_preview_to_internet_archive(
            str(preview_file),
            video_code
        )
        
        if result['success']:
            # Update database
            update_database_with_ia_url(video_code, result)
            results.append({
                'code': video_code,
                'status': 'success',
                'url': result['direct_url']
            })
        else:
            results.append({
                'code': video_code,
                'status': 'failed',
                'error': result.get('error')
            })
    
    # Summary
    print(f"\n{'='*60}")
    print(f"BATCH UPLOAD SUMMARY")
    print(f"{'='*60}")
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']
    
    print(f"Total: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print(f"\n✓ Successful uploads:")
        for r in successful:
            print(f"  - {r['code']}: {r['url']}")
    
    if failed:
        print(f"\n❌ Failed uploads:")
        for r in failed:
            print(f"  - {r['code']}: {r['error']}")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single upload: python upload_to_ia.py <video_file> <video_code>")
        print("  Batch upload:  python upload_to_ia.py --batch <preview_directory>")
        print("\nExamples:")
        print("  python upload_to_ia.py FNS-149_preview.mp4 FNS-149")
        print("  python upload_to_ia.py --batch ../previews")
        sys.exit(1)
    
    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("❌ Please provide preview directory")
            sys.exit(1)
        batch_upload_previews(sys.argv[2])
    else:
        if len(sys.argv) < 3:
            print("❌ Please provide video file and video code")
            sys.exit(1)
        
        video_path = sys.argv[1]
        video_code = sys.argv[2]
        
        result = upload_preview_to_internet_archive(video_path, video_code)
        
        if result['success']:
            update_database_with_ia_url(video_code, result)
            print(f"\n✓ Complete! Direct URL: {result['direct_url']}")
        else:
            print(f"\n❌ Upload failed: {result.get('error')}")
            sys.exit(1)
