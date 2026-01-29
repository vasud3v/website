import requests
import os
from pathlib import Path
import time
import urllib3
from tqdm import tqdm

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class StreamtapeUploader:
    def __init__(self, login, api_key):
        self.login = login
        self.api_key = api_key
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
            print(f"[Streamtape] Getting upload URL...")
            upload_url_endpoint = f"{self.base_url}/file/ul?login={self.login}&key={self.api_key}"
            
            # Retry getting upload URL
            for attempt in range(3):
                try:
                    response = self.session.get(upload_url_endpoint, timeout=30)
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"[Streamtape] Connection error, retrying...")
                        time.sleep(2)
                    else:
                        return {"success": False, "error": "Cannot connect to Streamtape (ISP blocking?)"}
            
            if response.status_code != 200:
                return {"success": False, "error": f"Failed to get upload URL: {response.status_code}"}
            
            data = response.json()
            if data.get('status') != 200:
                return {"success": False, "error": data.get('msg', 'Failed to get upload URL')}
            
            upload_url = data['result']['url']
            print(f"[Streamtape] Upload URL: {upload_url}")
            
            # Upload file
            print(f"[Streamtape] Uploading file...")
            file_size = os.path.getsize(video_path)
            size_mb = file_size / (1024 * 1024)
            
            # Retry logic for connection errors
            max_retries = 3
            upload_response = None
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        print(f"[Streamtape] Retry attempt {attempt + 1}/{max_retries}...")
                        time.sleep(5)
                    
                    with open(video_path, 'rb') as f:
                        files = {'file1': (file_name, f, 'video/mp4')}
                        
                        start_time = time.time()
                        upload_response = self.session.post(
                            upload_url,
                            files=files,
                            timeout=1800
                        )
                        elapsed = time.time() - start_time
                    
                    speed = (size_mb / elapsed) if elapsed > 0 else 0
                    print(f"[Streamtape] Upload completed in {elapsed:.1f}s ({speed:.2f} MB/s)")
                    print(f"[Streamtape] Response status: {upload_response.status_code}")
                    break  # Success
                    
                except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                    if attempt < max_retries - 1:
                        print(f"[Streamtape] Connection error, retrying...")
                    else:
                        return {"success": False, "error": f"Upload failed after {max_retries} attempts (ISP blocking?)"}
                except Exception as e:
                    return {"success": False, "error": f"Upload failed: {str(e)}"}
            
            # Check response after retry loop
            if upload_response and upload_response.status_code == 200:
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
                error_text = upload_response.text[:200] if upload_response else "No response"
                return {"success": False, "error": f"HTTP {upload_response.status_code if upload_response else 'N/A'}: {error_text}"}
                    
        except Exception as e:
            print(f"[Streamtape] Error: {str(e)}")
            return {"success": False, "error": str(e)}
