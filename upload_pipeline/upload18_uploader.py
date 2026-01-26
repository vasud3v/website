import requests
import os
from pathlib import Path
import time
import urllib3
from tqdm import tqdm

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Upload18Uploader:
    def __init__(self, email, username, password, api_key):
        self.email = email
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = "https://upload18.com/api"
        
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
        """Upload video to Upload18"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            
            print(f"[Upload18] Starting upload: {file_name}")
            
            # Direct upload to /api/upload
            upload_url = f"{self.base_url}/upload"
            print(f"[Upload18] Uploading to: {upload_url}")
            
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
                    
                    files = {'video': (file_name, progress_file, 'video/mp4')}
                    data = {
                        'apikey': self.api_key,
                        'cid': '15',  # Category ID (15 = default)
                        'mycid': '0',  # Optional custom category
                        'fid': '18'  # Folder ID (18 = direct upload)
                    }
                    
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
                    speed_mbps = (file_size / (1024*1024)) / elapsed if elapsed > 0 else 0
                    
                    print(f"\n[Upload18] Upload completed in {elapsed:.1f}s (avg {speed_mbps:.2f} MB/s)")
                    print(f"[Upload18] Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"[Upload18] Response: {result}")
                        
                        if result.get('status') == 'success':
                            vid = result.get('vid')
                            did = result.get('did')
                            
                            # If vid is empty, video is still processing - wait and poll
                            if not vid or vid == '':
                                print(f"[Upload18] ✓ Upload successful: did={did}")
                                print(f"[Upload18] ⏳ Video is processing. Waiting for VID...")
                                
                                # Poll for VID (max 5 minutes, check every 20 seconds)
                                max_attempts = 15  # 15 * 20s = 5 minutes
                                attempt = 0
                                
                                # Browser-like headers to bypass WAF
                                check_headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                    'Accept': 'application/json, text/plain, */*',
                                    'Accept-Language': 'en-US,en;q=0.9',
                                    'Referer': 'https://upload18.com/',
                                    'Origin': 'https://upload18.com'
                                }
                                
                                while attempt < max_attempts:
                                    attempt += 1
                                    time.sleep(20)  # Wait 20 seconds between checks
                                    print(f"[Upload18] Checking status (attempt {attempt}/{max_attempts})...")
                                    
                                    try:
                                        # Try to get video list with browser headers
                                        check_response = self.session.get(
                                            f"{self.base_url}/myvideo",
                                            params={'apikey': self.api_key, 'per_page': 20},
                                            headers=check_headers,
                                            timeout=30
                                        )
                                        
                                        if check_response.status_code == 200:
                                            check_data = check_response.json()
                                            if check_data.get('status') == 'success':
                                                videos = check_data.get('data', [])
                                                
                                                # Find our video by DID
                                                for video in videos:
                                                    if str(video.get('did')) == str(did):
                                                        found_vid = video.get('vid')
                                                        status = video.get('zt', 0)  # 0=pending, 1=transcoding, 2=done
                                                        
                                                        if found_vid and found_vid != '':
                                                            status_text = {0: 'Pending', 1: 'Transcoding', 2: 'Done'}.get(status, 'Unknown')
                                                            print(f"[Upload18] ✓ VID found: {found_vid} (Status: {status_text})")
                                                            return {
                                                                "success": True,
                                                                "host": "upload18",
                                                                "vid": found_vid,
                                                                "did": did,
                                                                "url": f"https://upload18.com/play/index/{found_vid}",
                                                                "embed_url": f"https://upload18.com/play/index/{found_vid}"
                                                            }
                                                        else:
                                                            print(f"[Upload18] Video found but VID still empty (processing...)")
                                                            break
                                    except Exception as e:
                                        print(f"[Upload18] ⚠ Check failed: {str(e)}")
                                
                                # If we couldn't get VID after polling, return with DID
                                print(f"[Upload18] ⚠ VID not available after {max_attempts} attempts.")
                                print(f"[Upload18] Video may need more processing time.")
                                print(f"[Upload18] Use: python upload18_update_vid.py {did} <vid>")
                                return {
                                    "success": True,
                                    "host": "upload18",
                                    "vid": did,
                                    "did": did,
                                    "processing": True,
                                    "url": f"https://upload18.com/myvideo",
                                    "embed_url": f"https://upload18.com/myvideo"
                                }
                            else:
                                print(f"[Upload18] ✓ Upload successful: vid={vid}, did={did}")
                                return {
                                    "success": True,
                                    "host": "upload18",
                                    "vid": vid,
                                    "did": did,
                                    "url": f"https://upload18.com/play/index/{vid}",
                                    "embed_url": f"https://upload18.com/play/index/{vid}"
                                }
                        else:
                            return {"success": False, "error": result.get('msg', 'Upload failed')}
                    else:
                        return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                    
        except Exception as e:
            print(f"[Upload18] Error: {str(e)}")
            return {"success": False, "error": str(e)}
