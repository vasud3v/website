#!/usr/bin/env python3
"""
Internet Archive Uploader for Preview Videos
Uploads preview videos to archive.org and returns direct MP4 links
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

try:
    import internetarchive as ia
    IA_AVAILABLE = True
except ImportError:
    print("⚠️ internetarchive package not installed")
    print("Install with: pip install internetarchive")
    IA_AVAILABLE = False


class InternetArchiveUploader:
    """Upload preview videos to Internet Archive"""
    
    def __init__(self, access_key=None, secret_key=None):
        """
        Initialize Internet Archive uploader
        
        Args:
            access_key: IA S3 access key (or set IA_ACCESS_KEY env var)
            secret_key: IA S3 secret key (or set IA_SECRET_KEY env var)
        """
        if not IA_AVAILABLE:
            raise ImportError("internetarchive package not installed")
        
        # HARDCODED CREDENTIALS (User Requested)
        self.access_key = 'lbNeBqUDERoIQXdo'
        self.secret_key = 'lCXTAjHpGcthPep4'
        
        # Configure session
        self.session = ia.get_session(config={
            's3': {
                'access': self.access_key,
                'secret': self.secret_key
            }
        })
        
        print("✅ Internet Archive session initialized")
    
    def generate_identifier(self, video_code):
        """
        Generate unique identifier for Internet Archive
        Format: javmix-preview-{code}-{timestamp}
        """
        timestamp = datetime.now().strftime('%Y%m%d')
        identifier = f"javmix-preview-{video_code.lower()}-{timestamp}"
        return identifier
    
    def upload_preview(self, preview_path, video_code, metadata=None):
        """
        Upload preview video to Internet Archive
        
        Args:
            preview_path: Path to preview video file
            video_code: Video code (e.g., MIDE-486)
            metadata: Optional metadata dict
        
        Returns:
            dict: Upload result with direct MP4 link
        """
        try:
            if not os.path.exists(preview_path):
                return {
                    'success': False,
                    'error': f'Preview file not found: {preview_path}'
                }
            
            file_size_mb = os.path.getsize(preview_path) / (1024 * 1024)
            
            print(f"\n{'='*70}")
            print(f"📤 UPLOADING TO INTERNET ARCHIVE")
            print(f"{'='*70}")
            print(f"Video Code: {video_code}")
            print(f"Preview File: {preview_path}")
            print(f"File Size: {file_size_mb:.2f} MB")
            
            # Generate identifier
            identifier = self.generate_identifier(video_code)
            print(f"Identifier: {identifier}")
            
            # Prepare metadata
            ia_metadata = {
                'title': f'{video_code} - Preview',
                'mediatype': 'movies',
                'collection': 'opensource_movies',
                'description': f'Preview video for {video_code}',
                'subject': ['preview', 'video', video_code.lower()],
                'creator': 'Javmix Scraper',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'language': 'jpn',
                'licenseurl': 'https://creativecommons.org/licenses/by-nc/4.0/'
            }
            
            # Add custom metadata if provided
            if metadata:
                if metadata.get('title'):
                    ia_metadata['title'] = f"{video_code} - {metadata['title']}"
                if metadata.get('actors'):
                    ia_metadata['subject'].extend(metadata['actors'])
                if metadata.get('studio'):
                    ia_metadata['publisher'] = metadata['studio']
                if metadata.get('release_date'):
                    ia_metadata['date'] = metadata['release_date']
            
            print(f"\n📝 Metadata:")
            print(f"  Title: {ia_metadata['title']}")
            print(f"  Collection: {ia_metadata['collection']}")
            
            # Get or create item
            item = self.session.get_item(identifier)
            
            # Upload file
            print(f"\n⬆️ Uploading to archive.org...")
            print(f"  This may take a few minutes...")
            
            filename = os.path.basename(preview_path)
            
            # Check if file already exists in the item
            if item.exists:
                existing_files = [f['name'] for f in item.files]
                if filename in existing_files:
                    print(f"  ℹ️ File already exists in item, will overwrite")
            
            result = item.upload(
                preview_path,
                metadata=ia_metadata,
                access_key=self.access_key,
                secret_key=self.secret_key,
                verbose=True,
                checksum=True,
                retries=3,
                retries_sleep=10
            )
            
            # Check if upload was successful
            # result is a list of Response objects
            if not result or len(result) == 0:
                error_msg = "Upload failed: No response from Internet Archive"
                print(f"\n❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Check status code
            status_code = result[0].status_code if hasattr(result[0], 'status_code') else None
            
            if status_code is None:
                # Sometimes IA returns success without status code
                # Check if file exists in item now
                item.refresh()
                existing_files = [f['name'] for f in item.files]
                if filename in existing_files:
                    print(f"  ✅ File verified in item (upload successful)")
                    status_code = 200  # Treat as success
                else:
                    error_msg = "Upload failed: File not found in item after upload"
                    print(f"\n❌ {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg
                    }
            
            if status_code in [200, 201]:
                # Generate direct MP4 link
                direct_link = f"https://archive.org/download/{identifier}/{filename}"
                
                # Generate player link
                player_link = f"https://archive.org/details/{identifier}"
                
                # Generate embed URL (for iframe src)
                embed_url = f"https://archive.org/embed/{identifier}"
                
                # Generate full embed/iframe code
                embed_code = f'<iframe src="{embed_url}" width="640" height="480" frameborder="0" webkitallowfullscreen="true" mozallowfullscreen="true" allowfullscreen></iframe>'
                
                # Alternative embed sizes
                embed_code_small = f'<iframe src="{embed_url}" width="480" height="360" frameborder="0" allowfullscreen></iframe>'
                embed_code_large = f'<iframe src="{embed_url}" width="854" height="480" frameborder="0" allowfullscreen></iframe>'
                
                print(f"\n✅ UPLOAD SUCCESSFUL")
                print(f"{'='*70}")
                print(f"Direct MP4 Link: {direct_link}")
                print(f"Player Link: {player_link}")
                print(f"Embed URL: {embed_url}")
                print(f"{'='*70}")
                
                return {
                    'success': True,
                    'identifier': identifier,
                    'direct_mp4_link': direct_link,
                    'player_link': player_link,
                    'embed_url': embed_url,
                    'embed_code': embed_code,
                    'embed_code_small': embed_code_small,
                    'embed_code_large': embed_code_large,
                    'filename': filename,
                    'file_size_mb': round(file_size_mb, 2),
                    'uploaded_at': datetime.now().isoformat()
                }
            else:
                error_msg = f"Upload failed with status code: {status_code}"
                print(f"\n❌ {error_msg}")
                print(f"  Response: {result[0].text if hasattr(result[0], 'text') else 'No response text'}")
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': status_code
                }
        
        except Exception as e:
            error_msg = f"Error uploading to Internet Archive: {str(e)}"
            print(f"\n❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def check_item_exists(self, identifier):
        """Check if item already exists on Internet Archive"""
        try:
            item = self.session.get_item(identifier)
            return item.exists
        except:
            return False
    
    def get_item_info(self, identifier):
        """Get information about an uploaded item"""
        try:
            item = self.session.get_item(identifier)
            if item.exists:
                return {
                    'identifier': identifier,
                    'url': f"https://archive.org/details/{identifier}",
                    'metadata': item.metadata,
                    'files': [f['name'] for f in item.files]
                }
            return None
        except Exception as e:
            print(f"Error getting item info: {e}")
            return None


def save_to_database(video_code, ia_result, db_path="../database/internet_archive_previews.json"):
    """Save Internet Archive upload info to database"""
    try:
        # Load existing database
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                db = json.load(f)
        else:
            db = {
                "previews": [],
                "stats": {
                    "total_previews": 0,
                    "total_size_mb": 0
                }
            }
        
        # Add new entry
        preview_entry = {
            "id": len(db['previews']) + 1,
            "video_code": video_code,
            "identifier": ia_result['identifier'],
            "direct_mp4_link": ia_result['direct_mp4_link'],
            "player_link": ia_result['player_link'],
            "embed_code": ia_result['embed_code'],
            "filename": ia_result['filename'],
            "file_size_mb": ia_result['file_size_mb'],
            "uploaded_at": ia_result['uploaded_at']
        }
        
        db['previews'].append(preview_entry)
        
        # Update stats
        db['stats']['total_previews'] = len(db['previews'])
        db['stats']['total_size_mb'] = round(
            sum(p.get('file_size_mb', 0) for p in db['previews']), 2
        )
        
        # Save database
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved to database: {db_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        return False


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Upload preview videos to Internet Archive',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a preview video
  python internet_archive_uploader.py preview.mp4 MIDE-486
  
  # Upload with custom metadata
  python internet_archive_uploader.py preview.mp4 MIDE-486 --title "My Video"
  
Environment Variables:
  IA_ACCESS_KEY    Internet Archive S3 access key
  IA_SECRET_KEY    Internet Archive S3 secret key
  
Get your keys from: https://archive.org/account/s3.php
        """
    )
    
    parser.add_argument('preview_path', help='Path to preview video file')
    parser.add_argument('video_code', help='Video code (e.g., MIDE-486)')
    parser.add_argument('--title', help='Video title')
    parser.add_argument('--access-key', help='IA access key (or use IA_ACCESS_KEY env var)')
    parser.add_argument('--secret-key', help='IA secret key (or use IA_SECRET_KEY env var)')
    
    args = parser.parse_args()
    
    if not IA_AVAILABLE:
        print("❌ internetarchive package not installed")
        print("Install with: pip install internetarchive")
        sys.exit(1)
    
    if not os.path.exists(args.preview_path):
        print(f"❌ Preview file not found: {args.preview_path}")
        sys.exit(1)
    
    try:
        # Initialize uploader
        uploader = InternetArchiveUploader(
            access_key=args.access_key,
            secret_key=args.secret_key
        )
        
        # Prepare metadata
        metadata = {}
        if args.title:
            metadata['title'] = args.title
        
        # Upload
        result = uploader.upload_preview(
            args.preview_path,
            args.video_code,
            metadata=metadata
        )
        
        if result['success']:
            # Save to database
            save_to_database(args.video_code, result)
            
            print("\n✅ Upload completed successfully!")
            print(f"\n📋 Direct MP4 Link:")
            print(f"   {result['direct_mp4_link']}")
            sys.exit(0)
        else:
            print(f"\n❌ Upload failed: {result['error']}")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
