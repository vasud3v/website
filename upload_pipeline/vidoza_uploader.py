import requests
import os
from pathlib import Path
import time
import urllib3
from tqdm import tqdm

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VidozaUploader:
    def __init__(self, email, password, api_key):
        self.email = email
        self.password = password
        self.api_key = api_key
        self.base_url = "https://api.vidoza.net/v1"
        
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
        """Upload video to Vidoza using their 2-stage upload process"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            
            print(f"[Vidoza] Starting upload: {file_name}")
            
            # Stage 1: Get upload server
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
                'cache-control': 'no-cache',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"[Vidoza] Getting upload server...")
            try:
                server_response = self.session.get(
                    f"{self.base_url}/upload/http/server",
                    headers=headers,
                    timeout=30
                )
            except Exception as e:
                return {"success": False, "error": f"Connection error: {str(e)}"}
            
            if server_response.status_code != 200:
                return {"success": False, "error": f"Failed to get upload server: {server_response.status_code}"}
            
            server_data = server_response.json()
            if not server_data.get('data'):
                return {"success": False, "error": "No upload server data received"}
            
            upload_url = server_data['data']['upload_url']
            upload_params = server_data['data']['upload_params']
            
            print(f"[Vidoza] Upload server: {upload_url}")
            
            # Stage 2: Upload file with progress bar
            print(f"[Vidoza] Uploading file...")
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
                    data = upload_params.copy()
                    data['title'] = title
                    
                    start_time = time.time()
                    
                    # Try upload with retry on connection errors
                    max_retries = 3
                    last_error = None
                    
                    for attempt in range(max_retries):
                        try:
                            # Reset file position for retries
                            if attempt > 0:
                                f.seek(0)
                                progress_file = ProgressFileWrapper(f, pbar)
                                files = {'file': (file_name, progress_file, 'video/mp4')}
                                print(f"\n[Vidoza] Retry attempt {attempt + 1}/{max_retries}...")
                            
                            response = self.session.post(
                                upload_url,
                                files=files,
                                data=data,
                                timeout=1800,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                    'Connection': 'keep-alive'
                                }
                            )
                            break  # Success, exit retry loop
                            
                        except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                            last_error = str(e)
                            if attempt < max_retries - 1:
                                print(f"\n[Vidoza] Connection error: {last_error}")
                                print(f"[Vidoza] Waiting 5 seconds before retry...")
                                time.sleep(5)
                            else:
                                return {"success": False, "error": f"Upload failed after {max_retries} attempts: {last_error}"}
                        except Exception as e:
                            return {"success": False, "error": f"Upload failed: {str(e)}"}
                    
                    elapsed = time.time() - start_time
                    speed_mbps = (file_size / (1024*1024)) / elapsed if elapsed > 0 else 0
                    
                    print(f"\n[Vidoza] Upload completed in {elapsed:.1f}s (avg {speed_mbps:.2f} MB/s)")
                    print(f"[Vidoza] Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"[Vidoza] Response: {result}")
                        
                        if result.get('status') == 'OK':
                            file_code = result.get('code')
                            print(f"[Vidoza] ✓ Upload successful: {file_code}")
                            return {
                                "success": True,
                                "host": "vidoza",
                                "file_code": file_code,
                                "video_id": file_code,
                                "url": f"https://vidoza.net/{file_code}.html",
                                "embed_url": f"https://vidoza.net/embed-{file_code}.html"
                            }
                        else:
                            return {"success": False, "error": result.get('msg', 'Upload failed')}
                    else:
                        return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                    
        except Exception as e:
            print(f"[Vidoza] Error: {str(e)}")
            return {"success": False, "error": str(e)}
