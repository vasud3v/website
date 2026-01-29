"""
Advanced HLS Downloader with Anti-Throttling Techniques
- Optimal 12 workers (configurable)
- Rotating User-Agents
- Connection reuse optimization
- Request spacing to avoid detection
- Retry with backoff
"""
import os
import sys
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import m3u8
import shutil
import glob
from pathlib import Path
import random
try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None
    print("⚠️ pycryptodome not installed - decryption will fail")

# Optimal default based on CDN analysis
# Note: CDN throttles heavily (~0.1-0.2 MB/s) regardless of worker count
# 18 workers provides best balance between speed and avoiding detection
DEFAULT_WORKERS = 32

class AdvancedHLSDownloader:
    def __init__(self, max_workers=32):
        self.max_workers = max_workers
        self.session = requests.Session()
        # Increase pool size significantly to prevent connection exhaustion
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_workers * 3,  # Increased pool for high concurrency
            pool_maxsize=max_workers * 3,
            max_retries=2,
            pool_block=False  # Don't block when pool is full, create new connection
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Use a single, standard high-quality User-Agent + Keep-Alive
        self.session.headers.update({
            'Referer': 'https://javgg.net/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        
        self.rate_limit_delay = 0
        self.consecutive_403s = 0
    
    def get_key(self, key_uri, base_url):
        """Fetch decryption key with retry"""
        if not key_uri.startswith('http'):
            key_uri = base_url + key_uri
        
        # Retry key fetch up to 3 times
        for attempt in range(3):
            try:
                response = self.session.get(key_uri, timeout=15)
                response.raise_for_status()
                if len(response.content) == 16:  # AES-128 key is 16 bytes
                    return response.content
                else:
                    print(f"  ⚠️ Invalid key size: {len(response.content)} bytes")
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    print(f"  ❌ Key fetch failed after 3 attempts: {e}")
        return None

    def decrypt_segment(self, data, key, iv):
        """Decrypt AES-128 segment"""
        if not AES:
            return data
        
        try:
            if len(key) != 16:
                return data
            if len(iv) != 16:
                return data
            
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(data)
            
            # Remove PKCS7 padding safely
            if len(decrypted) > 0:
                pad_len = decrypted[-1]
                if isinstance(pad_len, int) and 1 <= pad_len <= 16:
                    return decrypted[:-pad_len]
            return decrypted
        except Exception as e:
            # If decryption fails, return original data
            return data

    def download_segment(self, args):
        """Download a single segment"""
        index, url, output_path, m3u8_url, base_url, key_info = args
        
        # RESUME: Skip if already downloaded and valid
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            if size > 0:
                return index, True, size, False
        
        # Adaptive rate limiting (Matches Jable V2 logic)
        if self.rate_limit_delay > 0.15:
            time.sleep(self.rate_limit_delay * 0.2)
        
        # Retry loop
        for attempt in range(3):
            try:
                if attempt > 0:
                    time.sleep(0.2 * attempt)
                
                # Reduced timeout to prevent hanging
                response = self.session.get(url, timeout=15, stream=False)
                response.raise_for_status()
                data = response.content
                
                if len(data) == 0:
                    raise ValueError("Empty segment")
                
                # Decrypt if needed
                if key_info:
                    key, iv = key_info
                    if key:
                         data = self.decrypt_segment(data, key, iv)

                # Atomic write with error handling
                temp_path = output_path + '.tmp'
                try:
                    with open(temp_path, 'wb') as f:
                        f.write(data)
                    # Verify temp file was written correctly
                    if os.path.getsize(temp_path) == len(data):
                        os.replace(temp_path, output_path)
                    else:
                        raise IOError("Temp file size mismatch")
                except Exception as write_error:
                    # Clean up temp file on error
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                    raise write_error
                
                return index, True, len(data), False
                
            except requests.exceptions.HTTPError as e:
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 403:
                        if attempt < 2:
                            time.sleep(0.2)
                            continue
                        return index, False, 0, True  # 403 error
                if attempt < 2:
                    time.sleep(0.1)
            except requests.exceptions.Timeout:
                # Timeout - retry with exponential backoff
                if attempt < 2:
                    time.sleep(0.3 * (attempt + 1))
            except requests.exceptions.ConnectionError:
                # Connection error - retry
                if attempt < 2:
                    time.sleep(0.2 * (attempt + 1))
            except Exception as e:
                # Other errors
                if attempt < 2:
                    time.sleep(0.1)
        
        return index, False, 0, False

    def save_progress(self, temp_dir, downloaded_count, total_count):
        """Save download progress"""
        progress_file = os.path.join(temp_dir, '.progress.json')
        try:
            with open(progress_file, 'w') as f:
                json.dump({
                    'downloaded': downloaded_count,
                    'total': total_count,
                    'timestamp': time.time()
                }, f)
        except:
            pass
    
    def load_progress(self, temp_dir):
        """Load previous progress"""
        progress_file = os.path.join(temp_dir, '.progress.json')
        try:
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None
    
    def cleanup_temp_dir(self, temp_dir):
        """Clean up temp directory"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass
    
    def download(self, m3u8_url, output_file, code=None):
        """Download with high concurrency (Jable-style)"""
        print(f"\n📥 High-Performance HLS Downloader ({self.max_workers} workers)")
        
        if not m3u8_url or not m3u8_url.startswith('http'):
            print(f"  ❌ Invalid M3U8 URL")
            return False
        
        start_time = time.time()
        output_path = Path(output_file)
        if output_path.suffix != '.ts':
            temp_output = output_path.with_suffix('.ts')
        else:
            temp_output = output_path
        
        temp_dir = str(temp_output) + '_segments'
        
        try:
            # Parse M3U8
            print(f"  📋 Parsing M3U8...")
            response = self.session.get(m3u8_url, timeout=30)
            response.raise_for_status()
            playlist = m3u8.loads(response.text, uri=m3u8_url)
            
            base_url = m3u8_url.rsplit('/', 1)[0] + '/'
            
            # Handle master playlist
            if playlist.playlists:
                sorted_playlists = sorted(playlist.playlists, 
                                        key=lambda p: p.stream_info.bandwidth or 0, 
                                        reverse=True)
                best = sorted_playlists[0]
                bandwidth_mbps = (best.stream_info.bandwidth or 0) / 1_000_000
                resolution = f"{best.stream_info.resolution[0]}x{best.stream_info.resolution[1]}" if best.stream_info.resolution else "unknown"
                print(f"  🎬 Using BEST quality: {bandwidth_mbps:.1f} Mbps ({resolution})")
                
                media_url = base_url + best.uri if not best.uri.startswith('http') else best.uri
                response = self.session.get(media_url, timeout=30)
                response.raise_for_status()
                playlist = m3u8.loads(response.text, uri=media_url)
                base_url = media_url.rsplit('/', 1)[0] + '/'
            
            segments = playlist.segments
            total = len(segments)
            
            if total == 0:
                print(f"  ❌ No segments found!")
                return False
            
            print(f"  📦 Total segments: {total}")
            print(f"  🚀 Using {self.max_workers} parallel workers (optimized session)")
            
            os.makedirs(temp_dir, exist_ok=True)
            
            # Resume check
            prev_progress = self.load_progress(temp_dir)
            if prev_progress:
                print(f"  📂 Resuming: {prev_progress['downloaded']}/{prev_progress['total']} segments")
            
            # Check for encryption and fetch key once
            has_keys = playlist.keys and playlist.keys[0]
            encryption_key = None
            media_sequence_start = playlist.media_sequence if hasattr(playlist, 'media_sequence') else 0

            if has_keys:
                print(f"  🔐 Encryption detected: AES-128")
                try:
                    key_uri = playlist.keys[0].uri
                    encryption_key = self.get_key(key_uri, base_url)
                    if encryption_key:
                         print(f"  🔑 Key fetched successfully")
                except Exception as e:
                    print(f"  ❌ Failed to fetch key: {e}")
                    return False
            
            # Prepare tasks
            tasks = []
            for i, seg in enumerate(segments):
                url = base_url + seg.uri if not seg.uri.startswith('http') else seg.uri
                path = os.path.join(temp_dir, f'seg_{i:05d}.ts')
                
                # encryption info for this segment
                key_info = None
                if seg.key and seg.key.method == 'AES-128':
                     key = encryption_key if encryption_key else self.get_key(seg.key.uri, base_url)
                     
                     if seg.key.iv:
                         iv = bytes.fromhex(seg.key.iv[2:] if seg.key.iv.startswith('0x') else seg.key.iv)
                     else:
                         # IV is the sequence number (big-endian 16 bytes)
                         seq = media_sequence_start + i
                         iv = seq.to_bytes(16, byteorder='big')
                     
                     key_info = (key, iv)
                
                tasks.append((i, url, path, m3u8_url, base_url, key_info))
            
            print(f"  ⚡ Starting download...")
            
            downloaded = 0
            failed = []
            total_bytes = 0
            last_print = 0
            last_save = 0
            error_403_count = 0
            bar_width = 50
            
            # ThreadPool execution with timeout protection
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.download_segment, t): t for t in tasks}
                
                # Add timeout to prevent indefinite hangs
                timeout_per_segment = 60  # 60 seconds per segment max
                
                for future in as_completed(futures, timeout=timeout_per_segment * total):
                    try:
                        idx, success, size, got_403 = future.result(timeout=timeout_per_segment)
                    except Exception as e:
                        # Handle timeout or other exceptions
                        task_info = futures.get(future)
                        if task_info:
                            idx = task_info[0]
                            failed.append(idx)
                            print(f"\n  ⚠️ Segment {idx} timed out or failed: {str(e)[:50]}")
                        continue
                    
                    if success:
                        downloaded += 1
                        total_bytes += size
                        
                        # Reset 403 counter on success
                        if error_403_count > 0:
                            error_403_count = max(0, error_403_count - 3)
                            self.rate_limit_delay = max(0, self.rate_limit_delay - 0.05)
                        
                        current_time = time.time()
                        
                        # Update progress
                        if downloaded % 25 == 0 or (current_time - last_print) >= 2:
                            progress = (downloaded / total) * 100
                            elapsed = current_time - start_time
                            speed = (total_bytes / (1024*1024)) / elapsed if elapsed > 0 else 0
                            
                            # Throttling Check (0.5 MB/s threshold)
                            if elapsed > 30 and speed < 0.5:
                                print(f"\n  ⚠️ Throttling detected! Speed: {speed:.2f} MB/s")
                                print(f"  🛑 Aborting to trigger restart...")
                                return False

                            filled = int(bar_width * progress / 100)
                            bar = '█' * filled + '░' * (bar_width - filled)
                            
                            status = f"\r  [{bar}] {progress:.1f}% | {speed:.1f} MB/s"
                            sys.stdout.write(status)
                            sys.stdout.flush()
                            last_print = current_time
                        
                        if downloaded % 100 == 0:
                            self.save_progress(temp_dir, downloaded, total)
                    else:
                        failed.append(idx)
                        if got_403:
                            error_403_count += 1
                            if error_403_count > 10:
                                self.rate_limit_delay = min(0.2, self.rate_limit_delay + 0.02)
            
            sys.stdout.write(f"\r{' '*100}\r") # Clear line
            
            if failed:
                print(f"  ⚠️ {len(failed)} segments failed initially. Retrying...")
                # Retry logic similar to Jable V2 (simplified for brevity)
                # If failure rate is high (>50%), abort
                if len(failed) / total > 0.5:
                     print(f"  ❌ High failure rate. Aborting.")
                     return False
                
                # Retry with reduced workers and timeout protection
                retry_tasks = [tasks[i] for i in failed]
                still_failed = []
                retry_workers = min(16, len(retry_tasks))
                
                with ThreadPoolExecutor(max_workers=retry_workers) as executor:
                    futures = {executor.submit(self.download_segment, t): t for t in retry_tasks}
                    
                    # Add timeout for retry phase
                    retry_timeout = 120  # 2 minutes per segment on retry
                    try:
                        for future in as_completed(futures, timeout=retry_timeout * len(retry_tasks)):
                            try:
                                idx, success, size, _ = future.result(timeout=retry_timeout)
                                if success:
                                    downloaded += 1
                                    total_bytes += size
                                else:
                                    still_failed.append(idx)
                            except Exception as e:
                                task_info = futures.get(future)
                                if task_info:
                                    still_failed.append(task_info[0])
                    except Exception as timeout_error:
                        print(f"\n  ⚠️ Retry phase timeout: {timeout_error}")
                        # Mark remaining futures as failed
                        for future, task_info in futures.items():
                            if not future.done():
                                still_failed.append(task_info[0])
                
                if still_failed:
                    print(f"  ❌ {len(still_failed)} segments failed after retry.")
                    return False

            # Merge
            print(f"  🔗 Merging {downloaded} segments...")
            if not self.merge(temp_dir, str(temp_output), total):
                return False
            
            # Validate merged video
            print(f"  🔍 Validating merged video...")
            is_valid, msg = self.validate_merged_video(str(temp_output))
            if not is_valid:
                print(f"  ❌ Validation failed: {msg}")
                return False
            print(f"  ✅ Validation passed: {msg}")
            
            # Convert with better error handling
            if temp_output != output_path:
                print(f"  🎬 Converting to MP4...")
                try:
                    import subprocess
                    cmd = ['ffmpeg', '-i', str(temp_output), '-c', 'copy', '-y', str(output_path)]
                    result = subprocess.run(cmd, capture_output=True, timeout=600, text=True)
                    
                    if result.returncode == 0 and os.path.exists(output_path):
                        # Verify converted file
                        if os.path.getsize(output_path) > 0:
                            temp_output.unlink()
                        else:
                            print(f"  ⚠️ Converted file is empty, keeping .ts")
                            output_path = temp_output
                    else:
                        print(f"  ⚠️ FFmpeg conversion failed, keeping .ts file")
                        print(f"  Error: {result.stderr[:200]}")
                        output_path = temp_output
                except subprocess.TimeoutExpired:
                    print(f"  ⚠️ FFmpeg timeout, keeping .ts file")
                    output_path = temp_output
                except Exception as e:
                    print(f"  ⚠️ Conversion error: {e}, keeping .ts file")
                    output_path = temp_output
            
            self.cleanup_temp_dir(temp_dir)
            total_time = time.time() - start_time
            
            # Final verification
            if os.path.exists(output_path):
                size_gb = os.path.getsize(output_path) / (1024**3)
                avg_speed = (size_gb * 1024) / (total_time / 60) if total_time > 0 else 0
                print(f"  ✅ Complete! {size_gb:.2f} GB in {int(total_time)}s ({avg_speed:.1f} MB/min)")
                return True
            else:
                print(f"  ❌ Output file not found: {output_path}")
                return False

        except KeyboardInterrupt:
            print(f"\n  ⚠️ Download interrupted by user")
            print(f"  📂 Temp files preserved in: {temp_dir}")
            print(f"  💡 Resume by running the same command again")
            return False
        except Exception as e:
            print(f"  ❌ Download Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def merge(self, temp_dir, output, total):
        try:
            # Sort segments numerically by index
            # Filename format: seg_00001.ts
            segments = glob.glob(os.path.join(temp_dir, "seg_*.ts"))
            
            if not segments: 
                print(f"  ❌ No segments found in {temp_dir}")
                return False
            
            # Robust numeric sort with error handling
            try:
                segments.sort(key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
            except (ValueError, IndexError) as e:
                print(f"  ❌ Failed to sort segments: {e}")
                return False
            
            # Check for missing segments
            segment_indices = [int(os.path.basename(s).split('_')[1].split('.')[0]) for s in segments]
            expected_indices = set(range(total))
            missing_indices = expected_indices - set(segment_indices)
            
            if missing_indices:
                print(f"  ⚠️ Missing {len(missing_indices)} segments: {sorted(list(missing_indices))[:10]}...")
            
            if len(segments) < total * 0.95:  # Allow 5% loss max
                print(f"  ❌ Too many missing segments: {len(segments)}/{total}")
                return False
            
            # Merge with progress for large files
            merged_size = 0
            temp_output = output + '.merging'
            
            with open(temp_output, 'wb') as outfile:
                for i, seg in enumerate(segments):
                    try:
                        seg_size = os.path.getsize(seg)
                        if seg_size == 0:
                            print(f"  ⚠️ Skipping empty segment: {seg}")
                            continue
                        
                        with open(seg, 'rb') as infile:
                            chunk_size = 1024 * 1024  # 1MB chunks
                            while True:
                                chunk = infile.read(chunk_size)
                                if not chunk:
                                    break
                                outfile.write(chunk)
                        
                        merged_size += seg_size
                        
                        # Progress for large merges
                        if i % 100 == 0 and i > 0:
                            progress = (i / len(segments)) * 100
                            print(f"  🔗 Merging: {progress:.1f}% ({merged_size / (1024**2):.1f} MB)")
                    
                    except Exception as seg_error:
                        print(f"  ⚠️ Error reading segment {seg}: {seg_error}")
                        continue
            
            # Atomic rename
            if os.path.exists(temp_output):
                if os.path.getsize(temp_output) > 0:
                    os.replace(temp_output, output)
                    return True
                else:
                    print(f"  ❌ Merged file is empty")
                    os.remove(temp_output)
                    return False
            
            return False
            
        except Exception as e:
            print(f"  ❌ Merge error: {e}")
            import traceback
            traceback.print_exc()
            return False

    
    def validate_merged_video(self, video_path):
        """Validate merged video file"""
        try:
            if not os.path.exists(video_path):
                return False, "File not found"
            
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            if size_mb < 10:
                return False, f"File too small: {size_mb:.2f} MB"
            
            # Quick validation with ffprobe
            import subprocess
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_format',
                '-of', 'json',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return False, "ffprobe validation failed"
            
            data = json.loads(result.stdout)
            format_name = data.get('format', {}).get('format_name', '')
            
            if 'png' in format_name.lower() or 'image' in format_name.lower():
                return False, f"Invalid format: {format_name}"
            
            duration = float(data.get('format', {}).get('duration', 0))
            if duration < 30:
                return False, f"Duration too short: {duration}s"
            
            return True, f"Valid ({size_mb:.1f} MB, {duration:.0f}s)"
            
        except Exception as e:
            return False, f"Validation error: {str(e)[:100]}"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python hls_downloader_advanced.py <m3u8_url> <output_file> [workers]")
        print(f"Default workers: {DEFAULT_WORKERS} (recommended)")
        sys.exit(1)
    
    m3u8_url = sys.argv[1]
    output_file = sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_WORKERS
    
    downloader = AdvancedHLSDownloader(max_workers=workers)
    success = downloader.download(m3u8_url, output_file)
    
    sys.exit(0 if success else 1)
