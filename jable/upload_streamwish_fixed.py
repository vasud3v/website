"""
Fixed StreamWish upload - ensures full file is uploaded
"""
import os
import sys
import time
import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


def upload_with_progress(file_path, upload_server, upload_data):
    """
    Upload file with proper multipart encoding and progress tracking
    This ensures the ENTIRE file is uploaded, not just a chunk
    """
    file_size = os.path.getsize(file_path)
    file_size_gb = file_size / (1024**3)
    
    print(f"[Upload] File size: {file_size_gb:.2f} GB ({file_size:,} bytes)")
    print(f"[Upload] Opening file: {file_path}")
    
    # Create multipart encoder with the file
    # This properly handles large file uploads
    fields = {
        'key': upload_data['key'],
        'file_title': upload_data['file_title'],
        'file_adult': upload_data['file_adult'],
    }
    
    # Add folder ID if present
    if 'fld_id' in upload_data:
        fields['fld_id'] = upload_data['fld_id']
    
    # Add the file - this will be read completely
    fields['file'] = (os.path.basename(file_path), open(file_path, 'rb'), 'video/mp4')
    
    print(f"[Upload] Creating multipart encoder...")
    encoder = MultipartEncoder(fields=fields)
    
    print(f"[Upload] Encoder size: {encoder.len:,} bytes")
    print(f"[Upload] Encoder size GB: {encoder.len / (1024**3):.2f} GB")
    
    if encoder.len < file_size * 0.9:
        print(f"[Upload] ⚠️ WARNING: Encoder size is smaller than file size!")
        print(f"[Upload] This indicates a problem with file encoding")
        return None
    
    # Create progress monitor
    last_update = [time.time()]
    last_bytes = [0]
    start_time = time.time()
    
    def progress_callback(monitor):
        current_time = time.time()
        if current_time - last_update[0] >= 5.0:  # Update every 5 seconds
            progress = (monitor.bytes_read / monitor.len) * 100
            elapsed = current_time - start_time
            
            bytes_diff = monitor.bytes_read - last_bytes[0]
            time_diff = current_time - last_update[0]
            speed = (bytes_diff / (1024*1024)) / time_diff if time_diff > 0 else 0
            
            bar = '█' * int(40 * progress / 100) + '░' * (40 - int(40 * progress / 100))
            print(f"[Upload] [{bar}] {progress:.1f}% | {monitor.bytes_read:,}/{monitor.len:,} | ↑{speed:.1f} MB/s")
            sys.stdout.flush()
            
            last_update[0] = current_time
            last_bytes[0] = monitor.bytes_read
    
    monitor = MultipartEncoderMonitor(encoder, progress_callback)
    
    print(f"[Upload] Starting upload to {upload_server}")
    print(f"[Upload] This will take several minutes for large files...")
    sys.stdout.flush()
    
    try:
        response = requests.post(
            upload_server,
            data=monitor,
            headers={'Content-Type': monitor.content_type},
            timeout=7200  # 2 hour timeout
        )
        
        elapsed = time.time() - start_time
        print(f"\n[Upload] ✓ Upload completed in {int(elapsed//60)}m {int(elapsed%60)}s")
        print(f"[Upload] Total bytes sent: {monitor.bytes_read:,}")
        print(f"[Upload] Average speed: {(monitor.bytes_read / (1024**2)) / elapsed:.1f} MB/s")
        
        # Verify we sent the full file
        if monitor.bytes_read < file_size * 0.95:
            print(f"[Upload] ❌ WARNING: Only {monitor.bytes_read:,} bytes sent out of {file_size:,}")
            print(f"[Upload] Upload may be incomplete!")
        else:
            print(f"[Upload] ✓ Full file uploaded successfully")
        
        return response
        
    except Exception as e:
        print(f"[Upload] ❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Close the file
        if 'file' in fields and hasattr(fields['file'][1], 'close'):
            fields['file'][1].close()


def test_upload(file_path):
    """Test upload with a file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    # Mock upload data
    upload_data = {
        'key': 'test_key',
        'file_title': 'Test Video',
        'file_adult': '1'
    }
    
    # Mock server (will fail but we can see the encoding)
    upload_server = 'https://httpbin.org/post'
    
    print(f"\nTesting upload encoding for: {file_path}")
    print(f"="*60)
    
    response = upload_with_progress(file_path, upload_server, upload_data)
    
    if response:
        print(f"\nResponse status: {response.status_code}")
        print(f"Response size: {len(response.content)} bytes")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_streamwish_fixed.py <video_file>")
        sys.exit(1)
    
    test_upload(sys.argv[1])
