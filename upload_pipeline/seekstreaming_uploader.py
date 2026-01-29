import requests
import os
from pathlib import Path
import time
import base64
import sys

class SeekstreamingUploader:
    def __init__(self, api_key, email=None, password=None):
        self.api_key = api_key
        self.base_url = "https://seekstreaming.com"
        # Keep chunk size at 50 MB as per API spec
        self.chunk_size = 52428800  # 50 MB (required by API)
        self.session = requests.Session()  # Reuse connections for speed
        self.session.headers.update({
            'User-Agent': 'SeekStreaming-Uploader/2.0',
            'Connection': 'keep-alive'
        })
        # Optimized connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=3,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _print_progress_bar(self, current, total, start_time, prefix='Progress'):
        """Print a progress bar with speed and ETA"""
        bar_length = 40
        progress = current / total
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        elapsed = time.time() - start_time
        speed = (current / (1024*1024)) / elapsed if elapsed > 0 else 0
        
        if progress > 0:
            eta = (elapsed / progress) - elapsed
            eta_str = f"{int(eta)}s"
        else:
            eta_str = "calculating..."
        
        percent = progress * 100
        current_mb = current / (1024*1024)
        total_mb = total / (1024*1024)
        
        # Clear line and print progress
        sys.stdout.write('\r')
        sys.stdout.write(f"{prefix}: |{bar}| {percent:.1f}% ({current_mb:.1f}/{total_mb:.1f} MB) "
                        f"Speed: {speed:.2f} MB/s ETA: {eta_str}  ")
        sys.stdout.flush()
    
    def get_video_info(self, video_id):
        """Get detailed video information from API"""
        try:
            headers = {
                'api-token': self.api_key,
                'Content-Type': 'application/json'
            }
            
            # Retry loop for 404s (video processing lag)
            max_retries = 3
            for attempt in range(max_retries):
                # Request video details
                try:
                    response = self.session.get(
                        f"{self.base_url}/api/v1/video/{video_id}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 404:
                        if attempt < max_retries - 1:
                            print(f"[Seekstreaming] Video details not ready yet (404), retrying in 2s...")
                            time.sleep(2)
                            continue
                        else:
                            print(f"[Seekstreaming] Could not fetch video details: {response.status_code}")
                            return None
                    else:
                        print(f"[Seekstreaming] API Error: {response.status_code}")
                        return None
                except requests.exceptions.RequestException:
                    if attempt < max_retries - 1:
                         time.sleep(2)
                         continue
                    raise
            return None
                
        except Exception as e:
            print(f"[Seekstreaming] Error fetching video info: {str(e)}")
            return None
    
    def _extract_all_urls(self, video_id):
        """Extract URLs for embedding using custom domain"""
        # Use custom domain format
        embed_url = f"https://javcore.embedseek.com/#{video_id}"
        
        urls = {
            "video_player": embed_url,
            "video_downloader": embed_url,
            "embed_code": f'<iframe src="{embed_url}" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>',
        }
        
        return urls
    
    def _get_upload_endpoint(self):
        """Get TUS upload URL and access token"""
        try:
            headers = {
                'api-token': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = self.session.get(
                f"{self.base_url}/api/v1/video/upload",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'tus_url': data.get('tusUrl'),
                    'access_token': data.get('accessToken')
                }
            else:
                print(f"[Seekstreaming] Failed to get upload endpoint: {response.status_code}")
                print(f"[Seekstreaming] Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"[Seekstreaming] Error getting upload endpoint: {str(e)}")
            return None
    
    def _tus_upload_optimized(self, video_path, tus_url, access_token, title=None):
        """Upload video using TUS protocol with optimizations"""
        try:
            file_name = Path(video_path).name
            file_size = os.path.getsize(video_path)
            file_type = 'video/mp4'
            
            # Prepare metadata for TUS
            metadata_parts = [
                f"accessToken {base64.b64encode(access_token.encode()).decode()}",
                f"filename {base64.b64encode(file_name.encode()).decode()}",
                f"filetype {base64.b64encode(file_type.encode()).decode()}"
            ]
            
            if title:
                metadata_parts.append(f"title {base64.b64encode(title.encode()).decode()}")
            
            metadata = ",".join(metadata_parts)
            
            # Step 1: Create upload session
            print(f"[Seekstreaming] Creating TUS upload session...")
            headers = {
                'Tus-Resumable': '1.0.0',
                'Upload-Length': str(file_size),
                'Upload-Metadata': metadata,
                'Content-Type': 'application/offset+octet-stream'
            }
            
            response = self.session.post(tus_url, headers=headers, timeout=30)
            
            if response.status_code not in [200, 201]:
                return {"success": False, "error": f"Failed to create upload session: {response.status_code}"}
            
            upload_location = response.headers.get('Location')
            if not upload_location:
                return {"success": False, "error": "No upload location returned"}
            
            print(f"[Seekstreaming] Upload session created")
            print(f"[Seekstreaming] File size: {file_size / (1024*1024):.2f} MB")
            print(f"[Seekstreaming] Chunk size: {self.chunk_size / (1024*1024):.0f} MB")
            print()
            
            print()
            
            # Step 1.5: Check for existing offset (Resume capability)
            offset = 0
            try:
                head_resp = self.session.head(upload_location, headers={'Tus-Resumable': '1.0.0'})
                if head_resp.status_code == 200:
                    server_offset = int(head_resp.headers.get('Upload-Offset', 0))
                    if server_offset > 0:
                        print(f"[Seekstreaming] Resuming from offset {server_offset} ({server_offset/(1024*1024):.1f} MB)")
                        offset = server_offset
            except Exception as e:
                print(f"[Seekstreaming] Warning: Could not check offset: {e}")

            start_time = time.time()
            
            # Step 2: Upload file in chunks with progress bar
            with open(video_path, 'rb') as f:
                # Seek to current offset
                if offset > 0:
                    f.seek(offset)
                
                chunk_num = 0
                total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
                
                while offset < file_size:
                    chunk_num += 1
                    chunk_end = min(offset + self.chunk_size, file_size)
                    
                    # Read chunk
                    chunk_data = f.read(self.chunk_size)
                    chunk_size = len(chunk_data)
                    
                    if not chunk_data:
                        break
                    
                    # Show progress before upload
                    self._print_progress_bar(offset, file_size, start_time, 'Uploading')
                    
                    headers = {
                        'Tus-Resumable': '1.0.0',
                        'Upload-Offset': str(offset),
                        'Content-Type': 'application/offset+octet-stream',
                        'Content-Length': str(chunk_size)
                    }
                    
                    # Upload chunk with retry logic
                    max_retries = 3
                    success = False
                    
                    for attempt in range(max_retries):
                        try:
                            response = self.session.patch(
                                upload_location,
                                headers=headers,
                                data=chunk_data,
                                timeout=600  # Longer timeout for large chunks
                            )
                            
                            if response.status_code in [200, 204]:
                                success = True
                                break
                            elif attempt < max_retries - 1:
                                time.sleep(0.5)
                        except Exception as e:
                            if attempt < max_retries - 1:
                                time.sleep(0.5)
                            else:
                                raise
                    
                    if not success:
                        print()
                        return {"success": False, "error": f"Upload failed at offset {offset}: {response.status_code}"}
                    
                    offset += chunk_size
                
                # Final progress update
                self._print_progress_bar(file_size, file_size, start_time, 'Uploading')
                print()  # New line after progress bar
            
            elapsed = time.time() - start_time
            speed_mbps = (file_size / (1024*1024)) / elapsed if elapsed > 0 else 0
            
            print()
            print(f"[Seekstreaming] ✓ Upload completed in {elapsed:.1f}s (avg {speed_mbps:.2f} MB/s)")
            
            # Extract actual video ID from the final PATCH response body
            actual_video_id = None
            try:
                if response.text:
                    response_data = response.json()
                    actual_video_id = response_data.get('videoId')
                    if actual_video_id:
                        print(f"[Seekstreaming] ✓ Got actual video ID: {actual_video_id}")
            except:
                pass
            
            # If we didn't get the video ID from response, extract from upload location
            if not actual_video_id:
                tus_upload_id = upload_location.split('/')[-1]
                print(f"[Seekstreaming] ⚠ Video ID not in response, using TUS upload ID: {tus_upload_id}")
                actual_video_id = tus_upload_id
            
            # Extract all possible URLs using the actual video ID
            print(f"[Seekstreaming] Extracting video URLs...")
            all_urls = self._extract_all_urls(actual_video_id)
            
            # Try to get additional video info from API
            video_info = self.get_video_info(actual_video_id)
            
            result = {
                "success": True,
                "host": "seekstreaming",
                "file_code": actual_video_id,
                "video_id": actual_video_id,
                "all_urls": all_urls,
                "upload_time": elapsed,
                "speed_mbps": speed_mbps
            }
            
            # Add video info if available
            if video_info:
                result["video_info"] = video_info
            
            return result
            
        except Exception as e:
            print()
            print(f"[Seekstreaming] TUS upload error: {str(e)}")
            return {"success": False, "error": str(e)}
        
    def upload(self, video_path, title=None):
        """Upload video to Seekstreaming using optimized TUS protocol"""
        try:
            if not os.path.exists(video_path):
                return {"success": False, "error": "Video file not found"}
            
            file_name = Path(video_path).name
            title = title or Path(video_path).stem
            
            print(f"[Seekstreaming] Starting upload: {file_name}")
            
            # Get TUS upload endpoint
            endpoint_info = self._get_upload_endpoint()
            if not endpoint_info or not endpoint_info.get('tus_url'):
                return {"success": False, "error": "Failed to get upload endpoint. Check API key."}
            
            # Upload using optimized TUS protocol
            return self._tus_upload_optimized(
                video_path,
                endpoint_info['tus_url'],
                endpoint_info['access_token'],
                title
            )
                    
        except Exception as e:
            print(f"[Seekstreaming] Error: {str(e)}")
            return {"success": False, "error": str(e)}
