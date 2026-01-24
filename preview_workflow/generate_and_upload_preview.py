"""
Complete workflow: Generate preview video and upload to Internet Archive
Integrates with your existing preview generator and database
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "preview_generator"))
sys.path.insert(0, str(Path(__file__).parent.parent / "internet_archive_upload"))

def generate_and_upload_preview(video_path, video_code, video_title=None):
    """
    Complete workflow:
    1. Generate preview video from full video
    2. Upload preview to Internet Archive
    3. Update database with preview URL
    
    Args:
        video_path: Path to the full video file
        video_code: Video code (e.g., MIDA-479)
        video_title: Optional video title
    
    Returns:
        dict with success status and preview URL
    """
    print("\n" + "="*60)
    print("PREVIEW GENERATION & UPLOAD WORKFLOW")
    print("="*60)
    print(f"Video Code: {video_code}")
    print(f"Video Path: {video_path}")
    print("="*60)
    
    if not os.path.exists(video_path):
        return {
            'success': False,
            'error': f'Video file not found: {video_path}'
        }
    
    # Step 1: Generate preview video
    print("\n[1/3] Generating preview video...")
    print("-" * 60)
    
    try:
        from preview_generator.preview_generator import PreviewGenerator
        
        # Output path for preview
        preview_output = f"{video_code}_preview.mp4"
        
        # Generate preview (10 clips, 3 seconds each)
        generator = PreviewGenerator(video_path)
        result = generator.generate_preview(
            output_path=preview_output,
            num_clips=10,
            clip_duration=3,
            resolution="480",  # 480p for faster loading (height as string)
            create_gif=False  # We don't need GIF for hover preview
        )
        
        if not result or not os.path.exists(preview_output):
            return {
                'success': False,
                'error': 'Preview generation failed'
            }
        
        preview_size_mb = os.path.getsize(preview_output) / (1024 * 1024)
        print(f"✓ Preview generated: {preview_output}")
        print(f"  Size: {preview_size_mb:.2f} MB")
        print(f"  Duration: ~30 seconds")
        
    except Exception as e:
        print(f"❌ Preview generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'Preview generation error: {str(e)}'
        }
    
    # Step 2: Upload to Internet Archive
    print("\n[2/3] Uploading to Internet Archive...")
    print("-" * 60)
    
    try:
        from upload_to_ia import upload_preview_to_internet_archive
        
        ia_result = upload_preview_to_internet_archive(
            preview_output,
            video_code,
            video_title
        )
        
        if not ia_result['success']:
            # Cleanup preview file
            if os.path.exists(preview_output):
                os.remove(preview_output)
            return {
                'success': False,
                'error': f"Internet Archive upload failed: {ia_result.get('error')}"
            }
        
        print(f"✓ Uploaded to Internet Archive")
        print(f"  Direct URL: {ia_result['direct_url']}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup preview file
        if os.path.exists(preview_output):
            os.remove(preview_output)
        return {
            'success': False,
            'error': f'Upload error: {str(e)}'
        }
    
    # Step 3: Update database
    print("\n[3/3] Updating database...")
    print("-" * 60)
    
    try:
        database_path = Path(__file__).parent.parent / "database" / "combined_videos.json"
        
        if not database_path.exists():
            print(f"⚠️ Database not found: {database_path}")
        else:
            # Load database
            with open(database_path, 'r', encoding='utf-8') as f:
                videos = json.load(f)
            
            # Find and update video
            video_found = False
            for video in videos:
                if video.get('code') == video_code:
                    video['preview_ia'] = {
                        'identifier': ia_result['identifier'],
                        'direct_url': ia_result['direct_url'],
                        'details_url': ia_result['details_url'],
                        'filename': ia_result['filename'],
                        'file_size_mb': ia_result['file_size_mb'],
                        'uploaded_at': datetime.now().isoformat(),
                        'generated_at': datetime.now().isoformat()
                    }
                    video_found = True
                    print(f"✓ Updated database for {video_code}")
                    break
            
            if not video_found:
                print(f"⚠️ Video {video_code} not found in database")
            else:
                # Save database
                with open(database_path, 'w', encoding='utf-8') as f:
                    json.dump(videos, f, indent=2, ensure_ascii=False)
                print(f"✓ Database saved")
        
    except Exception as e:
        print(f"⚠️ Database update failed: {e}")
        # Don't fail the whole process if database update fails
    
    # Cleanup local preview file
    try:
        if os.path.exists(preview_output):
            os.remove(preview_output)
            print(f"✓ Cleaned up local preview file")
    except:
        pass
    
    # Success!
    print("\n" + "="*60)
    print("✓ WORKFLOW COMPLETE!")
    print("="*60)
    print(f"Preview URL: {ia_result['direct_url']}")
    print(f"Video Code: {video_code}")
    print("="*60 + "\n")
    
    return {
        'success': True,
        'video_code': video_code,
        'preview_url': ia_result['direct_url'],
        'details_url': ia_result['details_url'],
        'identifier': ia_result['identifier'],
        'file_size_mb': ia_result['file_size_mb']
    }


def batch_process_videos(video_directory, database_path=None):
    """
    Batch process all videos in a directory
    
    Args:
        video_directory: Directory containing video files
        database_path: Optional path to database (to get video codes)
    """
    video_dir = Path(video_directory)
    
    if not video_dir.exists():
        print(f"❌ Directory not found: {video_dir}")
        return
    
    # Find all video files
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
    video_files = []
    for ext in video_extensions:
        video_files.extend(video_dir.glob(f"*{ext}"))
    
    if not video_files:
        print(f"No video files found in {video_dir}")
        return
    
    print(f"\nFound {len(video_files)} video files")
    print("="*60 + "\n")
    
    # Load database to get video codes
    videos_db = {}
    if database_path:
        try:
            with open(database_path, 'r', encoding='utf-8') as f:
                db_videos = json.load(f)
                for v in db_videos:
                    # Try to match by filename or code
                    videos_db[v.get('code')] = v
        except Exception as e:
            print(f"⚠️ Could not load database: {e}")
    
    results = []
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] Processing: {video_file.name}")
        
        # Try to extract video code from filename
        # Assumes format like: MIDA-479.mp4 or MIDA-479_something.mp4
        video_code = video_file.stem.split('_')[0].split('.')[0].upper()
        
        # Get video title from database if available
        video_title = None
        if video_code in videos_db:
            video_title = videos_db[video_code].get('title')
        
        result = generate_and_upload_preview(
            str(video_file),
            video_code,
            video_title
        )
        
        results.append({
            'file': video_file.name,
            'code': video_code,
            'status': 'success' if result['success'] else 'failed',
            'url': result.get('preview_url') if result['success'] else None,
            'error': result.get('error') if not result['success'] else None
        })
    
    # Summary
    print("\n" + "="*60)
    print("BATCH PROCESSING SUMMARY")
    print("="*60)
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']
    
    print(f"Total: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print(f"\n✓ Successful:")
        for r in successful:
            print(f"  - {r['code']}: {r['url']}")
    
    if failed:
        print(f"\n❌ Failed:")
        for r in failed:
            print(f"  - {r['code']}: {r['error']}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single video: python generate_and_upload_preview.py <video_file> <video_code> [title]")
        print("  Batch:        python generate_and_upload_preview.py --batch <video_directory>")
        print("\nExamples:")
        print("  python generate_and_upload_preview.py MIDA-479.mp4 MIDA-479")
        print("  python generate_and_upload_preview.py --batch ../videos")
        sys.exit(1)
    
    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print("❌ Please provide video directory")
            sys.exit(1)
        
        video_dir = sys.argv[2]
        db_path = sys.argv[3] if len(sys.argv) > 3 else None
        batch_process_videos(video_dir, db_path)
    else:
        if len(sys.argv) < 3:
            print("❌ Please provide video file and video code")
            sys.exit(1)
        
        video_file = sys.argv[1]
        video_code = sys.argv[2]
        video_title = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = generate_and_upload_preview(video_file, video_code, video_title)
        
        if result['success']:
            print(f"\n✓ Success! Preview URL: {result['preview_url']}")
        else:
            print(f"\n❌ Failed: {result.get('error')}")
            sys.exit(1)
