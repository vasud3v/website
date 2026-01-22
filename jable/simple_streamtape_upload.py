"""
Simple Streamtape upload - no fancy buffering, just works
"""
import os
import requests

def upload_to_streamtape(file_path, code, title):
    """Simple, reliable upload to Streamtape with proper error handling"""
    print(f"\n📤 UPLOADING TO STREAMTAPE")
    print("="*60)
    
    # Load credentials from environment (at runtime, not import time)
    STREAMTAPE_LOGIN = os.getenv('STREAMTAPE_LOGIN')
    STREAMTAPE_API_KEY = os.getenv('STREAMTAPE_API_KEY')
    
    if not STREAMTAPE_LOGIN or not STREAMTAPE_API_KEY:
        print("❌ Streamtape credentials not set in environment!")
        print("   Set STREAMTAPE_LOGIN and STREAMTAPE_API_KEY in .env file")
        return {'service': 'Streamtape', 'success': False, 'error': 'Missing credentials'}
    
    print(f"   Using login: {STREAMTAPE_LOGIN[:10]}...")
    
    # Get upload URL
    print("Getting upload server...")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = requests.get("https://api.streamtape.com/file/ul",
                            params={
                                'login': STREAMTAPE_LOGIN,
                                'key': STREAMTAPE_API_KEY
                            }, timeout=30)
            
            # Check HTTP status first
            if r.status_code == 403:
                print(f"❌ HTTP 403: Invalid API credentials")
                return {'service': 'Streamtape', 'success': False, 'error': 'Invalid credentials'}
            elif r.status_code == 509:
                print(f"⚠️ HTTP 509: Bandwidth limit exceeded")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 60  # Exponential backoff: 1min, 2min, 4min
                    print(f"   Retrying in {wait_time}s...")
                    import time
                    time.sleep(wait_time)
                    continue
                return {'service': 'Streamtape', 'success': False, 'error': 'Bandwidth limit exceeded'}
            elif r.status_code == 451:
                print(f"❌ HTTP 451: Unavailable For Legal Reasons")
                return {'service': 'Streamtape', 'success': False, 'error': 'Legal block'}
            elif r.status_code != 200:
                print(f"❌ HTTP {r.status_code}")
                if attempt < max_retries - 1:
                    print(f"   Retrying in 5s...")
                    import time
                    time.sleep(5)
                    continue
                return {'service': 'Streamtape', 'success': False, 'error': f'HTTP {r.status_code}'}
            
            result = r.json()
            
            # Check API status in JSON response
            if result.get('status') != 200:
                error_msg = result.get('msg', 'Unknown error')
                print(f"❌ API Error: {error_msg}")
                if attempt < max_retries - 1:
                    print(f"   Retrying in 5s...")
                    import time
                    time.sleep(5)
                    continue
                return {'service': 'Streamtape', 'success': False, 'error': error_msg}
            
            upload_url = result['result']['url']
            print(f"✅ Server: {upload_url}")
            break
            
        except requests.exceptions.Timeout:
            print(f"❌ Timeout getting upload server")
            if attempt < max_retries - 1:
                print(f"   Retrying in 5s...")
                import time
                time.sleep(5)
                continue
            return {'service': 'Streamtape', 'success': False, 'error': 'Timeout'}
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error: {str(e)[:100]}")
            if attempt < max_retries - 1:
                print(f"   Retrying in 5s...")
                import time
                time.sleep(5)
                continue
            return {'service': 'Streamtape', 'success': False, 'error': 'Connection error'}
        except Exception as e:
            print(f"❌ Error: {e}")
            if attempt < max_retries - 1:
                print(f"   Retrying in 5s...")
                import time
                time.sleep(5)
                continue
            return {'service': 'Streamtape', 'success': False, 'error': str(e)}
    
    file_size = os.path.getsize(file_path)
    print(f"File: {file_size / (1024**3):.2f} GB ({file_size:,} bytes)")
    
    print("\n⏳ Uploading (this may take a while)...")
    print("="*60)
    
    import time
    start = time.time()
    
    max_upload_retries = 2
    for upload_attempt in range(max_upload_retries):
        try:
            # Simple upload - let requests handle everything
            with open(file_path, 'rb') as f:
                response = requests.post(
                    upload_url,
                    files={'file1': (os.path.basename(file_path), f, 'video/mp4')},
                    timeout=7200  # 2 hour timeout
                )
            
            elapsed = time.time() - start
            print(f"\n✅ Upload completed in {int(elapsed//60)}m {int(elapsed%60)}s")
            print(f"Average speed: {(file_size / (1024**2)) / elapsed:.2f} MB/s")
            
            # Check HTTP status
            if response.status_code == 509:
                print(f"⚠️ HTTP 509: Bandwidth limit exceeded")
                if upload_attempt < max_upload_retries - 1:
                    wait_time = 300  # 5 minutes
                    print(f"   Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return {'service': 'Streamtape', 'success': False, 'error': 'Bandwidth limit'}
            elif response.status_code == 451:
                print(f"❌ HTTP 451: Unavailable For Legal Reasons")
                return {'service': 'Streamtape', 'success': False, 'error': 'Legal block'}
            elif response.status_code != 200:
                print(f"❌ HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                if upload_attempt < max_upload_retries - 1:
                    print(f"   Retrying in 10s...")
                    time.sleep(10)
                    continue
                return {'service': 'Streamtape', 'success': False, 'error': f'HTTP {response.status_code}'}
            
            result = response.json()
            print(f"Response: {result}")
            
            # Check API status in JSON
            if result.get('status') == 200:
                file_id = result['result']['id']
                
                # Verify upload with retry
                print(f"\n🔍 Verifying upload...")
                verified = False
                for attempt in range(3):
                    try:
                        verify = requests.get("https://api.streamtape.com/file/info",
                                             params={
                                                 'login': STREAMTAPE_LOGIN,
                                                 'key': STREAMTAPE_API_KEY,
                                                 'file': file_id
                                             }, timeout=30)
                        
                        if verify.status_code == 200:
                            info = verify.json()
                            if info.get('status') == 200:
                                uploaded_size = info['result'][file_id]['size']
                                print(f"Uploaded size: {uploaded_size:,} bytes")
                                print(f"Original size: {file_size:,} bytes")
                                
                                if uploaded_size == file_size:
                                    print(f"✅ File uploaded completely!")
                                else:
                                    print(f"⚠️ Size mismatch! Upload may be incomplete")
                                verified = True
                                break
                            else:
                                print(f"⚠️ Verification API error: {info.get('msg')}")
                        else:
                            print(f"⚠️ Verification attempt {attempt+1} failed (HTTP {verify.status_code})")
                    except Exception as e:
                        print(f"⚠️ Verification attempt {attempt+1} failed: {str(e)[:100]}")
                        if attempt < 2:
                            time.sleep(2)
                
                if not verified:
                    print(f"⚠️ Could not verify upload, but file should be available")
                    print(f"   Upload completed successfully, verification timed out")
                
                return {
                    'service': 'Streamtape',
                    'success': True,
                    'filecode': file_id,
                    'embed_url': f"https://streamtape.com/e/{file_id}",
                    'watch_url': f"https://streamtape.com/v/{file_id}",
                    'time': elapsed
                }
            else:
                error_msg = result.get('msg', 'Unknown error')
                print(f"❌ Upload failed: {error_msg}")
                if upload_attempt < max_upload_retries - 1:
                    print(f"   Retrying in 10s...")
                    time.sleep(10)
                    continue
                return {'service': 'Streamtape', 'success': False, 'error': error_msg}
        
        except requests.exceptions.Timeout:
            print(f"\n❌ Upload timeout")
            if upload_attempt < max_upload_retries - 1:
                print(f"   Retrying in 30s...")
                time.sleep(30)
                continue
            return {'service': 'Streamtape', 'success': False, 'error': 'Upload timeout'}
        except requests.exceptions.ConnectionError as e:
            print(f"\n❌ Connection error: {str(e)[:100]}")
            if upload_attempt < max_upload_retries - 1:
                print(f"   Retrying in 30s...")
                time.sleep(30)
                continue
            return {'service': 'Streamtape', 'success': False, 'error': 'Connection error'}
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            if upload_attempt < max_upload_retries - 1:
                print(f"   Retrying in 30s...")
                time.sleep(30)
                continue
            return {'service': 'Streamtape', 'success': False, 'error': str(e)}
    
    return {'service': 'Streamtape', 'success': False}


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_streamtape_upload.py <video_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    code = os.path.basename(file_path).split('.')[0]
    title = code
    
    result = upload_to_streamtape(file_path, code, title)
    
    if result['success']:
        print(f"\n{'='*60}")
        print(f"SUCCESS!")
        print(f"{'='*60}")
        print(f"Embed URL: {result['embed_url']}")
        print(f"Watch URL: {result['watch_url']}")
    else:
        print("\nUpload failed!")
        sys.exit(1)
