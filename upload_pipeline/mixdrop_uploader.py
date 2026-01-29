"""
MixDrop Uploader
Popular video hosting site used by many JAV sites
API Documentation: https://mixdrop.ag/api
"""
import requests
import os
from pathlib import Path
import time


class MixDropUploader:
    def __init__(self, email, api_key):
        self.email = email
        self.api_key = api_key
        self.base_url = "https://api.mixdrop.ag/api"
        
        # Create session for connection reuse
        self.session = requests.Session()
        
        # Optimize connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def get_upload_server(self):
        """Get upload server URL"""
        try:
            url = f"{self.base_url}?email={self.email}&key={self.api_key}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                return None, f"Failed to get upload server: HTTP {response.status_code}"
            
            data = response.json()
            
            if not data.get('success'):
                return None, data.get('msg', 'Failed to get upload server')
            
            return data['result']['url'], None
            
        except Exception as e:
            return None, f"Error getting upload server: {str(e)}"
    
    def upload(self, video_path, title=None):
        """Upload video to MixDrop"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            
            print(f"[MixDrop] Starting upload: {file_name}")
            
            # MixDrop uses direct upload URL (no need to get upload server)
            upload_url = "https://ul.mixdrop.ag/api"
            print(f"[MixDrop] Upload URL: {upload_url}")
            
            # Upload file
            print(f"[MixDrop] Uploading file...")
            file_size = os.path.getsize(video_path)
            size_mb = file_size / (1024 * 1024)
            
            with open(video_path, 'rb') as f:
                files = {'file': (file_name, f, 'video/mp4')}
                data = {
                    'email': self.email,
                    'key': self.api_key
                }
                
                start_time = time.time()
                
                try:
                    upload_response = self.session.post(
                        upload_url,
                        files=files,
                        data=data,
                        timeout=1800
                    )
                except Exception as e:
                    return {"success": False, "error": f"Upload failed: {str(e)}"}
                
                elapsed = time.time() - start_time
                speed = (size_mb / elapsed) if elapsed > 0 else 0
                
                print(f"[MixDrop] Upload completed in {elapsed:.1f}s ({speed:.2f} MB/s)")
                print(f"[MixDrop] Response status: {upload_response.status_code}")
                
                if upload_response.status_code == 200:
                    result = upload_response.json()
                    print(f"[MixDrop] Response: {result}")
                    
                    if result.get('success'):
                        # Safely extract file code
                        result_data = result.get('result', {})
                        file_code = result_data.get('fileref')
                        
                        if not file_code:
                            return {"success": False, "error": f"No file code in response: {result}"}
                        
                        print(f"[MixDrop] ✓ Upload successful: {file_code}")
                        return {
                            "success": True,
                            "host": "mixdrop",
                            "file_code": file_code,
                            "url": result_data.get('url', f"https://mixdrop.ag/f/{file_code}"),
                            "embed_url": result_data.get('embedurl', f"https://mixdrop.ag/e/{file_code}")
                        }
                    else:
                        return {"success": False, "error": result.get('msg', 'Upload failed')}
                else:
                    return {"success": False, "error": f"HTTP {upload_response.status_code}: {upload_response.text[:200]}"}
                    
        except Exception as e:
            print(f"[MixDrop] Error: {str(e)}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    email = os.getenv("MIXDROP_EMAIL")
    api_key = os.getenv("MIXDROP_API_KEY")
    
    if not email or not api_key:
        print("Error: MIXDROP_EMAIL and MIXDROP_API_KEY not found in .env file")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python mixdrop_uploader.py <video_file> [title]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    
    uploader = MixDropUploader(email, api_key)
    result = uploader.upload(video_path, title)
    
    if result['success']:
        print(f"\n✓ Upload successful!")
        print(f"  File Code: {result['file_code']}")
        print(f"  URL: {result['url']}")
        print(f"  Embed URL: {result['embed_url']}")
    else:
        print(f"\n✗ Upload failed: {result['error']}")
