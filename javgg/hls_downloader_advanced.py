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

# Optimal default based on CDN analysis
# Note: CDN throttles heavily (~0.1-0.2 MB/s) regardless of worker count
# 18 workers provides best balance between speed and avoiding detection
DEFAULT_WORKERS = 32

class AdvancedHLSDownloader:
    def __init__(self, max_workers=DEFAULT_WORKERS):
        self.max_workers = max_workers
        
        # Multiple user agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
        # Create multiple sessions for connection pooling - optimized for 32 workers
        self.sessions = []
        # Create 8 sessions (4 workers per session)
        for i in range(8):
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=max_workers,
                pool_maxsize=max_workers,
                max_retries=0  # We handle retries manually
            )
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            self.sessions.append(session)
        
        self.rate_limit_delay = 0
        self.consecutive_403s = 0
        self.slow_speed_detected = False
        self.request_count = 0
    
    def get_session(self):
        """Get a session in round-robin fashion"""
        session = self.sessions[self.request_count % len(self.sessions)]
        self.request_count += 1
        return session
    
    def get_headers(self):
        """Get headers with rotating user agent"""
        return {
            'Referer': 'https://javgg.net/',
            'User-Agent': random.choice(self.user_agents),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
        }
    
    def download_segment(self, args):
        """Download a single segment with anti-throttling"""
        index, url, output_path, m3u8_url, base_url = args
        
        # RESUME: Skip if already downloaded and valid
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            if size > 0:
                return index, True, size, False
        
        # Small random delay to avoid burst detection (0-50ms)
        time.sleep(random.uniform(0, 0.05))
        
        # Get session and headers
        session = self.get_session()
        headers = self.get_headers()
        
        for attempt in range(3):
            try:
                if attempt > 0:
                    # Exponential backoff with jitter
                    delay = (0.5 * (2 ** attempt)) + random.uniform(0, 0.5)
                    time.sleep(delay)
                
                # Make request with timeout
                response = session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.content
                
                if len(data) == 0:
                    raise ValueError("Empty segment")
                
                # Atomic write
                temp_path = output_path + '.tmp'
                with open(temp_path, 'wb') as f:
                    f.write(data)
                os.replace(temp_path, output_path)
                
                return index, True, len(data), False
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    # 403 - try different session and user agent
                    if attempt < 2:
                        session = self.get_session()
                        headers = self.get_headers()
                        time.sleep(random.uniform(0.5, 1.5))
                        continue
                    return index, False, 0, True
                elif e.response.status_code == 429:
                    # 429 Too Many Requests - back off more
                    if attempt < 2:
                        time.sleep(random.uniform(2, 5))
                        continue
                    return index, False, 0, True
                elif attempt < 2:
                    time.sleep(0.3)
            except requests.exceptions.Timeout:
                if attempt < 2:
                    time.sleep(0.5)
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.3)
        
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
        """Download with anti-throttling techniques"""
        print(f"\n📥 Advanced HLS Downloader ({self.max_workers} workers + anti-throttling)")
        
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
            session = self.get_session()
            response = session.get(m3u8_url, headers=self.get_headers(), timeout=30)
            response.raise_for_status()
            playlist = m3u8.loads(response.text, uri=m3u8_url)
            
            base_url = m3u8_url.rsplit('/', 1)[0] + '/'
            
            # Handle master playlist
            if playlist.playlists:
                sorted_playlists = sorted(playlist.playlists, 
                                        key=lambda p: p.stream_info.bandwidth or 0, 
                                        reverse=True)
                
                print(f"  📊 Found {len(sorted_playlists)} quality variants")
                
                best = sorted_playlists[0]
                bandwidth_mbps = (best.stream_info.bandwidth or 0) / 1_000_000
                resolution = f"{best.stream_info.resolution[0]}x{best.stream_info.resolution[1]}" if best.stream_info.resolution else "unknown"
                print(f"  🎬 Using BEST quality: {bandwidth_mbps:.1f} Mbps ({resolution})")
                
                media_url = base_url + best.uri if not best.uri.startswith('http') else best.uri
                response = session.get(media_url, headers=self.get_headers(), timeout=30)
                response.raise_for_status()
                playlist = m3u8.loads(response.text, uri=media_url)
                base_url = media_url.rsplit('/', 1)[0] + '/'
            
            segments = playlist.segments
            total = len(segments)
            
            if total == 0:
                print(f"  ❌ No segments found!")
                return False
            
            print(f"  📦 Total segments: {total}")
            print(f"  🚀 Using {self.max_workers} parallel workers with anti-throttling")
            print(f"  🔄 Rotating between {len(self.sessions)} sessions and {len(self.user_agents)} user agents")
            
            os.makedirs(temp_dir, exist_ok=True)
            
            # Check for previous progress
            prev_progress = self.load_progress(temp_dir)
            if prev_progress:
                print(f"  📂 Resuming: {prev_progress['downloaded']}/{prev_progress['total']} segments")
            
            # Prepare tasks
            tasks = []
            for i, seg in enumerate(segments):
                url = base_url + seg.uri if not seg.uri.startswith('http') else seg.uri
                path = os.path.join(temp_dir, f'seg_{i:05d}.ts')
                tasks.append((i, url, path, m3u8_url, base_url))
            
            print(f"  ⚡ Starting download...")
            
            downloaded = 0
            failed = []
            total_bytes = 0
            last_print = 0
            last_save = 0
            error_403_count = 0
            bar_width = 50
            
            # Download with thread pool
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.download_segment, t): t for t in tasks}
                for future in as_completed(futures):
                    idx, success, size, got_403 = future.result()
                    
                    if success:
                        downloaded += 1
                        total_bytes += size
                        
                        if error_403_count > 0:
                            error_403_count = max(0, error_403_count - 2)
                        
                        current_time = time.time()
                        
                        # Update progress every 25 segments or 3 seconds
                        if downloaded % 25 == 0 or (current_time - last_print) >= 3:
                            progress = (downloaded / total) * 100
                            elapsed = current_time - start_time
                            speed = (total_bytes / (1024*1024)) / elapsed if elapsed > 0 else 0
                            
                            # THROTTLING CHECK: If speed is too low after 30 seconds
                            if elapsed > 30 and speed < 0.5:
                                print(f"\n  ⚠️ Throttling detected! Speed: {speed:.2f} MB/s (Threshold: 0.5 MB/s)")
                                print(f"  🛑 Aborting download to trigger restart...")
                                return False
                            
                            filled = int(bar_width * progress / 100)
                            bar = '█' * filled + '░' * (bar_width - filled)
                            
                            # Calculate ETA
                            if speed > 0:
                                remaining_segments = total - downloaded
                                avg_segment_size = total_bytes / downloaded
                                remaining_bytes = remaining_segments * avg_segment_size
                                eta_seconds = remaining_bytes / (speed * 1024 * 1024)
                                eta_min = int(eta_seconds // 60)
                                eta_sec = int(eta_seconds % 60)
                                
                                if eta_min >= 60:
                                    eta_hours = eta_min // 60
                                    eta_min = eta_min % 60
                                    eta_str = f"ETA {eta_hours}h{eta_min}m"
                                else:
                                    eta_str = f"ETA {eta_min}:{eta_sec:02d}"
                            else:
                                eta_str = "ETA --:--"
                            
                            status = f"\r  [{bar}] {progress:.1f}% | {downloaded}/{total} | {speed:.1f} MB/s | {eta_str}"
                            sys.stdout.write(status)
                            sys.stdout.flush()
                            last_print = current_time
                        
                        # Save progress
                        if downloaded % 100 == 0 or (current_time - last_save) >= 30:
                            self.save_progress(temp_dir, downloaded, total)
                            last_save = current_time
                    else:
                        failed.append(idx)
                        if got_403:
                            error_403_count += 1
            
            # Clear progress line
            sys.stdout.write(f"\r{' ' * 120}\r")
            sys.stdout.flush()
            
            # Handle failures
            if failed:
                failure_rate = len(failed) / total
                print(f"  ⚠️ Initial failure: {len(failed)}/{total} segments ({failure_rate*100:.1f}%)")
                
                if failure_rate > 0.5:
                    print(f"  ❌ HIGH FAILURE RATE - Connection issue")
                    self.save_progress(temp_dir, downloaded, total)
                    return False
                
                # Retry with more aggressive anti-throttling
                print(f"  🔄 Retrying {len(failed)} failed segments with enhanced anti-throttling...")
                
                for retry_attempt in range(5):
                    if not failed:
                        break
                    
                    still_failed = []
                    retry_tasks = [tasks[idx] for idx in failed]
                    
                    # Use fewer workers for retries to avoid triggering throttling
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
                    
                    if failed and retry_attempt < 4:
                        wait_time = min(2 + retry_attempt, 5)
                        print(f"  ⏳ {len(failed)} still failing, waiting {wait_time}s...")
                        time.sleep(wait_time)
            
            # Check completion
            if downloaded < total:
                missing = total - downloaded
                print(f"  ❌ Missing {missing}/{total} segments ({missing/total*100:.1f}%)")
                return False
            
            # Merge
            print(f"  🔗 Merging {downloaded} segments...")
            if not self.merge(temp_dir, str(temp_output), total):
                return False
            
            # Convert to MP4
            if temp_output != output_path:
                print(f"  🎬 Converting to MP4...")
                try:
                    import subprocess
                    cmd = [
                        'ffmpeg',
                        '-i', str(temp_output),
                        '-c', 'copy',
                        '-y',
                        str(output_path)
                    ]
                    result = subprocess.run(cmd, capture_output=True, timeout=300)
                    if result.returncode == 0:
                        temp_output.unlink()
                    else:
                        output_path = temp_output
                except:
                    output_path = temp_output
            
            # Cleanup
            self.cleanup_temp_dir(temp_dir)
            
            total_time = time.time() - start_time
            size = os.path.getsize(output_path) / (1024**3)
            avg_speed = (os.path.getsize(output_path) / (1024*1024)) / total_time
            print(f"  ✅ Complete! {size:.2f} GB in {int(total_time//60)}m {int(total_time%60)}s")
            print(f"  📊 Average speed: {avg_speed:.1f} MB/s")
            return True
            
        except Exception as e:
            print(f"  ❌ Download failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def merge(self, temp_dir, output, total):
        """Merge segments"""
        try:
            segments = sorted(glob.glob(os.path.join(temp_dir, "seg_*.ts")))
            
            if len(segments) == 0:
                print(f"  ❌ No segments to merge!")
                return False
            
            with open(output, 'wb') as outfile:
                for i, seg_path in enumerate(segments):
                    if (i + 1) % 200 == 0:
                        print(f"  Progress: {i+1}/{len(segments)}")
                    with open(seg_path, 'rb') as infile:
                        outfile.write(infile.read())
            
            return os.path.exists(output)
        except Exception as e:
            print(f"  ❌ Merge error: {e}")
            return False


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
