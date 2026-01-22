"""
Upload to Lulustream - typically faster than StreamWish
"""
import os
import sys
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, will use system environment variables

def create_optimized_session():
    """Create a session with optimized settings"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10,
        pool_block=False
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def upload_to_lulustream(file_path, code, title, folder_name=None):
    """
    Upload to Lulustream
    API Docs: https://lulustream.com/api
    
    Args:
        file_path: Path to video file
        code: Video code (e.g., PPPE-386)
        title: Video title
        folder_name: Optional folder name for organization (e.g., "PPPE", "2026-01", etc.)
    """
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    
    print(f"\n[UPLOAD] UPLOADING TO LULUSTREAM")
    print("="*60)
    
    # Load credentials from environment (at runtime, not import time)
    LULUSTREAM_API_KEY = os.getenv('LULUSTREAM_API_KEY')
    
    if not LULUSTREAM_API_KEY:
        print("❌ Lulustream API key not set in environment!")
        print("   Set LULUSTREAM_API_KEY in .env file")
        return {'service': 'Lulustream', 'success': False, 'error': 'Missing API key'}
    
    print(f"   Using API key: {LULUSTREAM_API_KEY[:10]}...")
    
    # Get upload server
    session = create_optimized_session()
    
    try:
        r = session.get("https://lulustream.com/api/upload/server",
                       params={'key': LULUSTREAM_API_KEY}, timeout=30)
        if r.status_code == 200:
            result = r.json()
            server = result.get('result', 'https://lulustream.com/upload')
            print(f"   Server: {server}")
        else:
            server = 'https://lulustream.com/upload'
            print(f"   Using default server")
    except Exception as e:
        print(f"   ⚠️ Using default server (API error: {e})")
        server = 'https://lulustream.com/upload'
    
    file_size = os.path.getsize(file_path)
    size_gb = file_size / (1024**3)
    print(f"   File: {size_gb:.2f} GB ({file_size:,} bytes)")
    
    start_time = time.time()
    
    try:
        from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
        
        print("\n⏳ Uploading to Lulustream...")
        print("="*60)
        
        # Larger buffer for faster upload
        BUFFER_SIZE = 1024 * 1024  # 1MB
        
        class BufferedReader:
            def __init__(self, file_path, buffer_size=BUFFER_SIZE):
                self.file = open(file_path, 'rb')
                self.buffer_size = buffer_size
                self.total_size = os.path.getsize(file_path)
                self.bytes_read = 0
            
            def read(self, size=-1):
                if size == -1:
                    size = self.buffer_size
                else:
                    size = min(size, self.buffer_size)
                
                data = self.file.read(size)
                self.bytes_read += len(data)
                return data
            
            def __len__(self):
                return self.total_size
            
            def close(self):
                self.file.close()
        
        buffered_file = BufferedReader(file_path)
        
        # Prepare upload fields
        # Note: LuluStream API uses 'key' parameter, not 'api_key'
        upload_fields = {
            'key': LULUSTREAM_API_KEY,
            'title': f"{code} - {title[:100]}",
            'file': (os.path.basename(file_path), buffered_file, 'video/mp4')
        }
        
        # Add folder if specified
        if folder_name:
            upload_fields['fld_id'] = folder_name
            print(f"   📁 Folder: {folder_name}")
        
        encoder = MultipartEncoder(fields=upload_fields)
        
        last_update = 0
        last_bytes = 0
        upload_complete = False
        
        def callback(monitor):
            nonlocal last_update, last_bytes, upload_complete
            
            current_time = time.time()
            
            # Check if upload is complete
            if monitor.bytes_read >= monitor.len and not upload_complete:
                upload_complete = True
                print(f"\r📊 [████████████████████████████████████████] 100.0% | Upload complete!{' '*30}")
                print("\n" + "="*60)
                print("   ⏳ Waiting for server response (processing/verification)...")
                print("   (This may take 30-60 seconds)")
                sys.stdout.flush()
                return
            
            # Update every 2 seconds instead of 0.5 for cleaner output
            if current_time - last_update >= 2.0:
                progress = (monitor.bytes_read / monitor.len) * 100
                elapsed = current_time - start_time
                
                # Instantaneous speed
                bytes_diff = monitor.bytes_read - last_bytes
                time_diff = current_time - last_update
                instant_speed = (bytes_diff / (1024*1024)) / time_diff if time_diff > 0 else 0
                
                # Average speed
                avg_speed = (monitor.bytes_read / (1024*1024)) / elapsed if elapsed > 0 else 0
                
                # ETA
                if avg_speed > 0:
                    remaining_bytes = monitor.len - monitor.bytes_read
                    eta_seconds = remaining_bytes / (avg_speed * 1024 * 1024)
                    eta_min = int(eta_seconds // 60)
                    eta_sec = int(eta_seconds % 60)
                    eta_str = f"ETA: {eta_min}m {eta_sec}s"
                else:
                    eta_str = "ETA: --"
                
                bar = '█' * int(40 * progress / 100) + '░' * (40 - int(40 * progress / 100))
                # Use sys.stdout.write for better control
                sys.stdout.write(f"\r📊 [{bar}] {progress:.1f}% | ↑{instant_speed:.1f} MB/s (avg: {avg_speed:.1f}) | {eta_str}" + " " * 10)
                sys.stdout.flush()
                
                last_update = current_time
                last_bytes = monitor.bytes_read
        
        monitor = MultipartEncoderMonitor(encoder, callback)
        
        # Upload with progress tracking
        print("\n⏳ Uploading to Lulustream...")
        print("="*60)
        sys.stdout.flush()
        
        # Use reasonable timeout for upload + server processing
        # Upload time + 5 minutes for server processing
        estimated_upload_time = file_size / (1024 * 1024 * 0.5)  # Assume 0.5 MB/s minimum
        timeout_seconds = max(300, int(estimated_upload_time + 300))  # At least 5 minutes
        
        print(f"   [DEBUG] Starting POST request (timeout: {timeout_seconds}s)...")
        sys.stdout.flush()
        
        response = session.post(
            server,
            data=monitor,
            headers={
                'Content-Type': monitor.content_type,
                'Connection': 'keep-alive'
            },
            timeout=timeout_seconds
        )
        
        print("   [DEBUG] POST request completed!")
        sys.stdout.flush()
        
        buffered_file.close()
        
        # If callback didn't print completion message, print it now
        if not upload_complete:
            print(f"\r📊 [████████████████████████████████████████] 100.0% | Upload complete!{' '*30}")
            print("\n" + "="*60)
            print("   ⏳ Waiting for server response...")
            sys.stdout.flush()
        
        total_time = time.time() - start_time
        avg_speed = (file_size / (1024**3)) / (total_time / 60) if total_time > 0 else 0
        
        print(f"   Upload time: {int(total_time//60)}m {int(total_time%60)}s")
        print(f"   Average speed: {avg_speed:.2f} GB/min ({avg_speed*1024/60:.1f} MB/s)")
        sys.stdout.flush()
        
    except ImportError:
        print("\n⏳ Uploading (basic mode)...")
        print("   Install requests-toolbelt for progress: pip install requests-toolbelt")
        
        data = {
            'key': LULUSTREAM_API_KEY,
            'title': f"{code} - {title[:100]}"
        }
        if folder_name:
            data['fld_id'] = folder_name
        
        # Calculate reasonable timeout
        estimated_upload_time = file_size / (1024 * 1024 * 0.5)  # Assume 0.5 MB/s minimum
        timeout_seconds = max(300, int(estimated_upload_time + 300))
        
        with open(file_path, 'rb') as f:
            response = session.post(
                server,
                files={'file': (os.path.basename(file_path), f, 'video/mp4')},
                data=data,
                timeout=timeout_seconds
            )
    
    except requests.exceptions.Timeout:
        print(f"\n❌ Upload timeout: Server took too long to respond")
        print(f"   The file may have been uploaded successfully but server didn't respond")
        print(f"   Check your Lulustream dashboard to verify")
        print(f"   Tip: For very large files, consider increasing timeout or using FTP upload")
        return {'service': 'Lulustream', 'success': False, 'error': 'Timeout waiting for server response'}
    
    except Exception as e:
        print(f"\n❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return {'service': 'Lulustream', 'success': False, 'error': str(e)}
    
    # Parse response
    print(f"\n[DEBUG] Response status: {response.status_code}")
    print(f"[DEBUG] Response length: {len(response.text)} bytes")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"[DEBUG] JSON response: {result}")
            
            # Lulustream response format - check multiple status formats
            status_ok = (
                result.get('status') == 'success' or 
                result.get('status') == 200 or
                result.get('msg') == 'OK'
            )
            
            if status_ok:
                file_code = result.get('file_code') or result.get('filecode') or result.get('result', {}).get('file_code')
                if file_code:
                    print(f"\n✅ Upload complete!")
                    print(f"   File code: {file_code}")
                    return {
                        'service': 'Lulustream',
                        'success': True,
                        'filecode': file_code,
                        'embed_url': f"https://lulustream.com/e/{file_code}",
                        'watch_url': f"https://lulustream.com/{file_code}",
                        'download_url': result.get('download_url', ''),
                        'time': total_time
                    }
                else:
                    print(f"\n⚠️ No file code in response, checking result field...")
                    # Sometimes the response is nested
                    if 'result' in result and isinstance(result['result'], dict):
                        file_code = result['result'].get('file_code') or result['result'].get('filecode')
                        if file_code:
                            print(f"\n✅ Upload complete!")
                            print(f"   File code: {file_code}")
                            return {
                                'service': 'Lulustream',
                                'success': True,
                                'filecode': file_code,
                                'embed_url': f"https://lulustream.com/e/{file_code}",
                                'watch_url': f"https://lulustream.com/{file_code}",
                                'download_url': result.get('download_url', ''),
                                'time': total_time
                            }
            else:
                print(f"\n❌ Upload failed: {result.get('message', result.get('msg', 'Unknown error'))}")
                print(f"   Full response: {result}")
        except Exception as e:
            print(f"\n⚠️ Response is not JSON, trying HTML parsing...")
            print(f"   Parse error: {e}")
            print(f"   Response preview: {response.text[:500]}")
            
            # Try HTML parsing as fallback
            import re
            file_code = None
            
            # Look for file_code in HTML
            code_match = re.search(r'file_code["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]+)', response.text)
            if code_match:
                file_code = code_match.group(1)
                print(f"\n✅ Upload complete (HTML response)!")
                print(f"   File code: {file_code}")
                return {
                    'service': 'Lulustream',
                    'success': True,
                    'filecode': file_code,
                    'embed_url': f"https://lulustream.com/e/{file_code}",
                    'watch_url': f"https://lulustream.com/{file_code}",
                    'time': total_time
                }
            else:
                print(f"\n❌ Could not extract file code from HTML")
    else:
        print(f"\n❌ Upload failed with status {response.status_code}")
        print(f"   Response: {response.text[:500]}")
    
    return {'service': 'Lulustream', 'success': False}


# Test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python lulustream_upload.py <video_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    code = os.path.basename(file_path).split('.')[0]
    title = code
    
    result = upload_to_lulustream(file_path, code, title)
    
    if result['success']:
        print(f"\n{'='*60}")
        print(f"SUCCESS!")
        print(f"{'='*60}")
        print(f"Embed URL: {result['embed_url']}")
        print(f"Watch URL: {result['watch_url']}")
        if result.get('download_url'):
            print(f"Download URL: {result['download_url']}")
    else:
        print("\nUpload failed!")
        sys.exit(1)
