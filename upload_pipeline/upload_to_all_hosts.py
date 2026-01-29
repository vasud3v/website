"""
Upload video to all configured hosts in parallel and save to individual databases
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add parent directory to path for database_manager import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_manager import db_manager

# Import all uploaders
from seekstreaming_uploader import SeekstreamingUploader
from streamtape_uploader import StreamtapeUploader
from turboviplay_uploader import TurboviplayUploader
from vidoza_uploader import VidozaUploader
from uploady_uploader import UploadyUploader

load_dotenv()

# Thread-safe print lock
print_lock = threading.Lock()

class MultiHostUploader:
    def __init__(self):
        self.uploaders = {}
        self.databases = {}
        
        # Initialize SeekStreaming
        if os.getenv('SEEKSTREAMING_API_KEY'):
            self.uploaders['seekstreaming'] = SeekstreamingUploader(
                api_key=os.getenv('SEEKSTREAMING_API_KEY')
            )
            self.databases['seekstreaming'] = "../database/seekstreaming_host.json"
        
        # Initialize Streamtape
        if os.getenv('STREAMTAPE_USERNAME') and os.getenv('STREAMTAPE_PASSWORD'):
            self.uploaders['streamtape'] = StreamtapeUploader(
                username=os.getenv('STREAMTAPE_USERNAME'),
                password=os.getenv('STREAMTAPE_PASSWORD')
            )
            self.databases['streamtape'] = "../database/streamtape_host.json"
        
        # Initialize Turboviplay
        if os.getenv('TURBOVIPLAY_API_KEY'):
            self.uploaders['turboviplay'] = TurboviplayUploader(
                email=os.getenv('TURBOVIPLAY_EMAIL'),
                username=os.getenv('TURBOVIPLAY_USERNAME'),
                password=os.getenv('TURBOVIPLAY_PASSWORD'),
                api_key=os.getenv('TURBOVIPLAY_API_KEY')
            )
            self.databases['turboviplay'] = "../database/turboviplay_host.json"
        
        # Initialize Vidoza
        if os.getenv('VIDOZA_API_KEY'):
            self.uploaders['vidoza'] = VidozaUploader(
                email=os.getenv('VIDOZA_EMAIL'),
                password=os.getenv('VIDOZA_PASSWORD'),
                api_key=os.getenv('VIDOZA_API_KEY')
            )
            self.databases['vidoza'] = "../database/vidoza_host.json"
        
        # Initialize Uploady
        if os.getenv('UPLOADY_API_KEY'):
            self.uploaders['uploady'] = UploadyUploader(
                email=os.getenv('UPLOADY_EMAIL'),
                username=os.getenv('UPLOADY_USERNAME'),
                api_key=os.getenv('UPLOADY_API_KEY')
            )
            self.databases['uploady'] = "../database/uploady_host.json"
    
    def load_database(self, db_path):
        """Load database"""
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"videos": [], "stats": {"total_videos": 0, "total_size_mb": 0}}
    
    def save_database(self, db_path, data):
        """Save database"""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_to_database(self, host, video_info, result):
        """Save video to host-specific database"""
        db_path = self.databases.get(host)
        if not db_path:
            return
        
        db = self.load_database(db_path)
        
        # Create video entry based on host
        new_video = {
            "id": len(db['videos']) + 1,
            "title": video_info['title'],
            "filename": video_info['filename'],
            "file_size_mb": video_info['file_size_mb'],
            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add host-specific fields
        if host == 'seekstreaming':
            new_video.update({
                "video_player": result['all_urls']['video_player'],
                "video_downloader": result['all_urls']['video_downloader'],
                "embed_code": result['all_urls']['embed_code']
            })
        elif host == 'streamtape':
            new_video.update({
                "file_id": result['file_id'],
                "video_player": result['embed_url'],
                "video_downloader": result['url'],
                "embed_code": f'<iframe src="{result["embed_url"]}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
            })
        elif host == 'turboviplay':
            new_video.update({
                "video_id": result['video_id'],
                "video_player": result['embed_url'],
                "video_downloader": result['url'],
                "embed_code": f'<iframe src="{result["embed_url"]}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
            })
        elif host == 'vidoza':
            new_video.update({
                "video_id": result['video_id'],
                "video_player": result['embed_url'],
                "video_downloader": result['url'],
                "embed_code": f'<iframe src="{result["embed_url"]}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
            })
        elif host == 'uploady':
            new_video.update({
                "file_code": result['file_code'],
                "video_player": result['embed_url'],
                "video_downloader": result['url'],
                "embed_code": f'<iframe src="{result["embed_url"]}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>'
            })
        
        db['videos'].append(new_video)
        db['stats']['total_videos'] = len(db['videos'])
        db['stats']['total_size_mb'] = round(sum(v.get('file_size_mb', 0) for v in db['videos']), 2)
        
        self.save_database(db_path, db)
    
    def upload_to_single_host(self, host, uploader, video_path, video_title, video_info):
        """Upload to a single host (thread-safe)"""
        try:
            with print_lock:
                print(f"\n[{host.upper()}] Starting upload...")
                print("-" * 70)
            
            result = uploader.upload(video_path, video_title)
            
            if result.get('success'):
                with print_lock:
                    print(f"[{host.upper()}] ✓ Upload successful!")
                
                # Save to host-specific database
                self.save_to_database(host, video_info, result)
                
                with print_lock:
                    print(f"[{host.upper()}] ✓ Saved to host database")
                
                return {
                    'host': host,
                    'success': True,
                    'result': result
                }
            else:
                with print_lock:
                    print(f"[{host.upper()}] ✗ Upload failed: {result.get('error')}")
                
                return {
                    'host': host,
                    'success': False,
                    'error': result.get('error')
                }
        except Exception as e:
            with print_lock:
                print(f"[{host.upper()}] ✗ Error: {str(e)}")
            
            return {
                'host': host,
                'success': False,
                'error': str(e)
            }
    
    def upload_to_all(self, video_path, title=None, max_workers=5):
        """Upload to all configured hosts"""
        if not os.path.exists(video_path):
            print(f"✗ Video file not found: {video_path}")
            return {}
        
        file_name = os.path.basename(video_path)
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        video_title = title or os.path.splitext(file_name)[0]
        
        video_info = {
            'title': video_title,
            'filename': file_name,
            'file_size_mb': round(file_size_mb, 2)
        }
        
        print("=" * 70)
        print("MULTI-HOST VIDEO UPLOADER (PARALLEL)")
        print("=" * 70)
        print(f"\nVideo: {file_name}")
        print(f"Size: {file_size_mb:.2f} MB")
        print(f"Title: {video_title}")
        print(f"\nConfigured hosts: {len(self.uploaders)}")
        print(f"Parallel uploads: {min(max_workers, len(self.uploaders))}")
        print("=" * 70)
        print()
        
        results = {}
        
        # Upload to all hosts in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all upload tasks
            future_to_host = {
                executor.submit(
                    self.upload_to_single_host,
                    host,
                    uploader,
                    video_path,
                    video_title,
                    video_info
                ): host
                for host, uploader in self.uploaders.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_host):
                host = future_to_host[future]
                try:
                    result = future.result()
                    results[result['host']] = result
                except Exception as e:
                    with print_lock:
                        print(f"[{host.upper()}] ✗ Thread error: {str(e)}")
                    results[host] = {
                        'success': False,
                        'error': str(e)
                    }
        
        # Summary
        print()
        print("=" * 70)
        print("UPLOAD SUMMARY")
        print("=" * 70)
        
        successful = [h for h, r in results.items() if r.get('success')]
        failed = [h for h, r in results.items() if not r.get('success')]
        
        print(f"\n✓ Successful: {len(successful)}/{len(results)}")
        if successful:
            for host in successful:
                print(f"  - {host}")
        
        if failed:
            print(f"\n✗ Failed: {len(failed)}/{len(results)}")
            for host in failed:
                print(f"  - {host}: {results[host].get('error')}")
        
        print(f"\n📁 Databases saved in: database/")
        
        # Update main combined database with hosting URLs
        if successful:
            print(f"\n🔄 Syncing to main database...")
            self.sync_to_main_database(video_title, results)
        
        print()
        
        return results
    
    def sync_to_main_database(self, video_title, results):
        """Sync upload results to main combined_videos.json"""
        try:
            # Find video by title/code in main database
            video = db_manager.get_video_by_code(video_title)
            
            if not video:
                print(f"⚠️ Video '{video_title}' not found in main database, skipping sync")
                return
            
            # Update hosting URLs
            if 'hosting_urls' not in video:
                video['hosting_urls'] = {}
            
            for host, result in results.items():
                if result.get('success'):
                    host_result = result.get('result', {})
                    
                    # Initialize host entry if not exists
                    if host not in video['hosting_urls']:
                        video['hosting_urls'][host] = {}
                    
                    # Map different host response formats
                    if host == 'seekstreaming':
                        video['hosting_urls'][host] = {
                            'embed_url': host_result.get('all_urls', {}).get('video_player', ''),
                            'download_url': host_result.get('all_urls', {}).get('video_downloader', ''),
                            'file_code': host_result.get('all_urls', {}).get('video_player', '').split('#')[-1] if host_result.get('all_urls', {}).get('video_player') else ''
                        }
                    elif host == 'streamtape':
                        video['hosting_urls'][host] = {
                            'embed_url': host_result.get('embed_url', ''),
                            'download_url': host_result.get('url', ''),
                            'file_code': host_result.get('file_id', '')
                        }
                    elif host == 'turboviplay':
                        video['hosting_urls'][host] = {
                            'embed_url': host_result.get('embed_url', ''),
                            'download_url': host_result.get('url', ''),
                            'file_code': host_result.get('video_id', '')
                        }
                    elif host == 'vidoza':
                        video['hosting_urls'][host] = {
                            'embed_url': host_result.get('embed_url', ''),
                            'download_url': host_result.get('url', ''),
                            'file_code': host_result.get('video_id', '')
                        }
                    elif host == 'uploady':
                        video['hosting_urls'][host] = {
                            'embed_url': host_result.get('embed_url', ''),
                            'download_url': host_result.get('url', ''),
                            'file_code': host_result.get('file_code', '')
                        }
            
            # Update uploaded_at timestamp
            video['uploaded_at'] = datetime.now().isoformat()
            
            # Save back to main database
            if db_manager.add_or_update_video(video):
                print(f"✓ Synced hosting URLs to main database for '{video_title}'")
            else:
                print(f"✗ Failed to sync to main database")
                
        except Exception as e:
            print(f"✗ Error syncing to main database: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_to_all_hosts.py <video_path> [title]")
        print("\nExamples:")
        print("  python upload_to_all_hosts.py ../test.mp4")
        print("  python upload_to_all_hosts.py ../video.mp4 \"My Video Title\"")
        sys.exit(1)
    
    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    
    uploader = MultiHostUploader()
    
    if not uploader.uploaders:
        print("✗ No uploaders configured. Check your .env file.")
        sys.exit(1)
    
    results = uploader.upload_to_all(video_path, title)
    
    # Exit with success if at least one upload succeeded
    success = any(r.get('success') for r in results.values())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
