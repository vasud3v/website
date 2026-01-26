import requests
import os
from pathlib import Path
import time
import urllib3
from tqdm import tqdm

# Disable SSL warnings for expired certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TurboviplayUploader:
    def __init__(self, email, username, password, api_key):
        self.email = email
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = "https://api.turboviplay.com"
        
        # Create session for connection reuse
        self.session = requests.Session()
        self.session.verify = False
        
        # Optimize connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def upload(self, video_path, title=None):
        """Upload video to Turboviplay"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            
            print(f"[Turboviplay] Starting upload: {file_name}")
            
            # Get upload server
            print(f"[Turboviplay] Getting upload server...")
            server_response = self.session.get(
                f"{self.base_url}/uploadserver",
                params={'keyApi': self.api_key},
                timeout=30
            )
            
            if server_response.status_code != 200:
                return {"success": False, "error": f"Failed to get upload server: {server_response.status_code} - {server_response.text[:200]}"}
            
            try:
                server_data = server_response.json()
            except Exception as e:
                return {"success": False, "error": f"Invalid JSON response: {server_response.text[:200]}"}
            
            if server_data.get('status') != 200:
                return {"success": False, "error": server_data.get('msg', 'Failed to get upload server')}
            
            upload_url = server_data.get('result')
            
            if not upload_url:
                return {"success": False, "error": f"No upload URL in response: {server_data}"}
            
            print(f"[Turboviplay] Upload server: {upload_url}")
            
            # Upload file with progress bar
            print(f"[Turboviplay] Uploading file...")
            file_size = os.path.getsize(video_path)
            
            with open(video_path, 'rb') as f:
                # Wrap file with tqdm progress bar
                with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, 
                         desc=f"📤 {file_name}", leave=False) as pbar:
                    
                    # Create a wrapper that updates progress
                    class ProgressFileWrapper:
                        def __init__(self, file_obj, progress_bar):
                            self.file_obj = file_obj
                            self.progress_bar = progress_bar
                            self.bytes_read = 0
                        
                        def read(self, size=-1):
                            data = self.file_obj.read(size)
                            self.bytes_read += len(data)
                            self.progress_bar.update(len(data))
                            return data
                        
                        def __len__(self):
                            return file_size
                    
                    progress_file = ProgressFileWrapper(f, pbar)
                    
                    files = {'file': (file_name, progress_file, 'video/mp4')}
                    data = {'keyapi': self.api_key}
                    
                    start_time = time.time()
                    
                    try:
                        response = self.session.post(
                            upload_url,
                            files=files,
                            data=data,
                            timeout=1800  # 30 minutes timeout
                        )
                    except requests.exceptions.Timeout:
                        return {"success": False, "error": "Upload timeout. File may be too large or network is slow."}
                    except requests.exceptions.ConnectionError as e:
                        return {"success": False, "error": f"Connection error: {str(e)}"}
                    
                    elapsed = time.time() - start_time
                    speed_mbps = (file_size / (1024*1024)) / elapsed if elapsed > 0 else 0
                    
                    print(f"\n[Turboviplay] Upload completed in {elapsed:.1f}s (avg {speed_mbps:.2f} MB/s)")
                    print(f"[Turboviplay] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    # Check if response is empty
                    if not response.text or response.text.strip() == '':
                        return {"success": False, "error": "Empty response from server. Try again or check dashboard."}
                    
                    try:
                        result = response.json()
                        print(f"[Turboviplay] Response: {result}")
                    except Exception as e:
                        return {"success": False, "error": f"Invalid JSON: {response.text[:200]}"}
                    
                    # API can return two formats:
                    # Format 1: {"videoID": "6977acc01633c", "title": "test.mp4"}
                    # Format 2: {"videoID": {"status":0, "slug":"...", "title":"..."}, "title":"..."}
                    video_data = result.get('videoID')
                    
                    if isinstance(video_data, str):
                        # Format 1: videoID is directly the ID string
                        video_id = video_data
                    elif isinstance(video_data, dict):
                        # Format 2: videoID is an object with slug
                        video_id = video_data.get('slug')
                    else:
                        return {"success": False, "error": f"Unexpected videoID format: {result}"}
                    
                    if not video_id:
                        return {"success": False, "error": f"No video ID in response: {result}"}
                    
                    print(f"[Turboviplay] ✓ Upload successful: {video_id}")
                    return {
                        "success": True,
                        "host": "turboviplay",
                        "video_id": video_id,
                        "url": f"https://turboviplay.com/v/{video_id}",
                        "embed_url": f"https://emturbovid.com/t/{video_id}"
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                    
        except Exception as e:
            print(f"[Turboviplay] Error: {str(e)}")
            return {"success": False, "error": str(e)}
