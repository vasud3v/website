"""
Simple Streamtape upload - no fancy buffering, just works
"""
import os
import requests

def upload_to_streamtape(file_path, code, title):
    """Simple, reliable upload to Streamtape"""
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
    max_retries = 2
    for attempt in range(max_retries):
        try:
            r = requests.get("https://api.streamtape.com/file/ul",
                            params={
                                'login': STREAMTAPE_LOGIN,
                                'key': STREAMTAPE_API_KEY
                            }, timeout=30)
            result = r.json()
            
            if result.get('status') != 200:
                print(f"❌ Failed: {result.get('msg')}")
                if attempt < max_retries - 1:
                    print(f"   Retrying in 5s...")
                    import time
                    time.sleep(5)
                    continue
                return {'service': 'Streamtape', 'success': False, 'error': result.get('msg')}
            
            upload_url = result['result']['url']
            print(f"✅ Server: {upload_url}")
            break
            
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
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result}")
            
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
                            print(f"⚠️ Verification attempt {attempt+1} failed (HTTP {verify.status_code})")
                    except Exception as e:
                        print(f"⚠️ Verification attempt {attempt+1} failed: {str(e)[:100]}")
                        if attempt < 2:
                            import time
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
                print(f"❌ Upload failed: {result.get('msg')}")
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
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
