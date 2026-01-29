import requests
import os
from pathlib import Path
import time
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Upload18Uploader:
    def __init__(self, email, username, password, api_key):
        self.email = email
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = "https://upload18.com/api"
        self.max_retries = 30
        self.wait_seconds = 20
        
        # Optimized session
        self.session = requests.Session()
        self.session.verify = False
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1,
            pool_maxsize=1,
            max_retries=0,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def upload(self, video_path, title=None):
        """Upload video to Upload18 with queue retry logic"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            file_size = os.path.getsize(video_path)
            size_mb = file_size / (1024 * 1024)
            
            print(f"[Upload18] Uploading: {file_name} ({size_mb:.1f} MB)")
            
            # Upload with queue retry logic
            attempt = 0
            while attempt < self.max_retries:
                attempt += 1
                
                try:
                    print(f"[Upload18] Attempt {attempt}/{self.max_retries}...")
                    
                    # Open file fresh for each attempt
                    with open(video_path, 'rb') as f:
                        files = {'video': (file_name, f, 'video/mp4')}
                        data = {
                            'apikey': self.api_key,
                            'cid': '15',
                            'fid': '18'
                        }
                        
                        start_time = time.time()
                        
                        try:
                            response = self.session.post(
                                f"{self.base_url}/upload",
                                files=files,
                                data=data,
                                timeout=1800
                            )
                            elapsed = time.time() - start_time
                        except (ConnectionAbortedError, ConnectionResetError, ConnectionError) as e:
                            print(f"[Upload18] Connection error: {str(e)[:50]}")
                            if attempt < self.max_retries:
                                print(f"[Upload18] Retrying in {self.wait_seconds}s...")
                                time.sleep(self.wait_seconds)
                                continue
                            else:
                                return {"success": False, "error": f"Connection failed after {self.max_retries} attempts"}
                    
                    if response.status_code == 200:
                        result = response.json()
                        status = result.get('status', '')
                        msg = result.get('msg', '').lower()
                        
                        print(f"[Upload18] Full API Response: {result}")
                        
                        if status == 'success':
                            # Try all possible fields for video ID
                            vid = result.get('vid', '')
                            did = result.get('did', '')
                            
                            speed = (size_mb / elapsed) if elapsed > 0 else 0
                            
                            print(f"[Upload18] Upload response: vid='{vid}', did='{did}'")
                            
                            # If we have vid, use it directly
                            if vid and vid != '':
                                print(f"[Upload18] ✓ Success in {elapsed:.1f}s ({speed:.2f} MB/s): vid={vid}")
                                
                                return {
                                    "success": True,
                                    "host": "upload18",
                                    "vid": vid,
                                    "did": did,
                                    "url": f"https://upload18.com/play/index/{vid}",
                                    "embed_url": f"https://upload18.com/play/index/{vid}",
                                    "file_code": vid
                                }
                            
                            # If no vid but have did, try to get video details using did
                            if did:
                                print(f"[Upload18] No vid in response, trying /getvideodetail with did={did}...")
                                
                                # Wait a bit for video to be processed
                                time.sleep(5)
                                
                                try:
                                    detail_response = self.session.get(
                                        f"{self.base_url}/getvideodetail/{did}",
                                        params={'apikey': self.api_key},
                                        timeout=30
                                    )
                                    
                                    print(f"[Upload18] Detail API status: {detail_response.status_code}")
                                    
                                    if detail_response.status_code == 200:
                                        detail_data = detail_response.json()
                                        print(f"[Upload18] Video detail response: {detail_data}")
                                        
                                        if detail_data.get('status') == 'success':
                                            video_info = detail_data.get('data', {})
                                            real_vid = video_info.get('vid', '') or video_info.get('id', '') or video_info.get('file_code', '')
                                            
                                            if real_vid and real_vid != did:
                                                print(f"[Upload18] ✓ Got real vid from details: {real_vid}")
                                                
                                                return {
                                                    "success": True,
                                                    "host": "upload18",
                                                    "vid": real_vid,
                                                    "did": did,
                                                    "url": f"https://upload18.com/play/index/{real_vid}",
                                                    "embed_url": f"https://upload18.com/play/index/{real_vid}",
                                                    "file_code": real_vid
                                                }
                                        else:
                                            print(f"[Upload18] Detail API error: {detail_data.get('msg', 'Unknown')}")
                                    else:
                                        print(f"[Upload18] Detail API HTTP error: {detail_response.text[:200]}")
                                        
                                except Exception as e:
                                    print(f"[Upload18] Error getting video details: {str(e)}")
                                
                                # If detail fetch failed, use did as fallback
                                print(f"[Upload18] ⚠️ Using did as video ID (may not work): {did}")
                                return {
                                    "success": True,
                                    "host": "upload18",
                                    "vid": did,
                                    "did": did,
                                    "url": f"https://upload18.com/play/index/{did}",
                                    "embed_url": f"https://upload18.com/play/index/{did}",
                                    "file_code": did,
                                    "note": "Using did as vid - may need manual verification"
                                }
                            
                            return {"success": False, "error": f"No vid or did in response: {result}"}
                        
                        # Queue retry keywords from API docs
                        if any(k in msg for k in ['wait', 'processing', 'upload request', 'error on uploaded file']):
                            print(f"[Upload18] Queue busy, waiting {self.wait_seconds}s...")
                            time.sleep(self.wait_seconds)
                            continue
                        
                        return {"success": False, "error": result.get('msg', 'Upload failed')}
                    else:
                        if attempt < self.max_retries:
                            time.sleep(self.wait_seconds)
                            continue
                        return {"success": False, "error": f"HTTP {response.status_code}"}
                
                except Exception as e:
                    if attempt < self.max_retries:
                        print(f"[Upload18] Error: {str(e)[:50]}")
                        time.sleep(self.wait_seconds)
                        continue
                    return {"success": False, "error": str(e)}
            
            return {"success": False, "error": f"Failed after {self.max_retries} attempts"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
