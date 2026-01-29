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
    def __init__(self, max_workers=32):
        self.max_workers = max_workers
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_workers * 2,  # Increased pool for high concurrency
            pool_maxsize=max_workers * 2,
            max_retries=3
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
    
    def download_segment(self, args):
        """Download a single segment"""
        index, url, output_path, m3u8_url, base_url = args
        
        # RESUME: Skip if already downloaded and valid
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            if size > 0:
                return index, True, size, False
        
        # Adaptive rate limiting
        if self.rate_limit_delay > 0.1:
            time.sleep(self.rate_limit_delay * 0.5)
        
        # Retry loop
        for attempt in range(3):
            try:
                if attempt > 0:
                    time.sleep(0.2 * attempt)
                    
                    # Optional: Refresh URL logic could go here if links expire
                
                response = self.session.get(url, timeout=30)
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
                    if attempt < 2:
                        time.sleep(0.2)
                        continue
                    return index, False, 0, True  # 403 error
                elif attempt < 2:
                    time.sleep(0.1)
            except Exception as e:
                # Connection errors etc
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
            
            # ThreadPool execution
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.download_segment, t): t for t in tasks}
                for future in as_completed(futures):
                    idx, success, size, got_403 = future.result()
                    
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
                
                # Simple retry loop for remaining items
                retry_tasks = [tasks[i] for i in failed]
                still_failed = []
                with ThreadPoolExecutor(max_workers=16) as executor:
                    futures = {executor.submit(self.download_segment, t): t for t in retry_tasks}
                    for future in as_completed(futures):
                        idx, success, size, _ = future.result()
                        if success:
                            downloaded += 1
                        else:
                            still_failed.append(idx)
                
                if still_failed:
                    print(f"  ❌ {len(still_failed)} segments failed after retry.")
                    return False

            # Merge
            print(f"  🔗 Merging {downloaded} segments...")
            if not self.merge(temp_dir, str(temp_output), total):
                return False
            
            # Convert
            if temp_output != output_path:
                print(f"  🎬 Converting to MP4...")
                try:
                    import subprocess
                    cmd = ['ffmpeg', '-i', str(temp_output), '-c', 'copy', '-y', str(output_path)]
                    subprocess.run(cmd, capture_output=True, timeout=300)
                    temp_output.unlink()
                except:
                    output_path = temp_output
            
            self.cleanup_temp_dir(temp_dir)
            total_time = time.time() - start_time
            size_gb = os.path.getsize(output_path) / (1024**3)
            print(f"  ✅ Complete! {size_gb:.2f} GB in {int(total_time)}s")
            return True

        except Exception as e:
            print(f"  ❌ Download Error: {e}")
            return False

    def merge(self, temp_dir, output, total):
        try:
            segments = sorted(glob.glob(os.path.join(temp_dir, "seg_*.ts")))
            if not segments: return False
            with open(output, 'wb') as outfile:
                for seg in segments:
                    with open(seg, 'rb') as infile:
                        outfile.write(infile.read())
            return True
        except:
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
