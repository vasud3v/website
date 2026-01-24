"""
Download HLS with AES decryption support - Enhanced Version
Features:
- Resume capability (skip already downloaded segments)
- Disk space checking
- Better cleanup on failure
- Segment validation
- Progress persistence
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
from Crypto.Cipher import AES

MAX_WORKERS = 32  # High concurrency with smart rate limiting

class HLSDownloaderV2:
    def __init__(self, max_workers=32):
        self.max_workers = max_workers
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_workers * 2,  # Increased pool
            pool_maxsize=max_workers * 2,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'Referer': 'https://jable.tv/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.keys_cache = {}
        self.rate_limit_delay = 0  # Adaptive delay for rate limiting
        self.consecutive_403s = 0  # Track 403 errors
    
    def check_disk_space(self, required_bytes, path='.'):
        """Check if enough disk space is available"""
        try:
            import shutil as sh
            stat = sh.disk_usage(path)
            available = stat.free
            # Add 10% buffer
            required_with_buffer = required_bytes * 1.1
            return available > required_with_buffer, available, required_with_buffer
        except Exception as e:
            print(f"   ⚠️ Could not check disk space: {e}")
            return True, 0, 0  # Assume OK if can't check
    
    def get_key(self, key_uri, base_url):
        """Download and cache decryption key with retry logic"""
        if key_uri in self.keys_cache:
            return self.keys_cache[key_uri]
        
        if not key_uri.startswith('http'):
            key_uri = base_url + key_uri
        
        print(f"\n   Fetching decryption key: {key_uri[:80]}...")
        sys.stdout.flush()
        
        # Retry logic for key fetching
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(key_uri, timeout=10)
                response.raise_for_status()
                key = response.content
                
                # Validate key length (should be 16 bytes for AES-128)
                if len(key) != 16:
                    raise ValueError(f"Invalid key length: {len(key)} bytes (expected 16)")
                
                self.keys_cache[key_uri] = key
                print(f"   ✓ Key fetched ({len(key)} bytes)")
                sys.stdout.flush()
                return key
            except Exception as e:
                print(f"   ⚠️ Key fetch attempt {attempt+1} failed: {e}")
                sys.stdout.flush()
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    print(f"   ✗ Key fetch failed after {max_retries} attempts")
                    sys.stdout.flush()
                    raise
    
    def decrypt_segment(self, data, key, iv):
        """Decrypt AES-128 encrypted segment"""
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(data)
        # Remove PKCS7 padding only if it looks valid
        if len(decrypted) > 0:
            pad_len = decrypted[-1]
            if isinstance(pad_len, int) and 1 <= pad_len <= 16:
                # Verify padding is valid
                if all(b == pad_len for b in decrypted[-pad_len:]):
                    return decrypted[:-pad_len]
        return decrypted
    
    def download_segment(self, args):
        index, url, output_path, key_info, m3u8_url, base_url = args
        
        # RESUME: Skip if already downloaded and valid
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            if size > 0:
                return index, True, size, False  # success, no 403
        
        # Apply adaptive rate limiting if needed (only if significant)
        if self.rate_limit_delay > 0.15:  # Increased threshold from 0.1 to 0.15
            time.sleep(self.rate_limit_delay * 0.2)  # Apply only 20% of the delay (was 30%)
        
        for attempt in range(3):
            try:
                if attempt > 0:
                    # Minimal backoff on retries
                    time.sleep(0.2 * attempt)  # 0.2s, 0.4s instead of 0.5s, 1s, 2s
                    
                    # Refresh URL on retry (only on second retry)
                    if attempt == 2:
                        try:
                            fresh_playlist = m3u8.load(m3u8_url, headers=self.session.headers, timeout=30)
                            if fresh_playlist.segments and index < len(fresh_playlist.segments):
                                fresh_seg = fresh_playlist.segments[index]
                                url = base_url + fresh_seg.uri if not fresh_seg.uri.startswith('http') else fresh_seg.uri
                        except Exception as e:
                            # Silently fail - URL refresh is optional and 403 is expected
                            pass
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                data = response.content
                
                if len(data) == 0:
                    raise ValueError("Empty segment")
                
                # Decrypt if needed
                if key_info:
                    key, iv = key_info
                    data = self.decrypt_segment(data, key, iv)
                
                # Atomic write
                temp_path = output_path + '.tmp'
                with open(temp_path, 'wb') as f:
                    f.write(data)
                os.replace(temp_path, output_path)
                
                return index, True, len(data), False  # success, no 403
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    if attempt < 2:
                        time.sleep(0.3)  # Reduced from 1s to 0.3s
                        continue
                    return index, False, 0, True  # failed with 403
                elif attempt < 2:
                    time.sleep(0.2)  # Reduced from 0.5s to 0.2s
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.2)  # Reduced from 0.5s to 0.2s
        
        return index, False, 0, False  # failed, no 403
    
    def save_progress(self, temp_dir, downloaded_count, total_count):
        """Save download progress for resume"""
        progress_file = os.path.join(temp_dir, '.progress.json')
        try:
            with open(progress_file, 'w') as f:
                json.dump({
                    'downloaded': downloaded_count,
                    'total': total_count,
                    'timestamp': time.time()
                }, f)
        except Exception as e:
            print(f"   ⚠️ Could not save progress: {e}")
            pass
    
    def load_progress(self, temp_dir):
        """Load previous download progress"""
        progress_file = os.path.join(temp_dir, '.progress.json')
        try:
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"   ⚠️ Could not load progress: {e}")
            pass
        return None
    
    def cleanup_temp_dir(self, temp_dir):
        """Clean up temporary directory"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"   🗑️ Cleaned up temp directory")
                sys.stdout.flush()
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")
            sys.stdout.flush()
    
    def download(self, m3u8_url, output_file, code):
        print(f"\nDOWNLOADING WITH DECRYPTION: {code}")
        print("="*60)
        
        # Validate M3U8 URL
        if not m3u8_url or not isinstance(m3u8_url, str):
            print(f"ERROR: Invalid M3U8 URL")
            return False
        
        if not m3u8_url.startswith('http'):
            print(f"ERROR: M3U8 URL must start with http/https")
            return False
        
        # Increased limit from 2000 to 3000
        if len(m3u8_url) > 3000:
            print(f"ERROR: M3U8 URL suspiciously long ({len(m3u8_url)} chars)")
            return False
        
        start_time = time.time()
        
        # Ensure output is .ts format (will be converted to MP4 later)
        if not output_file.endswith('.ts'):
            output_file = output_file.rsplit('.', 1)[0] + '.ts'
        
        temp_dir = output_file + '_segments'
        
        try:
            # Parse M3U8
            print(f"Parsing M3U8...")
            try:
                playlist = m3u8.load(m3u8_url, headers=self.session.headers, timeout=30)
            except requests.exceptions.Timeout:
                print(f"ERROR: M3U8 request timed out")
                return False
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Failed to fetch M3U8: {e}")
                return False
            except Exception as e:
                print(f"ERROR: Failed to parse M3U8: {e}")
                return False
            
            base_url = m3u8_url.rsplit('/', 1)[0] + '/'
            
            # Handle master playlist - try alternatives if best quality fails
            if playlist.playlists:
                # Sort by bandwidth (best first)
                sorted_playlists = sorted(playlist.playlists, 
                                        key=lambda p: p.stream_info.bandwidth or 0, 
                                        reverse=True)
                
                print(f"   Found {len(sorted_playlists)} quality variants:")
                for idx, pl in enumerate(sorted_playlists):
                    bandwidth_mbps = (pl.stream_info.bandwidth or 0) / 1_000_000
                    resolution = f"{pl.stream_info.resolution[0]}x{pl.stream_info.resolution[1]}" if pl.stream_info.resolution else "unknown"
                    print(f"      #{idx+1}: {bandwidth_mbps:.1f} Mbps ({resolution})")
                
                media_url = None
                for idx, pl in enumerate(sorted_playlists):
                    try:
                        test_url = base_url + pl.uri if not pl.uri.startswith('http') else pl.uri
                        bandwidth_mbps = (pl.stream_info.bandwidth or 0) / 1_000_000
                        resolution = f"{pl.stream_info.resolution[0]}x{pl.stream_info.resolution[1]}" if pl.stream_info.resolution else "unknown"
                        print(f"   Trying quality #{idx+1}: {bandwidth_mbps:.1f} Mbps ({resolution})")
                        playlist = m3u8.load(test_url, headers=self.session.headers, timeout=30)
                        media_url = test_url
                        base_url = media_url.rsplit('/', 1)[0] + '/'
                        print(f"   ✅ Using HIGHEST quality: {bandwidth_mbps:.1f} Mbps ({resolution})")
                        break
                    except Exception as e:
                        print(f"   ⚠️ Quality #{idx+1} failed: {e}")
                        if idx < len(sorted_playlists) - 1:
                            print(f"   Trying next quality...")
                            continue
                        else:
                            raise
                
                if not media_url:
                    print(f"   ❌ All quality variants failed!")
                    return False
            
            segments = playlist.segments
            total = len(segments)
            
            if total == 0:
                print(f"   ❌ No segments found in M3U8!")
                return False
            
            if total > 10000:
                print(f"   ⚠️ Warning: Very large number of segments ({total})")
                print(f"   This may take a very long time or fail")
            
            print(f"   Segments: {total}")
            
            # Estimate size (rough: 800KB per segment average)
            estimated_size = total * 800 * 1024
            has_space, available, required = self.check_disk_space(estimated_size)
            if not has_space:
                print(f"   ❌ Insufficient disk space!")
                print(f"      Available: {available / (1024**3):.2f} GB")
                print(f"      Required: {required / (1024**3):.2f} GB")
                return False
            
            # Get media sequence start (for IV calculation)
            media_sequence_start = playlist.media_sequence if hasattr(playlist, 'media_sequence') else 0
            
            # Check for encryption and fetch key once
            has_keys = playlist.keys and playlist.keys[0]
            encryption_key = None
            if has_keys:
                print(f"   Encryption: AES-128 (will decrypt)")
                sys.stdout.flush()
                # Fetch the key once before processing segments
                try:
                    key_uri = playlist.keys[0].uri
                    encryption_key = self.get_key(key_uri, base_url)
                except Exception as e:
                    print(f"   ERROR: Failed to fetch encryption key: {e}")
                    sys.stdout.flush()
                    return False
            
            os.makedirs(temp_dir, exist_ok=True)
            
            # Check for previous progress
            prev_progress = self.load_progress(temp_dir)
            if prev_progress:
                print(f"   📂 Found previous download: {prev_progress['downloaded']}/{prev_progress['total']} segments")
                sys.stdout.flush()
            
            print(f"\n   Preparing {total} download tasks...")
            sys.stdout.flush()
            
            # Prepare tasks with decryption info and m3u8 URL for refresh
            tasks = []
            for i, seg in enumerate(segments):
                url = base_url + seg.uri if not seg.uri.startswith('http') else seg.uri
                path = os.path.join(temp_dir, f'seg_{i:05d}.ts')
                
                # Get key and IV for this segment
                key_info = None
                if seg.key and seg.key.method == 'AES-128':
                    # Use the pre-fetched key
                    key = encryption_key if encryption_key else self.get_key(seg.key.uri, base_url)
                    # IV handling: use explicit IV if provided, otherwise use media sequence number
                    if seg.key.iv:
                        # Remove '0x' prefix and convert hex to bytes
                        iv = bytes.fromhex(seg.key.iv[2:] if seg.key.iv.startswith('0x') else seg.key.iv)
                    else:
                        # Use media sequence number as IV (big-endian, 16 bytes)
                        sequence = media_sequence_start + i
                        iv = sequence.to_bytes(16, byteorder='big')
                    key_info = (key, iv)
                
                # Include m3u8_url and base_url for URL refresh on 403 errors
                tasks.append((i, url, path, key_info, m3u8_url, base_url))
            
            print(f"   ✓ Tasks prepared, starting download...")
            sys.stdout.flush()
            
            print(f"\nDownloading and decrypting...")
            print("="*60)
            sys.stdout.flush()
            
            downloaded = 0
            failed = []
            total_bytes = 0
            last_print = 0
            last_save = 0
            error_403_count = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.download_segment, t): t for t in tasks}
                for future in as_completed(futures):
                    idx, success, size, got_403 = future.result()
                    
                    if success:
                        downloaded += 1
                        total_bytes += size
                        
                        # Reset 403 counter on success (faster recovery)
                        if error_403_count > 0:
                            error_403_count = max(0, error_403_count - 3)  # Decrease by 3 instead of 2
                            self.rate_limit_delay = max(0, self.rate_limit_delay - 0.08)  # Much faster recovery
                        
                        current_time = time.time()
                        
                        # Update progress every 100 segments or 10 seconds (less frequent updates)
                        if downloaded % 100 == 0 or (current_time - last_print) >= 10:
                            progress = (downloaded / total) * 100
                            elapsed = current_time - start_time
                            speed = (total_bytes / (1024*1024)) / elapsed if elapsed > 0 else 0
                            bar = '#' * int(40 * progress / 100) + '-' * (40 - int(40 * progress / 100))
                            
                            # Show rate limit status if active
                            status = f" [throttled {self.rate_limit_delay:.2f}s]" if self.rate_limit_delay > 0 else ""
                            sys.stdout.write(f"\r[{bar}] {progress:.1f}% | {downloaded}/{total} | {speed:.1f} MB/s{status}")
                            sys.stdout.flush()
                            last_print = current_time
                        
                        # Save progress periodically
                        if downloaded % 100 == 0 or (current_time - last_save) >= 30:
                            self.save_progress(temp_dir, downloaded, total)
                            last_save = current_time
                    else:
                        failed.append(idx)
                        
                        # Adaptive rate limiting on 403 errors
                        if got_403:
                            error_403_count += 1
                            if error_403_count >= 12:  # Increased threshold from 10 to 12
                                # Too many 403s, slow down slightly
                                self.rate_limit_delay = min(0.15, self.rate_limit_delay + 0.015)  # Reduced from 0.2s max to 0.15s
                                error_403_count = 0  # Reset counter
            
            print("\n" + "="*60)
            
            # Check for massive failure rate (>50%) - indicates connection/browser issue
            if failed:
                failure_rate = len(failed) / total
                print(f"\n\nInitial failure: {len(failed)}/{total} segments ({failure_rate*100:.1f}%)")
                sys.stdout.flush()
                
                # If >50% failed on first attempt, likely a browser/connection issue
                # Return immediately to trigger browser restart
                if failure_rate > 0.5:
                    print(f"   ⚠️ HIGH FAILURE RATE ({failure_rate*100:.1f}%) - Browser restart needed")
                    print(f"   💾 Progress saved: {downloaded}/{total} segments")
                    sys.stdout.flush()
                    self.save_progress(temp_dir, downloaded, total)
                    return False
                
                # Normal retry logic for lower failure rates
                print(f"Retrying {len(failed)} failed segments...")
                sys.stdout.flush()
                
                # Reset rate limiting for retries
                self.rate_limit_delay = 0
                
                for retry_attempt in range(7):  # Increased from 5 to 7 retries for <50% failures
                    if not failed:
                        break
                    
                    print(f"   Retry {retry_attempt + 1}/7: {len(failed)} segments...")
                    sys.stdout.flush()
                    
                    still_failed = []
                    retry_tasks = [tasks[idx] for idx in failed]
                    
                    # Use more workers for retries
                    retry_workers = min(16, self.max_workers)
                    with ThreadPoolExecutor(max_workers=retry_workers) as executor:
                        retry_futures = {executor.submit(self.download_segment, t): t for t in retry_tasks}
                        for future in as_completed(retry_futures):
                            idx, success, size, got_403 = future.result()
                            if success:
                                downloaded += 1
                                total_bytes += size
                            else:
                                still_failed.append(idx)
                    
                    failed = still_failed
                    
                    # Check if failure rate is still too high after retry
                    if failed:
                        current_failure_rate = len(failed) / total
                        if current_failure_rate > 0.5 and retry_attempt >= 2:
                            print(f"   ⚠️ Failure rate still high ({current_failure_rate*100:.1f}%) after {retry_attempt+1} retries")
                            print(f"   💾 Saving progress and requesting browser restart...")
                            sys.stdout.flush()
                            self.save_progress(temp_dir, downloaded, total)
                            return False
                    
                    if failed and retry_attempt < 6:
                        wait_time = min(1 + retry_attempt, 8)  # Progressive wait: 1s, 2s, 3s, 4s, 5s, 6s, 7s
                        print(f"   {len(failed)} still failing, waiting {wait_time}s...")
                        sys.stdout.flush()
                        time.sleep(wait_time)
                
                if failed:
                    print(f"   ✗ {len(failed)} segments permanently failed after 7 attempts")
                    sys.stdout.flush()
            
                # Check if we got all segments
            if downloaded < total:
                missing = total - downloaded
                print(f"   ⚠️ Warning: Missing {missing}/{total} segments ({missing/total*100:.1f}%)")
                sys.stdout.flush()
                
                # If ANY segments missing, fail the download (was 2% threshold)
                # We need complete videos for quality
                print(f"   ❌ Incomplete download ({missing} segments missing), download failed")
                sys.stdout.flush()
                return False
            
            # Merge
            print(f"\nMerging {downloaded} segments...")
            if not self.merge(temp_dir, output_file, total):
                return False
            
            # Cleanup
            print(f"Cleaning up...")
            self.cleanup_temp_dir(temp_dir)
            
            total_time = time.time() - start_time
            size = os.path.getsize(output_file) / (1024**3)
            print(f"\nCOMPLETE! {size:.2f} GB in {int(total_time//60)}m {int(total_time%60)}s")
            return True
            
        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't cleanup on failure - allow resume
            print(f"\n   💾 Temp files preserved for resume: {temp_dir}")
            return False
    
    def merge(self, temp_dir, output, total):
        """Merge decrypted segments into TS file"""
        try:
            segments = sorted(glob.glob(os.path.join(temp_dir, "seg_*.ts")))
            
            if len(segments) == 0:
                print(f"   ❌ No segments found to merge!")
                return False
            
            if len(segments) < total:
                print(f"   ⚠️ Warning: Expected {total} segments, found {len(segments)}")
            
            # Validate segments before merging
            invalid_segments = []
            for seg_path in segments:
                if os.path.getsize(seg_path) == 0:
                    invalid_segments.append(seg_path)
            
            if invalid_segments:
                print(f"   ⚠️ Warning: {len(invalid_segments)} empty segments found")
                # Remove empty segments
                for seg_path in invalid_segments:
                    segments.remove(seg_path)
            
            with open(output, 'wb') as outfile:
                for i, seg_path in enumerate(segments):
                    if (i + 1) % 200 == 0:
                        print(f"      Progress: {i+1}/{len(segments)}")
                    
                    with open(seg_path, 'rb') as infile:
                        outfile.write(infile.read())
            
            if os.path.exists(output):
                size = os.path.getsize(output) / (1024**3)
                print(f"   SUCCESS: {size:.2f} GB")
                return True
            return False
        except Exception as e:
            print(f"   ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


# Test
if __name__ == "__main__":
    print("="*60)
    print("  HLS DOWNLOADER V2 WITH AES DECRYPTION")
    print("="*60)
    
    # Load videos
    with open('database/videos.json', 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    video = videos[0]
    code = video['code']
    m3u8_url = video['m3u8_url']
    
    print(f"\nVideo: {code}")
    print(f"M3U8: {m3u8_url[:80]}...")
    
    # Download
    output = f"temp_downloads/{code}.ts"
    os.makedirs("temp_downloads", exist_ok=True)
    
    downloader = HLSDownloaderV2(MAX_WORKERS)
    if downloader.download(m3u8_url, output, code):
        print(f"\n{'='*60}")
        print(f"SUCCESS! Video saved to: {output}")
        print(f"Size: {os.path.getsize(output) / (1024**3):.2f} GB")
    else:
        print("\nERROR: Download failed")
