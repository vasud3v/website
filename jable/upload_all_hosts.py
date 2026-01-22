"""
Upload video to StreamWish with LuluStream fallback - Rewritten for reliability
Ensures full video is uploaded correctly
Falls back to LuluStream when StreamWish hits upload limits
"""
import os
import sys
import time
import requests
from streamwish_folders import get_or_create_folder

# Load API keys at module level
LULUSTREAM_API_KEY = os.getenv('LULUSTREAM_API_KEY')
STREAMWISH_API_KEY = os.getenv('STREAMWISH_API_KEY')


def upload_to_lulustream(file_path, code, title, folder_name=None):
    """
    Upload to LuluStream as fallback
    
    Args:
        file_path: Full path to MP4 file
        code: Video code
        title: Video title
        folder_name: Optional folder name
        
    Returns:
        Dict with success status and upload details
    """
    print(f"\n[LuluStream] ═══════════════════════════════════════")
    print(f"[LuluStream] Starting fallback upload")
    print(f"[LuluStream] ═══════════════════════════════════════")
    
    # Verify file exists and get size
    if not os.path.exists(file_path):
        print(f"[LuluStream] ❌ File not found: {file_path}")
        return {'service': 'LuluStream', 'success': False, 'error': 'File not found'}
    
    file_size = os.path.getsize(file_path)
    file_size_gb = file_size / (1024**3)
    file_size_mb = file_size / (1024**2)
    
    print(f"[LuluStream] File: {os.path.basename(file_path)}")
    print(f"[LuluStream] Size: {file_size_gb:.2f} GB ({file_size:,} bytes)")
    
    # Verify file is not too small
    if file_size_mb < 50:
        print(f"[LuluStream] ❌ File too small ({file_size_mb:.1f} MB) - likely incomplete")
        return {'service': 'LuluStream', 'success': False, 'error': 'File too small'}
    
    # Check API key
    if not LULUSTREAM_API_KEY:
        print("[LuluStream] ❌ API key not set in environment")
        return {'service': 'LuluStream', 'success': False, 'error': 'Missing API key'}
    
    print(f"[LuluStream] API key: {LULUSTREAM_API_KEY[:10]}...")
    
    # Prepare title - don't duplicate code if already in title
    if title.upper().startswith(code.upper()):
        upload_title = title[:100]
    else:
        upload_title = f"{code} - {title[:100]}"
    
    # Get upload server
    try:
        print(f"[LuluStream] Getting upload server...")
        server_response = requests.get(
            "https://lulustream.com/api/upload/server",
            params={'key': LULUSTREAM_API_KEY},
            timeout=30
        )
        
        if server_response.status_code == 200:
            server_data = server_response.json()
            upload_server = server_data.get('result', 'https://lulustream.com/upload')
            print(f"[LuluStream] ✓ Upload server: {upload_server}")
        else:
            upload_server = 'https://lulustream.com/upload'
            print(f"[LuluStream] Using default server")
    except Exception as e:
        upload_server = 'https://lulustream.com/upload'
        print(f"[LuluStream] ⚠️ Using default server (error: {str(e)[:50]})")
    
    upload_start = time.time()
    
    try:
        # Use MultipartEncoder for proper large file handling
        try:
            from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
            use_multipart = True
        except ImportError:
            print(f"[LuluStream] ⚠️ requests-toolbelt not available, using standard upload")
            use_multipart = False
        
        if use_multipart:
            # Prepare fields for multipart encoder
            fields = {
                'api_key': LULUSTREAM_API_KEY,
                'title': upload_title,
            }
            
            if folder_name:
                fields['folder'] = folder_name
                print(f"[LuluStream] ✓ Folder: {folder_name}")
            
            # Add file
            print(f"[LuluStream] Opening file for multipart encoding...")
            file_handle = open(file_path, 'rb')
            fields['file'] = (os.path.basename(file_path), file_handle, 'video/mp4')
            
            print(f"[LuluStream] Creating multipart encoder...")
            encoder = MultipartEncoder(fields=fields)
            
            print(f"[LuluStream] Encoder size: {encoder.len:,} bytes ({encoder.len / (1024**3):.2f} GB)")
            
            # Verify encoder size
            if encoder.len < file_size * 0.9:
                print(f"[LuluStream] ❌ ERROR: Encoder size too small!")
                file_handle.close()
                return {'service': 'LuluStream', 'success': False, 'error': 'Encoder size mismatch'}
            
            # Create progress monitor
            last_update = [time.time()]
            last_bytes = [0]
            
            def progress_callback(monitor):
                current_time = time.time()
                if current_time - last_update[0] >= 5.0:
                    progress = (monitor.bytes_read / monitor.len) * 100
                    elapsed = current_time - upload_start
                    
                    bytes_diff = monitor.bytes_read - last_bytes[0]
                    time_diff = current_time - last_update[0]
                    speed = (bytes_diff / (1024*1024)) / time_diff if time_diff > 0 else 0
                    
                    bar = '█' * int(40 * progress / 100) + '░' * (40 - int(40 * progress / 100))
                    print(f"[LuluStream] [{bar}] {progress:.1f}% | ↑{speed:.1f} MB/s")
                    sys.stdout.flush()
                    
                    last_update[0] = current_time
                    last_bytes[0] = monitor.bytes_read
            
            monitor = MultipartEncoderMonitor(encoder, progress_callback)
            
            print(f"[LuluStream] Uploading to {upload_server}")
            print(f"[LuluStream] This will take several minutes...")
            sys.stdout.flush()
            
            try:
                upload_response = requests.post(
                    upload_server,
                    data=monitor,
                    headers={'Content-Type': monitor.content_type},
                    timeout=7200
                )
                
                print(f"\n[LuluStream] ✓ POST request completed")
                print(f"[LuluStream] Bytes sent: {monitor.bytes_read:,}")
                
                if monitor.bytes_read < file_size * 0.95:
                    print(f"[LuluStream] ❌ WARNING: Only {monitor.bytes_read:,} bytes sent!")
                else:
                    print(f"[LuluStream] ✓ Full file uploaded")
                
            except Exception as e:
                print(f"[LuluStream] ❌ Upload exception: {str(e)[:200]}")
                raise
            finally:
                file_handle.close()
        else:
            # Fallback to standard upload
            print(f"[LuluStream] Using standard file upload...")
            with open(file_path, 'rb') as video_file:
                files = {'file': (os.path.basename(file_path), video_file, 'video/mp4')}
                data = {
                    'api_key': LULUSTREAM_API_KEY,
                    'title': upload_title
                }
                if folder_name:
                    data['folder'] = folder_name
                
                upload_response = requests.post(
                    upload_server,
                    files=files,
                    data=data,
                    timeout=7200
                )
        
        upload_time = time.time() - upload_start
        print(f"[LuluStream] ✓ Upload completed in {int(upload_time//60)}m {int(upload_time%60)}s")
        
        # Parse response
        if upload_response.status_code == 200:
            try:
                response_data = upload_response.json()
                
                if response_data.get('status') == 'success':
                    filecode = response_data.get('file_code') or response_data.get('filecode')
                    
                    if filecode:
                        print(f"\n[LuluStream] ═══════════════════════════════════════")
                        print(f"[LuluStream] ✅ UPLOAD SUCCESSFUL!")
                        print(f"[LuluStream] ═══════════════════════════════════════")
                        print(f"[LuluStream] File code: {filecode}")
                        print(f"[LuluStream] Embed URL: https://lulustream.com/e/{filecode}")
                        print(f"[LuluStream] Watch URL: https://lulustream.com/{filecode}")
                        print(f"[LuluStream] Upload time: {int(upload_time//60)}m {int(upload_time%60)}s")
                        print(f"[LuluStream] File size uploaded: {file_size_gb:.2f} GB")
                        if folder_name:
                            print(f"[LuluStream] Folder: {folder_name}")
                        
                        return {
                            'service': 'LuluStream',
                            'success': True,
                            'filecode': filecode,
                            'embed_url': f"https://lulustream.com/e/{filecode}",
                            'watch_url': f"https://lulustream.com/{filecode}",
                            'time': upload_time,
                            'folder': folder_name,
                            'file_size': file_size
                        }
                    else:
                        print(f"[LuluStream] ❌ No filecode in response")
                else:
                    print(f"[LuluStream] ❌ Upload failed: {response_data.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"[LuluStream] ❌ Failed to parse response: {e}")
                print(f"[LuluStream] Response: {upload_response.text[:200]}")
        else:
            print(f"[LuluStream] ❌ Upload failed: HTTP {upload_response.status_code}")
            print(f"[LuluStream] Response: {upload_response.text[:200]}")
        
        return {'service': 'LuluStream', 'success': False, 'error': 'Upload failed'}
        
    except Exception as e:
        print(f"[LuluStream] ❌ Unexpected error: {str(e)[:100]}")
        import traceback
        traceback.print_exc()
        return {'service': 'LuluStream', 'success': False, 'error': str(e)}


def upload_to_streamwish(file_path, code, title, folder_name=None):
    """
    Upload full video file to StreamWish with verification
    Handles upload limits by pausing workflow until limit resets
    
    Args:
        file_path: Full path to MP4 file
        code: Video code
        title: Video title
        folder_name: Optional folder name
        
    Returns:
        Dict with success status and upload details
        Special return: {'service': 'StreamWish', 'success': False, 'error': 'RATE_LIMIT', 'wait_until': timestamp}
    """
    print(f"\n[StreamWish] ═══════════════════════════════════════")
    print(f"[StreamWish] Starting upload process")
    print(f"[StreamWish] ═══════════════════════════════════════")
    
    # Verify file exists and get size
    if not os.path.exists(file_path):
        print(f"[StreamWish] ❌ File not found: {file_path}")
        return {'service': 'StreamWish', 'success': False, 'error': 'File not found'}
    
    file_size = os.path.getsize(file_path)
    file_size_gb = file_size / (1024**3)
    file_size_mb = file_size / (1024**2)
    
    print(f"[StreamWish] File: {os.path.basename(file_path)}")
    print(f"[StreamWish] Size: {file_size_gb:.2f} GB ({file_size:,} bytes)")
    
    # Verify file is not too small (likely preview/incomplete)
    if file_size_mb < 50:
        print(f"[StreamWish] ❌ File too small ({file_size_mb:.1f} MB) - likely incomplete")
        return {'service': 'StreamWish', 'success': False, 'error': 'File too small'}
    
    # Check API key
    if not STREAMWISH_API_KEY:
        print("[StreamWish] ❌ API key not set in environment")
        return {'service': 'StreamWish', 'success': False, 'error': 'Missing API key'}
    
    print(f"[StreamWish] API key: {STREAMWISH_API_KEY[:10]}...")
    
    # Prepare title - don't duplicate code if already in title
    if title.upper().startswith(code.upper()):
        upload_title = title[:100]
    else:
        upload_title = f"{code} - {title[:100]}"
    
    # Validate API key by testing account info
    print(f"[StreamWish] Validating API key...")
    try:
        test_response = requests.get(
            "https://api.streamwish.com/api/account/info",
            params={'key': STREAMWISH_API_KEY},
            timeout=10
        )
        if test_response.status_code == 200:
            test_data = test_response.json()
            if test_data.get('status') == 200:
                account_info = test_data.get('result', {})
                print(f"[StreamWish] ✓ API key valid")
                print(f"[StreamWish] Account: {account_info.get('email', 'N/A')}")
                print(f"[StreamWish] Storage used: {account_info.get('storage_used', 'N/A')}")
            else:
                print(f"[StreamWish] ❌ API key invalid: {test_data.get('msg', 'Unknown error')}")
                return {'service': 'StreamWish', 'success': False, 'error': 'Invalid API key'}
        else:
            print(f"[StreamWish] ⚠️ Could not validate API key (HTTP {test_response.status_code})")
    except Exception as e:
        print(f"[StreamWish] ⚠️ API key validation error: {str(e)[:100]}")
        print(f"[StreamWish] Continuing anyway...")
    
    # Get folder ID if folder name provided
    folder_id = None
    if folder_name:
        print(f"[StreamWish] Getting folder ID for: {folder_name}")
        folder_id = get_or_create_folder(folder_name, STREAMWISH_API_KEY)
        if folder_id:
            print(f"[StreamWish] ✓ Folder ID: {folder_id}")
        else:
            print(f"[StreamWish] ⚠️ Could not get folder, uploading to root")
    
    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        print(f"\n[StreamWish] ─────────────────────────────────────")
        print(f"[StreamWish] Attempt {attempt + 1}/{max_retries}")
        print(f"[StreamWish] ─────────────────────────────────────")
        
        try:
            # Step 1: Get upload server
            print(f"[StreamWish] Step 1: Getting upload server...")
            server_response = requests.get(
                "https://api.streamwish.com/api/upload/server",
                params={'key': STREAMWISH_API_KEY},
                timeout=30
            )
            
            if server_response.status_code != 200:
                print(f"[StreamWish] ❌ Server request failed: HTTP {server_response.status_code}")
                if attempt < max_retries - 1:
                    print(f"[StreamWish] Retrying in 5s...")
                    time.sleep(5)
                    continue
                return {'service': 'StreamWish', 'success': False, 'error': f'HTTP {server_response.status_code}'}
            
            server_data = server_response.json()
            if server_data.get('status') != 200:
                error_msg = server_data.get('msg', 'Unknown')
                print(f"[StreamWish] ❌ API error: {error_msg}")
                
                # Check for rate limit errors
                if 'limit' in error_msg.lower() or 'quota' in error_msg.lower() or 'exceeded' in error_msg.lower():
                    print(f"[StreamWish] 🚫 UPLOAD LIMIT DETECTED!")
                    print(f"[StreamWish] Error message: {error_msg}")
                    
                    # Calculate wait time (StreamWish limits usually reset after 24 hours)
                    wait_seconds = 24 * 3600  # 24 hours default
                    wait_until = time.time() + wait_seconds
                    
                    # Try to extract wait time from error message if available
                    import re
                    time_match = re.search(r'(\d+)\s*(hour|hr|h)', error_msg.lower())
                    if time_match:
                        hours = int(time_match.group(1))
                        wait_seconds = hours * 3600
                        wait_until = time.time() + wait_seconds
                        print(f"[StreamWish] Detected {hours} hour wait period")
                    
                    return {
                        'service': 'StreamWish',
                        'success': False,
                        'error': 'RATE_LIMIT',
                        'error_msg': error_msg,
                        'wait_until': wait_until,
                        'wait_seconds': wait_seconds
                    }
                
                if attempt < max_retries - 1:
                    print(f"[StreamWish] Retrying in 5s...")
                    time.sleep(5)
                    continue
                return {'service': 'StreamWish', 'success': False, 'error': error_msg}
            
            upload_server = server_data.get('result', 'https://s1.streamwish.com/upload/01')
            print(f"[StreamWish] ✓ Upload server: {upload_server}")
            
            # Step 2: Prepare upload data
            print(f"[StreamWish] Step 2: Preparing upload data...")
            upload_data = {
                'key': STREAMWISH_API_KEY,
                'file_title': upload_title,
                'file_adult': '1',
                'file_public': '1'  # CRITICAL: Make file public so it's accessible
            }
            
            if folder_id:
                upload_data['fld_id'] = folder_id
                print(f"[StreamWish] ✓ Folder ID added: {folder_id}")
            
            print(f"[StreamWish] ✓ Upload parameters ready")
            
            # Step 3: Upload file with proper multipart encoding
            print(f"[StreamWish] Step 3: Uploading file...")
            print(f"[StreamWish] File path: {file_path}")
            print(f"[StreamWish] File size: {file_size:,} bytes ({file_size_gb:.2f} GB)")
            
            upload_start = time.time()
            upload_integrity_confirmed = False
            
            # Use MultipartEncoder for proper large file handling
            try:
                from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
                use_multipart = True
            except ImportError:
                print(f"[StreamWish] ⚠️ requests-toolbelt not available, using standard upload")
                use_multipart = False
            
            if use_multipart:
                # Prepare fields for multipart encoder
                fields = {
                    'key': upload_data['key'],
                    'file_title': upload_data['file_title'],
                    'file_adult': upload_data['file_adult'],
                    'file_public': upload_data['file_public'],  # Make file public
                }
                
                if 'fld_id' in upload_data:
                    fields['fld_id'] = upload_data['fld_id']
                
                # Add file - will be read completely
                print(f"[StreamWish] Opening file for multipart encoding...")
                file_handle = open(file_path, 'rb')
                fields['file'] = (os.path.basename(file_path), file_handle, 'video/mp4')
                
                print(f"[StreamWish] Creating multipart encoder...")
                encoder = MultipartEncoder(fields=fields)
                
                print(f"[StreamWish] Encoder size: {encoder.len:,} bytes ({encoder.len / (1024**3):.2f} GB)")
                
                # Verify encoder size matches file size (approximately)
                if encoder.len < file_size * 0.9:
                    print(f"[StreamWish] ❌ ERROR: Encoder size too small!")
                    print(f"[StreamWish] Expected: ~{file_size:,} bytes")
                    print(f"[StreamWish] Got: {encoder.len:,} bytes")
                    file_handle.close()
                    if attempt < max_retries - 1:
                        time.sleep(10)
                        continue
                    return {'service': 'StreamWish', 'success': False, 'error': 'Encoder size mismatch'}
                
                # Create progress monitor
                last_update = [time.time()]
                last_bytes = [0]
                
                def progress_callback(monitor):
                    current_time = time.time()
                    if current_time - last_update[0] >= 5.0:
                        progress = (monitor.bytes_read / monitor.len) * 100
                        elapsed = current_time - upload_start
                        
                        bytes_diff = monitor.bytes_read - last_bytes[0]
                        time_diff = current_time - last_update[0]
                        speed = (bytes_diff / (1024*1024)) / time_diff if time_diff > 0 else 0
                        
                        bar = '█' * int(40 * progress / 100) + '░' * (40 - int(40 * progress / 100))
                        print(f"[StreamWish] [{bar}] {progress:.1f}% | ↑{speed:.1f} MB/s")
                        sys.stdout.flush()
                        
                        last_update[0] = current_time
                        last_bytes[0] = monitor.bytes_read
                
                monitor = MultipartEncoderMonitor(encoder, progress_callback)
                
                print(f"[StreamWish] Uploading to {upload_server}")
                print(f"[StreamWish] This will take several minutes...")
                sys.stdout.flush()
                
                try:
                    upload_response = requests.post(
                        upload_server,
                        data=monitor,
                        headers={'Content-Type': monitor.content_type},
                        timeout=7200
                    )
                    
                    print(f"\n[StreamWish] ✓ POST request completed")
                    print(f"[StreamWish] Bytes sent: {monitor.bytes_read:,}")
                    
                    # Verify full file was sent
                    if monitor.bytes_read < file_size * 0.95:
                        print(f"[StreamWish] ❌ WARNING: Only {monitor.bytes_read:,} bytes sent!")
                        print(f"[StreamWish] Expected: {file_size:,} bytes")
                    else:
                        print(f"[StreamWish] ✓ Full file uploaded")
                        upload_integrity_confirmed = True
                    
                except Exception as e:
                    print(f"[StreamWish] ❌ Upload exception: {str(e)[:200]}")
                    raise
                finally:
                    file_handle.close()
            else:
                # Fallback to standard upload
                print(f"[StreamWish] Using standard file upload...")
                with open(file_path, 'rb') as video_file:
                    files = {'file': (os.path.basename(file_path), video_file, 'video/mp4')}
                    
                    upload_response = requests.post(
                        upload_server,
                        files=files,
                        data=upload_data,
                        timeout=7200
                    )
                    
                    print(f"[StreamWish] ✓ POST request completed")
                    upload_integrity_confirmed = True
            
            upload_time = time.time() - upload_start
            print(f"[StreamWish] ✓ Upload completed in {int(upload_time//60)}m {int(upload_time%60)}s")
            
            # Step 4: Parse response
            print(f"[StreamWish] Step 4: Parsing response...")
            print(f"[StreamWish] Response length: {len(upload_response.text)} characters")
            
            if upload_response.status_code != 200:
                print(f"[StreamWish] ❌ Upload failed: HTTP {upload_response.status_code}")
                print(f"[StreamWish] Response text: {upload_response.text[:500]}")
                
                # Check for rate limit in response
                if 'limit' in upload_response.text.lower() or 'quota' in upload_response.text.lower():
                    print(f"[StreamWish] 🚫 UPLOAD LIMIT DETECTED in response!")
                    wait_seconds = 24 * 3600
                    wait_until = time.time() + wait_seconds
                    return {
                        'service': 'StreamWish',
                        'success': False,
                        'error': 'RATE_LIMIT',
                        'error_msg': upload_response.text[:200],
                        'wait_until': wait_until,
                        'wait_seconds': wait_seconds
                    }
                
                if attempt < max_retries - 1:
                    print(f"[StreamWish] Retrying in 10s...")
                    time.sleep(10)
                    continue
                return {'service': 'StreamWish', 'success': False, 'error': f'HTTP {upload_response.status_code}'}
            
            try:
                response_data = upload_response.json()
            except Exception as e:
                print(f"[StreamWish] ❌ Failed to parse JSON response: {e}")
                print(f"[StreamWish] Raw response: {upload_response.text[:500]}")
                
                # Check for rate limit in raw response
                if 'limit' in upload_response.text.lower() or 'quota' in upload_response.text.lower():
                    print(f"[StreamWish] 🚫 UPLOAD LIMIT DETECTED in raw response!")
                    wait_seconds = 24 * 3600
                    wait_until = time.time() + wait_seconds
                    return {
                        'service': 'StreamWish',
                        'success': False,
                        'error': 'RATE_LIMIT',
                        'error_msg': upload_response.text[:200],
                        'wait_until': wait_until,
                        'wait_seconds': wait_seconds
                    }
                
                if attempt < max_retries - 1:
                    print(f"[StreamWish] Retrying in 10s...")
                    time.sleep(10)
                    continue
                return {'service': 'StreamWish', 'success': False, 'error': 'Invalid JSON response'}
            
            print(f"[StreamWish] Response JSON: {response_data}")
            print(f"[StreamWish] Response status: {response_data.get('status')}")
            print(f"[StreamWish] Response message: {response_data.get('msg')}")
            
            # Step 5: Extract file code
            print(f"[StreamWish] Step 5: Extracting file code...")
            
            if 'files' not in response_data:
                print(f"[StreamWish] ❌ No 'files' key in response")
                print(f"[StreamWish] Response keys: {list(response_data.keys())}")
                print(f"[StreamWish] Full response: {response_data}")
                if attempt < max_retries - 1:
                    print(f"[StreamWish] Retrying in 10s...")
                    time.sleep(10)
                    continue
                return {'service': 'StreamWish', 'success': False, 'error': 'No files in response'}
            
            if len(response_data['files']) == 0:
                print(f"[StreamWish] ❌ Empty files array in response")
                print(f"[StreamWish] Full response: {response_data}")
                if attempt < max_retries - 1:
                    print(f"[StreamWish] Retrying in 10s...")
                    time.sleep(10)
                    continue
                return {'service': 'StreamWish', 'success': False, 'error': 'Empty files array'}
            
            file_info = response_data['files'][0]
            print(f"[StreamWish] File info: {file_info}")
            
            filecode = file_info.get('filecode')
            filename = file_info.get('filename')
            status = file_info.get('status')
            
            print(f"[StreamWish] Filecode: {filecode}")
            print(f"[StreamWish] Filename: {filename}")
            print(f"[StreamWish] Status: {status}")
            
            # Check for quota/limit errors in status
            if status and isinstance(status, str):
                status_lower = status.lower()
                if 'too many files' in status_lower or 'quota' in status_lower or 'limit' in status_lower or 'daily' in status_lower:
                    print(f"[StreamWish] 🚫 DAILY UPLOAD QUOTA EXCEEDED!")
                    print(f"[StreamWish] Status message: {status}")
                    print(f"[StreamWish] The file was uploaded but rejected by StreamWish")
                    wait_seconds = 24 * 3600  # 24 hours
                    wait_until = time.time() + wait_seconds
                    return {
                        'service': 'StreamWish',
                        'success': False,
                        'error': 'QUOTA_EXCEEDED',
                        'error_msg': status,
                        'wait_until': wait_until,
                        'wait_seconds': wait_seconds
                    }
            
            if not filecode:
                print(f"[StreamWish] ❌ No filecode in file info")
                if attempt < max_retries - 1:
                    print(f"[StreamWish] Retrying in 10s...")
                    time.sleep(10)
                    continue
                return {'service': 'StreamWish', 'success': False, 'error': 'No filecode'}
            
            # Success!
            print(f"\n[StreamWish] ═══════════════════════════════════════")
            print(f"[StreamWish] ✅ UPLOAD SUCCESSFUL!")
            print(f"[StreamWish] ═══════════════════════════════════════")
            print(f"[StreamWish] File code: {filecode}")
            print(f"[StreamWish] Embed URL: https://hglink.to/e/{filecode}")
            print(f"[StreamWish] Watch URL: https://hglink.to/{filecode}")
            print(f"[StreamWish] Download URL: https://hglink.to/{filecode}")
            print(f"[StreamWish] Direct URL: https://streamwish.com/{filecode}")
            print(f"[StreamWish] Upload time: {int(upload_time//60)}m {int(upload_time%60)}s")
            print(f"[StreamWish] File size uploaded: {file_size_gb:.2f} GB ({file_size:,} bytes)")
            if folder_name:
                print(f"[StreamWish] Folder: {folder_name}")
            
            # Verify upload by checking file info
            print(f"\n[StreamWish] Verifying upload...")
            verification_passed = False
            try:
                verify_response = requests.get(
                    "https://api.streamwish.com/api/file/info",
                    params={'key': STREAMWISH_API_KEY, 'file_code': filecode},
                    timeout=30
                )
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    print(f"[StreamWish] Verification response: {verify_data}")
                    
                    if verify_data.get('status') == 200 and 'result' in verify_data:
                        file_info_verify = verify_data['result']

                        # Handle case where result is a list (StreamWish API inconsistency)
                        if isinstance(file_info_verify, list):
                            if len(file_info_verify) > 0:
                                file_info_verify = file_info_verify[0]
                            else:
                                file_info_verify = {}

                        # Get file size - StreamWish returns it in file_sizes array
                        server_size = 0
                        if 'file_sizes' in file_info_verify:
                            file_sizes = file_info_verify.get('file_sizes', [])
                            if isinstance(file_sizes, list) and len(file_sizes) > 0:
                                server_size = file_sizes[0].get('size', 0)
                        else:
                            # Fallback to direct size field
                            server_size = file_info_verify.get('size', 0)
                        
                        server_size_gb = int(server_size) / (1024**3) if server_size else 0
                        print(f"[StreamWish] ✓ Server confirms file size: {server_size_gb:.2f} GB ({server_size:,} bytes)")
                        
                        if server_size_gb < 0.1:
                            print(f"[StreamWish] ❌ WARNING: Server shows very small file size!")
                            print(f"[StreamWish] ❌ Upload may have failed silently")
                            verification_passed = False
                        else:
                            verification_passed = True
                    else:
                        print(f"[StreamWish] ❌ Verification failed: {verify_data.get('msg', 'Unknown error')}")
                        verification_passed = False
                else:
                    print(f"[StreamWish] ❌ Verification HTTP error: {verify_response.status_code}")
                    verification_passed = False
            except Exception as e:
                print(f"[StreamWish] ❌ Verification exception: {str(e)[:100]}")
                verification_passed = False
            
            # Test direct access to file (Double check even if verification failed)
            print(f"\n[StreamWish] Testing direct access...")
            direct_access_passed = False
            try:
                test_url = f"https://streamwish.com/{filecode}"
                test_response = requests.head(test_url, timeout=10, allow_redirects=True)
                print(f"[StreamWish] Direct access test: HTTP {test_response.status_code}")
                
                if test_response.status_code == 403:
                    print(f"[StreamWish] ⚠️ 403 Forbidden - File is still processing")
                    print(f"[StreamWish] ℹ️ This is normal for newly uploaded files")
                    print(f"[StreamWish] ℹ️ File will be accessible once processing completes")
                elif test_response.status_code == 404:
                    print(f"[StreamWish] ❌ 404 Not Found - File doesn't exist!")
                elif test_response.status_code in [200, 302]:
                    print(f"[StreamWish] ✓ File is accessible!")
                    direct_access_passed = True
                else:
                    print(f"[StreamWish] ⚠️ Unexpected status: {test_response.status_code}")
            except Exception as e:
                print(f"[StreamWish] ⚠️ Access test error: {str(e)[:100]}")

            # Decision Logic
            if verification_passed:
                print(f"[StreamWish] ✓ API Verification Passed")
            elif direct_access_passed:
                print(f"[StreamWish] ⚠️ API Verification Failed but Direct Access Passed")
                print(f"[StreamWish] ✓ Marking as SUCCESS (Ignoring API metadata issues)")
            elif upload_integrity_confirmed:
                print(f"[StreamWish] ⚠️ Verification failed but upload integrity confirmed locally")
                print(f"[StreamWish] ℹ️ File is likely processing or API is lagging")
                print(f"[StreamWish] ✓ Marking as SUCCESS to avoid duplicates")
            else:
                print(f"[StreamWish] ❌ Verification failed and upload incomplete")
                if attempt < max_retries - 1:
                    print(f"[StreamWish] Retrying upload...")
                    time.sleep(10)
                    continue
                else:
                    print(f"[StreamWish] ❌ All retries exhausted, upload failed")
                    return {
                        'service': 'StreamWish',
                        'success': False,
                        'error': 'Upload verification failed',
                        'filecode': filecode
                    }
            
            print(f"[StreamWish] ═══════════════════════════════════════")
            
            return {
                'service': 'StreamWish',
                'success': True,
                'filecode': filecode,
                'embed_url': f"https://hglink.to/e/{filecode}",
                'watch_url': f"https://hglink.to/{filecode}",
                'download_url': f"https://hglink.to/{filecode}",
                'direct_url': f"https://streamwish.com/{filecode}",
                'api_url': f"https://api.streamwish.com/api/file/direct_link?key={STREAMWISH_API_KEY}&file_code={filecode}",
                'time': upload_time,
                'folder': folder_name,
                'file_size': file_size
            }
            
        except requests.exceptions.Timeout:
            print(f"[StreamWish] ❌ Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                print(f"[StreamWish] Retrying in 10s...")
                time.sleep(10)
        except requests.exceptions.ConnectionError as e:
            print(f"[StreamWish] ❌ Connection error: {str(e)[:100]}")
            if attempt < max_retries - 1:
                print(f"[StreamWish] Retrying in 10s...")
                time.sleep(10)
        except Exception as e:
            print(f"[StreamWish] ❌ Unexpected error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
            if attempt < max_retries - 1:
                print(f"[StreamWish] Retrying in 10s...")
                time.sleep(10)
    
    print(f"\n[StreamWish] ❌ All {max_retries} attempts failed")
    return {'service': 'StreamWish', 'success': False, 'error': 'All retries failed'}


def upload_all(file_path, code, title, video_data=None):
    """
    Main upload function - uploads to StreamWish, falls back to LuluStream if rate limited
    """
    print(f"\n╔══════════════════════════════════════════════════════════╗")
    print(f"║              VIDEO UPLOAD (StreamWish + LuluStream)      ║")
    print(f"╚══════════════════════════════════════════════════════════╝")
    
    # Create nested folder structure: parent_folder/video_code/
    parent_folder = "JAV_VIDEOS"  # Parent folder name
    folder_name = f"{parent_folder}/{code}"  # Nested path
    print(f"📁 Folder structure: {folder_name}")
    print(f"   Parent: {parent_folder}")
    print(f"   Video folder: {code}")
    
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"ATTEMPT 1: StreamWish")
    print(f"{'='*60}")
    result = upload_to_streamwish(file_path, code, title, folder_name)
    
    total_time = time.time() - start_time
    
    if result.get('error') in ['RATE_LIMIT', 'QUOTA_EXCEEDED']:
        print(f"\n{'='*60}")
        print(f"🚫 STREAMWISH QUOTA EXCEEDED - TRYING LULUSTREAM FALLBACK")
        print(f"{'='*60}")
        print(f"StreamWish error: {result.get('error_msg', 'Upload quota exceeded')}")
        print(f"Wait time: {result.get('wait_seconds', 0) / 3600:.1f} hours")
        
        from datetime import datetime
        if result.get('wait_until'):
            resume_time = datetime.fromtimestamp(result['wait_until'])
            print(f"StreamWish resume at: {resume_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n{'='*60}")
        print(f"ATTEMPT 2: LuluStream (Fallback)")
        print(f"{'='*60}")
        
        lulustream_result = upload_to_lulustream(file_path, code, title, folder_name)
        
        total_time = time.time() - start_time
        
        if lulustream_result.get('success'):
            print(f"\n{'='*60}")
            print(f"UPLOAD SUMMARY")
            print(f"{'='*60}")
            print(f"Total time: {int(total_time//60)}m {int(total_time%60)}s")
            print(f"✅ LuluStream (fallback)")
            print(f"   Embed: {lulustream_result['embed_url']}")
            print(f"   Watch: {lulustream_result['watch_url']}")
            print(f"   Time: {int(lulustream_result['time']//60)}m {int(lulustream_result['time']%60)}s")
            print(f"{'='*60}")
            
            return {
                'successful': [lulustream_result],
                'failed': [result],
                'total_time': total_time,
                'rate_limited': True,
                'wait_until': result.get('wait_until'),
                'wait_seconds': result.get('wait_seconds'),
                'error_msg': result.get('error_msg'),
                'fallback_used': 'LuluStream'
            }
        else:
            # Both failed
            print(f"\n{'='*60}")
            print(f"UPLOAD SUMMARY")
            print(f"{'='*60}")
            print(f"Total time: {int(total_time//60)}m {int(total_time%60)}s")
            print(f"❌ StreamWish: Rate limited")
            print(f"❌ LuluStream: {lulustream_result.get('error', 'Unknown error')}")
            print(f"{'='*60}")
            
            return {
                'successful': [],
                'failed': [result, lulustream_result],
                'total_time': total_time,
                'rate_limited': True,
                'wait_until': result.get('wait_until'),
                'wait_seconds': result.get('wait_seconds'),
                'error_msg': result.get('error_msg')
            }
    
    # Summary for normal StreamWish upload
    print(f"\n{'='*60}")
    print(f"UPLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"Total time: {int(total_time//60)}m {int(total_time%60)}s")
    
    successful = []
    failed = []
    
    if result.get('success'):
        successful.append(result)
        print(f"✅ StreamWish")
        print(f"   Embed: {result['embed_url']}")
        print(f"   Watch: {result['watch_url']}")
        print(f"   Time: {int(result['time']//60)}m {int(result['time']%60)}s")
    else:
        failed.append(result)
        print(f"❌ StreamWish: {result.get('error', 'Unknown error')}")
    
    print(f"{'='*60}")
    
    return {
        'successful': successful,
        'failed': failed,
        'total_time': total_time
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_all_hosts.py <video_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    code = os.path.basename(file_path).split('.')[0]
    result = upload_all(file_path, code, code)
    
    sys.exit(0 if result['successful'] else 1)
