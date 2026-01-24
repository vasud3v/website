"""
Parallel Upload - Upload file using multiple parallel streams
Similar to how download managers work, but for uploads
"""
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import time

def upload_chunk_stream(file_path, start_byte, end_byte, chunk_id, upload_url, fields):
    """
    Upload a chunk of the file
    
    Args:
        file_path: Path to file
        start_byte: Starting byte position
        end_byte: Ending byte position
        chunk_id: Chunk identifier
        upload_url: URL to upload to
        fields: Upload form fields
    
    Returns:
        Dict with success status and chunk info
    """
    try:
        chunk_size = end_byte - start_byte
        print(f"[Chunk {chunk_id}] Uploading bytes {start_byte:,} to {end_byte:,} ({chunk_size / (1024**2):.1f} MB)")
        
        # Read chunk from file
        with open(file_path, 'rb') as f:
            f.seek(start_byte)
            chunk_data = f.read(chunk_size)
        
        # Create multipart encoder for this chunk
        chunk_fields = fields.copy()
        chunk_fields['file'] = (f"{os.path.basename(file_path)}.part{chunk_id}", chunk_data, 'application/octet-stream')
        
        encoder = MultipartEncoder(fields=chunk_fields)
        
        # Upload chunk
        start_time = time.time()
        response = requests.post(
            upload_url,
            data=encoder,
            headers={'Content-Type': encoder.content_type},
            timeout=300
        )
        
        elapsed = time.time() - start_time
        speed_mbps = (chunk_size / (1024**2)) / elapsed if elapsed > 0 else 0
        
        if response.status_code == 200:
            print(f"[Chunk {chunk_id}] ✓ Uploaded in {elapsed:.1f}s ({speed_mbps:.1f} MB/s)")
            return {
                'success': True,
                'chunk_id': chunk_id,
                'size': chunk_size,
                'time': elapsed,
                'response': response.json() if response.text else {}
            }
        else:
            print(f"[Chunk {chunk_id}] ❌ Failed: {response.status_code}")
            return {
                'success': False,
                'chunk_id': chunk_id,
                'error': f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        print(f"[Chunk {chunk_id}] ❌ Error: {str(e)[:100]}")
        return {
            'success': False,
            'chunk_id': chunk_id,
            'error': str(e)[:100]
        }

def parallel_upload(file_path, upload_url, fields, num_workers=32):
    """
    Upload file using parallel streams
    
    NOTE: This only works if the hosting service supports chunked/resumable uploads.
    Most video hosting services (StreamWish, LuluStream, Streamtape) do NOT support this.
    
    Args:
        file_path: Path to file to upload
        upload_url: Upload endpoint URL
        fields: Form fields for upload
        num_workers: Number of parallel upload streams
    
    Returns:
        Dict with success status and upload details
    """
    print(f"\n[Parallel Upload] ═══════════════════════════════════════")
    print(f"[Parallel Upload] File: {os.path.basename(file_path)}")
    print(f"[Parallel Upload] Workers: {num_workers}")
    print(f"[Parallel Upload] ═══════════════════════════════════════")
    
    # Get file size
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024**2)
    print(f"[Parallel Upload] Size: {file_size_mb:.1f} MB ({file_size:,} bytes)")
    
    # Calculate chunk size
    chunk_size = file_size // num_workers
    print(f"[Parallel Upload] Chunk size: {chunk_size / (1024**2):.1f} MB")
    
    # Create chunks
    chunks = []
    for i in range(num_workers):
        start_byte = i * chunk_size
        end_byte = start_byte + chunk_size if i < num_workers - 1 else file_size
        chunks.append((start_byte, end_byte, i))
    
    print(f"[Parallel Upload] Created {len(chunks)} chunks")
    print(f"[Parallel Upload] Starting parallel upload...")
    
    # Upload chunks in parallel
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(
                upload_chunk_stream,
                file_path,
                start_byte,
                end_byte,
                chunk_id,
                upload_url,
                fields
            ): chunk_id
            for start_byte, end_byte, chunk_id in chunks
        }
        
        for future in as_completed(futures):
            chunk_id = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"[Chunk {chunk_id}] ❌ Exception: {str(e)[:100]}")
                results.append({
                    'success': False,
                    'chunk_id': chunk_id,
                    'error': str(e)[:100]
                })
    
    elapsed = time.time() - start_time
    
    # Check results
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"\n[Parallel Upload] ═══════════════════════════════════════")
    print(f"[Parallel Upload] Upload complete in {elapsed:.1f}s")
    print(f"[Parallel Upload] Successful chunks: {len(successful)}/{len(chunks)}")
    print(f"[Parallel Upload] Failed chunks: {len(failed)}")
    
    if len(successful) == len(chunks):
        speed_mbps = file_size_mb / elapsed if elapsed > 0 else 0
        print(f"[Parallel Upload] ✓ All chunks uploaded successfully")
        print(f"[Parallel Upload] Average speed: {speed_mbps:.1f} MB/s")
        print(f"[Parallel Upload] ═══════════════════════════════════════")
        
        return {
            'success': True,
            'file_size': file_size,
            'chunks': len(chunks),
            'time': elapsed,
            'speed_mbps': speed_mbps,
            'results': results
        }
    else:
        print(f"[Parallel Upload] ❌ Some chunks failed")
        print(f"[Parallel Upload] ═══════════════════════════════════════")
        
        return {
            'success': False,
            'error': f"{len(failed)} chunks failed",
            'failed_chunks': failed,
            'results': results
        }

# Note: This is a proof of concept. Most video hosting services do NOT support
# chunked/resumable uploads. They expect the full file in one multipart request.
# 
# To use parallel upload, the hosting service must support one of:
# 1. Chunked upload API (upload parts separately, then merge)
# 2. Resumable upload API (upload with Range headers)
# 3. Multiple simultaneous connections to same upload endpoint
#
# StreamWish, LuluStream, and Streamtape do NOT support these features.
# They require the full file in a single multipart/form-data request.
