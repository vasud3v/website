import requests
import os
from pathlib import Path
import time
import urllib3
from tqdm import tqdm

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class StreamtapeUploader:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = "https://api.streamtape.com"
        
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
        """Upload video to Streamtape"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            
            print(f"[Streamtape] Starting upload: {file_name}")
            
            # Get upload URL
            upload_url_endpoint = f"{self.base_url}/file/ul?login={self.username}&key={self.password}"
            response = requests.get(upload_url_endpoint)
            
            if response.status_code != 200:
                return {"success": False, "error": f"Failed to get upload URL: {response.status_code}"}
            
            data = response.json()
            if data.get('status') != 200:
                return {"success": False, "error": data.get('msg', 'Failed to get upload URL')}
            
            # Get upload URL
            print(f"[Streamtape] Getting upload URL...")
            upload_url_endpoint = f"{self.base_url}/file/ul?login={self.username}&key={self.password}"
            response = self.session.get(upload_url_endpoint, timeout=30)
            
            if response.status_code != 200:
                return {"success": False, "error": f"Failed to get upload URL: {response.status_code}"}
            
            data = response.json()
            if data.get('status') != 200:
                return {"success": False, "error": data.get('msg', 'Failed to get upload URL')}
            
            upload_url = data['result']['url']
            print(f"[Streamtape] Upload URL: {upload_url}")
            
            # Upload file with progress bar
            print(f"[Streamtape] Uploading file...")
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
                    
                    files = {'file1': (file_name, progress_file, 'video/mp4')}
                    
                    start_time = time.time()
                    
                    try:
                        upload_response = self.session.post(
                            upload_url,
                            files=files,
                            timeout=1800
                        )
                    except Exception as e:
                        return {"success": False, "error": f"Upload failed: {str(e)}"}
                    
                    elapsed = time.time() - start_time
                    speed_mbps = (file_size / (1024*1024)) / elapsed if elapsed > 0 else 0
                    
                    print(f"\n[Streamtape] Upload completed in {elapsed:.1f}s (avg {speed_mbps:.2f} MB/s)")
                    print(f"[Streamtape] Response status: {upload_response.status_code}")
                
                if upload_response.status_code == 200:
                    result = upload_response.json()
                    print(f"[Streamtape] Response: {result}")
                    
                    if result.get('status') == 200:
                        file_id = result['result']['id']
                        print(f"[Streamtape] ✓ Upload successful: {file_id}")
                        return {
                            "success": True,
                            "host": "streamtape",
                            "file_id": file_id,
                            "url": result['result']['url'],
                            "embed_url": f"https://streamtape.com/e/{file_id}"
                        }
                    else:
                        return {"success": False, "error": result.get('msg', 'Upload failed')}
                else:
                    return {"success": False, "error": f"HTTP {upload_response.status_code}: {upload_response.text[:200]}"}
                    
        except Exception as e:
            print(f"[Streamtape] Error: {str(e)}")
            return {"success": False, "error": str(e)}
