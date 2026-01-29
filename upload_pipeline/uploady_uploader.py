import requests
import os
from pathlib import Path
import time
import urllib3
from tqdm import tqdm

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class UploadyUploader:
    def __init__(self, email, username, api_key):
        self.email = email
        self.username = username
        self.api_key = api_key
        self.base_url = "https://uploady.io/api"
        
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
        """Upload video to Uploady (XFS-based host)"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            
            print(f"[Uploady] Starting upload: {file_name}")
            
            # Get upload server with retry
            print(f"[Uploady] Getting upload server...")
            server_response = None
            last_error = None
            
            for attempt in range(3):
                try:
                    server_response = self.session.get(
                        f"{self.base_url}/upload/server",
                        params={'key': self.api_key},
                        timeout=30
                    )
                    
                    if server_response.status_code == 200:
                        break
                    
                    last_error = f"Status {server_response.status_code}"
                    print(f"[Uploady] Attempt {attempt + 1} failed: {last_error}")
                    
                except Exception as e:
                    last_error = str(e)
                    print(f"[Uploady] Attempt {attempt + 1} error: {last_error}")
                
                if attempt < 2:
                    time.sleep(2)
            
            if not server_response or server_response.status_code != 200:
                return {"success": False, "error": f"Failed to get upload server after 3 attempts. Last error: {last_error}"}
            
            server_data = server_response.json()
            if server_data.get('status') != 200:
                return {"success": False, "error": server_data.get('msg', 'Failed to get upload server')}
            
            upload_url = server_data.get('result')
            sess_id = server_data.get('sess_id')
            print(f"[Uploady] Upload server: {upload_url}")
            print(f"[Uploady] Session ID: {sess_id}")
            
            # Upload file
            print(f"[Uploady] Uploading file...")
            file_size = os.path.getsize(video_path)
            size_mb = file_size / (1024 * 1024)
            
            with open(video_path, 'rb') as f:
                files = {'file': (file_name, f, 'video/mp4')}
                data = {'sess_id': sess_id}
                
                start_time = time.time()
                
                try:
                    response = self.session.post(
                        upload_url,
                        files=files,
                        data=data,
                        timeout=1800
                    )
                except Exception as e:
                    return {"success": False, "error": f"Upload failed: {str(e)}"}
                
                elapsed = time.time() - start_time
                speed = (size_mb / elapsed) if elapsed > 0 else 0
                
                print(f"[Uploady] Upload completed in {elapsed:.1f}s ({speed:.2f} MB/s)")
                print(f"[Uploady] Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"[Uploady] Response: {result}")
                
                # Response can be a list or dict
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                
                if isinstance(result, dict):
                    # Check for errors
                    file_status = result.get('file_status')
                    if file_status == 'failed':
                        error_msg = result.get('file_code', 'Unknown error')
                        return {"success": False, "error": f"Upload failed: {error_msg}"}
                    
                    file_code = result.get('file_code')
                    if file_code and file_code != 'undef':
                        print(f"[Uploady] ✓ Upload successful: {file_code}")
                        
                        return {
                            "success": True,
                            "host": "uploady",
                            "file_code": file_code,
                            "url": f"https://uploady.io/{file_code}",
                            "embed_url": f"https://uploady.io/embed-{file_code}.html"
                        }
                    else:
                        error_reason = result.get('file_status', 'Unknown error')
                        return {"success": False, "error": f"Upload rejected: {error_reason}"}
                else:
                    return {"success": False, "error": f"Unexpected response format: {result}"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                    
        except Exception as e:
            print(f"[Uploady] Error: {str(e)}")
            return {"success": False, "error": str(e)}
