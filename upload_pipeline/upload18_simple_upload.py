import requests
import os
from pathlib import Path
import time
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Upload18SimpleUploader:
    """
    Upload18 uploader based on official API v2 documentation
    Handles queue retries for "Error on uploaded file" and "Please wait" messages
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://upload18.com/api"
        self.max_retries = 30
        self.wait_seconds = 20
    
    def upload(self, video_path, title=None):
        """Upload video to Upload18 with queue handling"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            file_size = os.path.getsize(video_path)
            size_mb = file_size / (1024 * 1024)
            
            print(f"[Upload18] Starting upload: {file_name} ({size_mb:.1f} MB)")
            print(f"[Upload18] Max retries: {self.max_retries}, Wait time: {self.wait_seconds}s")
            
            # Upload with retry logic for queue handling
            attempt = 0
            while attempt < self.max_retries:
                attempt += 1
                
                try:
                    print(f"\n[Upload18] Upload attempt {attempt}/{self.max_retries}...")
                    
                    with open(video_path, 'rb') as f:
                        files = {'video': (file_name, f, 'video/mp4')}
                        data = {
                            'apikey': self.api_key,
                            'cid': '15',  # Videos category (default)
                            'fid': '18'   # Direct upload server (fid 18)
                        }
                        
                        start_time = time.time()
                        response = requests.post(
                            f"{self.base_url}/upload",
                            files=files,
                            data=data,
                            verify=False,
                            timeout=1800
                        )
                        elapsed = time.time() - start_time
                    
                    if response.status_code == 200:
                        result = response.json()
                        status = result.get('status', '')
                        msg = result.get('msg', '')
                        msg_lower = msg.lower()
                        
                        print(f"[Upload18] Response ({elapsed:.1f}s): status={status}, msg={msg}")
                        
                        if status == 'success':
                            vid = result.get('vid', '')
                            did = result.get('did', '')
                            print(f"[Upload18] ✓ Upload successful: vid={vid}, did={did}")
                            
                            return {
                                "success": True,
                                "host": "upload18",
                                "vid": vid,
                                "did": did,
                                "url": f"https://upload18.com/{vid}",
                                "embed_url": f"https://upload18.com/embed-{vid}.html",
                                "file_code": vid
                            }
                        
                        # Check for queue/processing messages that require retry
                        # Based on official API docs queue examples
                        retry_keywords = [
                            'wait',
                            'processing',
                            'upload request',
                            'error on uploaded file',
                            'please wait before starting another'
                        ]
                        
                        should_retry = any(keyword in msg_lower for keyword in retry_keywords)
                        
                        if should_retry:
                            print(f"[Upload18] ⏳ Queue busy or processing: {msg}")
                            print(f"[Upload18] Waiting {self.wait_seconds}s before retry...")
                            time.sleep(self.wait_seconds)
                            continue
                        
                        # Other error - don't retry
                        print(f"[Upload18] ✗ Upload failed: {msg}")
                        return {"success": False, "error": msg}
                    else:
                        print(f"[Upload18] HTTP {response.status_code}: {response.text[:200]}")
                        if attempt < self.max_retries:
                            print(f"[Upload18] Waiting {self.wait_seconds}s before retry...")
                            time.sleep(self.wait_seconds)
                            continue
                        return {"success": False, "error": f"HTTP {response.status_code}"}
                
                except requests.exceptions.Timeout:
                    print(f"[Upload18] Upload timeout")
                    if attempt < self.max_retries:
                        print(f"[Upload18] Waiting {self.wait_seconds}s before retry...")
                        time.sleep(self.wait_seconds)
                        continue
                    return {"success": False, "error": "Upload timeout"}
                
                except Exception as e:
                    print(f"[Upload18] Exception: {str(e)}")
                    if attempt < self.max_retries:
                        print(f"[Upload18] Waiting {self.wait_seconds}s before retry...")
                        time.sleep(self.wait_seconds)
                        continue
                    return {"success": False, "error": str(e)}
            
            # Max retries reached
            return {"success": False, "error": f"Upload failed after {self.max_retries} attempts (queue busy)"}
                
        except Exception as e:
            print(f"[Upload18] Error: {str(e)}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if len(sys.argv) < 2:
        print("Usage: python upload18_simple_upload.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    api_key = os.getenv("UPLOAD18_API_KEY")
    
    if not api_key:
        print("Error: UPLOAD18_API_KEY not found in .env")
        sys.exit(1)
    
    uploader = Upload18SimpleUploader(api_key)
    result = uploader.upload(video_path)
    
    print(f"\nResult: {result}")
