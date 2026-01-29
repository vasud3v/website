"""
Fixed Upload18 Uploader
Improved error handling, validation, and status checking
"""
import requests
import os
from pathlib import Path
import time
import urllib3
from tqdm import tqdm
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Upload18UploaderFixed:
    def __init__(self, email, username, password, api_key):
        self.email = email
        self.username = username
        self.password = password
        self.api_key = api_key
        self.base_url = "https://upload18.com/api"
        
        # Create session for connection reuse
        self.session = requests.Session()
        self.session.verify = False
        
        # Browser-like headers to bypass WAF
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://upload18.com/',
            'Origin': 'https://upload18.com'
        })
        
        # Optimize connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def check_video_status(self, did):
        """Check video processing status by DID"""
        try:
            response = self.session.get(
                f"{self.base_url}/myvideo",
                params={'apikey': self.api_key, 'per_page': 50},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    videos = data.get('data', [])
                    
                    for video in videos:
                        if str(video.get('did')) == str(did):
                            return {
                                'found': True,
                                'vid': video.get('vid'),
                                'did': video.get('did'),
                                'status': video.get('zt', 0),  # 0=pending, 1=transcoding, 2=done
                                'title': video.get('title', ''),
                                'duration': video.get('duration', 0)
                            }
            
            return {'found': False}
            
        except Exception as e:
            print(f"[Upload18] Status check error: {str(e)}")
            return {'found': False, 'error': str(e)}
    
    def wait_for_processing(self, did, max_wait_minutes=10):
        """Wait for video to finish processing"""
        max_attempts = max_wait_minutes * 3  # Check every 20 seconds
        attempt = 0
        
        print(f"[Upload18] Waiting for video processing (max {max_wait_minutes} minutes)...")
        
        while attempt < max_attempts:
            attempt += 1
            time.sleep(20)
            
            status = self.check_video_status(did)
            
            if status.get('found'):
                vid = status.get('vid')
                processing_status = status.get('status', 0)
                status_text = {0: 'Pending', 1: 'Transcoding', 2: 'Done'}.get(processing_status, 'Unknown')
                
                print(f"[Upload18] Status check {attempt}/{max_attempts}: {status_text}")
                
                if vid and vid != '':
                    print(f"[Upload18] ✓ VID available: {vid}")
                    return vid
            else:
                print(f"[Upload18] Status check {attempt}/{max_attempts}: Video not found yet")
        
        print(f"[Upload18] ⚠ Timeout waiting for VID after {max_wait_minutes} minutes")
        return None
    
    def upload(self, video_path, title=None):
        """Upload video to Upload18 with improved error handling"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            file_size = os.path.getsize(video_path)
            size_mb = file_size / (1024 * 1024)
            
            print(f"[Upload18] Starting upload: {file_name}")
            print(f"[Upload18] File size: {size_mb:.2f} MB")
            
            # Validate file size (Upload18 typically has limits)
            if size_mb > 5000:  # 5GB limit
                return {"success": False, "error": f"File too large: {size_mb:.2f} MB (max 5000 MB)"}
            
            # Upload endpoint
            upload_url = f"{self.base_url}/upload"
            print(f"[Upload18] Uploading to: {upload_url}")
            
            with open(video_path, 'rb') as f:
                # Progress bar
                with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, 
                         desc=f"📤 {file_name}", leave=False) as pbar:
                    
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
                        'cid': '15',  # Category ID
                        'mycid': '0',
                        'fid': '18'  # Folder ID
                    }
                    
                    start_time = time.time()
                    
                    try:
                        response = self.session.post(
                            upload_url,
                            files=files,
                            data=data,
                            timeout=3600  # 1 hour timeout
                        )
                    except requests.exceptions.Timeout:
                        return {"success": False, "error": "Upload timeout (1 hour)"}
                    except Exception as e:
                        return {"success": False, "error": f"Upload failed: {str(e)}"}
                    
                    elapsed = time.time() - start_time
                    speed_mbps = (file_size / (1024*1024)) / elapsed if elapsed > 0 else 0
                    
                    print(f"\n[Upload18] Upload completed in {elapsed:.1f}s (avg {speed_mbps:.2f} MB/s)")
                    print(f"[Upload18] Response status: {response.status_code}")
                    
                    if response.status_code != 200:
                        return {"success": False, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
                    
                    try:
                        result = response.json()
                    except json.JSONDecodeError:
                        return {"success": False, "error": f"Invalid JSON response: {response.text[:200]}"}
                    
                    print(f"[Upload18] Response: {result}")
                    
                    if result.get('status') != 'success':
                        error_msg = result.get('msg', result.get('error', 'Upload failed'))
                        return {"success": False, "error": error_msg}
                    
                    vid = result.get('vid', '')
                    did = result.get('did', '')
                    
                    if not did:
                        return {"success": False, "error": "No DID returned from server"}
                    
                    # If VID is empty, wait for processing
                    if not vid or vid == '':
                        print(f"[Upload18] ✓ Upload successful: did={did}")
                        print(f"[Upload18] ⏳ Video is processing...")
                        
                        vid = self.wait_for_processing(did, max_wait_minutes=10)
                        
                        if not vid:
                            print(f"[Upload18] ⚠ VID not available yet")
                            print(f"[Upload18] Video is still processing on server")
                            print(f"[Upload18] Check status later with: python upload18_check_status.py {did}")
                            
                            return {
                                "success": True,
                                "host": "upload18",
                                "vid": did,  # Use DID as placeholder
                                "did": did,
                                "processing": True,
                                "file_code": did,
                                "url": f"https://upload18.com/myvideo",
                                "embed_url": f"https://upload18.com/myvideo",
                                "note": "Video is processing. VID will be available soon."
                            }
                    
                    print(f"[Upload18] ✓ Upload successful: vid={vid}, did={did}")
                    
                    return {
                        "success": True,
                        "host": "upload18",
                        "vid": vid,
                        "did": did,
                        "file_code": vid,
                        "url": f"https://upload18.com/play/index/{vid}",
                        "embed_url": f"https://upload18.com/play/index/{vid}"
                    }
                    
        except Exception as e:
            print(f"[Upload18] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    email = os.getenv("UPLOAD18_EMAIL")
    username = os.getenv("UPLOAD18_USERNAME")
    password = os.getenv("UPLOAD18_PASSWORD")
    api_key = os.getenv("UPLOAD18_API_KEY")
    
    if not all([email, username, password, api_key]):
        print("Error: Upload18 credentials not found in .env file")
        print("Required: UPLOAD18_EMAIL, UPLOAD18_USERNAME, UPLOAD18_PASSWORD, UPLOAD18_API_KEY")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python upload18_uploader_fixed.py <video_file> [title]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    
    uploader = Upload18UploaderFixed(email, username, password, api_key)
    result = uploader.upload(video_path, title)
    
    if result['success']:
        print(f"\n✓ Upload successful!")
        print(f"  VID: {result['vid']}")
        print(f"  DID: {result['did']}")
        print(f"  URL: {result['url']}")
        print(f"  Embed URL: {result['embed_url']}")
        if result.get('processing'):
            print(f"  Note: {result['note']}")
    else:
        print(f"\n✗ Upload failed: {result['error']}")
