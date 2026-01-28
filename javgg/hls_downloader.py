#!/usr/bin/env python3
"""
HLS Downloader for JavaGG videos
Uses m3u8 library like jable for proper HLS handling
"""
import os
import sys
import time
import requests
import m3u8
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

class JavaGGHLSDownloader:
    """Download HLS streams from JavaGG"""
    
    def __init__(self, max_workers=16):
        self.max_workers = max_workers
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_workers * 2,
            pool_maxsize=max_workers * 2,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_segment(self, segment_url, segment_num, total_segments):
        """Download a single segment"""
        try:
            response = self.session.get(segment_url, timeout=30)
            response.raise_for_status()
            return segment_num, response.content, None
        except Exception as e:
            return segment_num, None, str(e)
    
    def download(self, m3u8_url, output_file):
        """Download HLS stream to file"""
        print(f"  📥 Downloading HLS stream...")
        
        try:
            # Parse M3U8
            print(f"     Parsing M3U8...")
            playlist = m3u8.load(m3u8_url, headers=self.session.headers, timeout=30)
            
            base_url = m3u8_url.rsplit('/', 1)[0] + '/'
            
            # Handle master playlist
            if playlist.playlists:
                # Get best quality
                best = max(playlist.playlists, key=lambda p: p.stream_info.bandwidth or 0)
                media_url = base_url + best.uri if not best.uri.startswith('http') else best.uri
                playlist = m3u8.load(media_url, headers=self.session.headers, timeout=30)
                base_url = media_url.rsplit('/', 1)[0] + '/'
                print(f"     Using best quality")
            
            segments = playlist.segments
            total = len(segments)
            
            if total == 0:
                print(f"     ❌ No segments found")
                return False
            
            print(f"     Segments: {total}")
            
            # Download segments
            temp_dir = Path(output_file).parent / f"{Path(output_file).stem}_segments"
            temp_dir.mkdir(exist_ok=True)
            
            segment_files = []
            downloaded = 0
            
            print(f"     [{'░' * 50}] 0%", end='', flush=True)
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                
                for i, segment in enumerate(segments):
                    segment_url = base_url + segment.uri if not segment.uri.startswith('http') else segment.uri
                    future = executor.submit(self.download_segment, segment_url, i, total)
                    futures[future] = i
                
                for future in as_completed(futures):
                    segment_num, data, error = future.result()
                    
                    if error:
                        print(f"\n     ❌ Segment {segment_num} failed: {error}")
                        return False
                    
                    # Save segment
                    segment_file = temp_dir / f"segment_{segment_num:05d}.ts"
                    with open(segment_file, 'wb') as f:
                        f.write(data)
                    
                    segment_files.append((segment_num, segment_file))
                    downloaded += 1
                    
                    # Update progress bar
                    percent = int((downloaded / total) * 100)
                    filled = int((downloaded / total) * 50)
                    bar = '█' * filled + '░' * (50 - filled)
                    print(f"\r     [{bar}] {percent}%", end='', flush=True)
            
            print()  # New line after progress
            
            # Sort segments
            segment_files.sort(key=lambda x: x[0])
            
            # Concatenate segments using ffmpeg
            print(f"     Merging segments...")
            concat_file = temp_dir / "concat.txt"
            with open(concat_file, 'w') as f:
                for _, seg_file in segment_files:
                    f.write(f"file '{seg_file.absolute()}'\n")
            
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-y',
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            if result.returncode == 0 and os.path.exists(output_file):
                size_mb = os.path.getsize(output_file) / 1024 / 1024
                print(f"     ✅ Downloaded: {size_mb:.1f} MB")
                return True
            else:
                print(f"     ❌ Merge failed")
                return False
                
        except Exception as e:
            print(f"     ❌ Download failed: {str(e)}")
            return False
