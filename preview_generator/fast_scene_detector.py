#!/usr/bin/env python3
"""
Ultra-Fast Scene Detector using Parallel Processing
Analyzes video segments in parallel for maximum speed
"""
import subprocess
import re
import json
import concurrent.futures
from typing import List, Tuple
from multiprocessing import cpu_count

class FastSceneDetector:
    """Fast parallel scene detection"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.duration = None
        self.width = None
        self.height = None
        self.fps = None
        
    def get_video_info(self) -> dict:
        """Get video metadata quickly"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                self.video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = next(
                (s for s in data['streams'] if s['codec_type'] == 'video'),
                None
            )
            
            if video_stream:
                self.duration = float(data['format']['duration'])
                self.width = int(video_stream['width'])
                self.height = int(video_stream['height'])
                
                # Parse FPS
                fps_str = video_stream.get('r_frame_rate', '30/1')
                num, den = map(int, fps_str.split('/'))
                self.fps = num / den if den != 0 else 30.0
                
                return {
                    'duration': self.duration,
                    'width': self.width,
                    'height': self.height,
                    'fps': self.fps
                }
        except Exception as e:
            print(f"[FastSceneDetector] Error getting video info: {e}")
            return None
    
    def detect_scenes_fast(self, num_clips: int = 10, threshold: float = 0.3) -> List[float]:
        """
        Ultra-fast scene detection using parallel segment analysis
        
        Args:
            num_clips: Number of clips needed
            threshold: Scene detection sensitivity
            
        Returns:
            List of timestamps with interesting scenes
        """
        if not self.duration:
            self.get_video_info()
        
        print(f"[FastSceneDetector] Analyzing video ({self.duration/60:.1f} minutes)...")
        
        # Strategy: Analyze strategic segments in parallel
        # For long videos, sample more segments than needed
        num_samples = num_clips * 3  # Analyze 3x more segments than needed
        
        # Calculate sample points (evenly distributed, skip first/last 5%)
        start_offset = self.duration * 0.05
        end_offset = self.duration * 0.95
        usable_duration = end_offset - start_offset
        
        interval = usable_duration / num_samples
        sample_points = [start_offset + (i * interval) for i in range(num_samples)]
        
        print(f"[FastSceneDetector] Analyzing {num_samples} segments in parallel...")
        
        # Analyze all segments in parallel
        max_workers = min(cpu_count(), 32)  # Use up to 32 threads
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_timestamp = {
                executor.submit(self._analyze_segment_fast, timestamp, 3.0, threshold): timestamp
                for timestamp in sample_points
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_timestamp, timeout=60):
                timestamp = future_to_timestamp[future]
                try:
                    score = future.result()
                    if score > 0:
                        results.append((timestamp, score))
                except Exception as e:
                    print(f"[FastSceneDetector] Segment analysis failed: {e}")
        
        # Sort by score (highest first) and take top N
        results.sort(key=lambda x: x[1], reverse=True)
        timestamps = [t for t, s in results[:num_clips]]
        timestamps.sort()  # Sort chronologically
        
        print(f"[FastSceneDetector] Selected {len(timestamps)} best scenes")
        return timestamps
    
    def _analyze_segment_fast(self, start_time: float, duration: float, threshold: float) -> float:
        """
        Quickly analyze a segment for scene quality
        Returns a score (higher = better scene)
        """
        try:
            # Use a simpler approach: check frame difference
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', self.video_path,
                '-t', str(duration),
                '-vf', 'select=gt(scene\\,0.2),metadata=print:file=-',
                '-an',
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Count frames selected (indicates scene activity)
            frame_count = result.stderr.count('frame:')
            
            # Also give points for being in the middle of the video (more interesting)
            middle_bonus = 1.0 - abs((start_time / self.duration) - 0.5) * 2
            
            # Higher score = more scene activity + position bonus
            return float(frame_count) + middle_bonus
            
        except Exception:
            # If analysis fails, return position-based score
            return 1.0 - abs((start_time / self.duration) - 0.5) * 2
    
    def get_smart_timestamps(self, num_clips: int = 10) -> List[float]:
        """
        Get smart timestamps without scene detection (fastest method)
        Uses strategic sampling with slight randomization
        """
        if not self.duration:
            self.get_video_info()
        
        print(f"[FastSceneDetector] Calculating smart timestamps...")
        
        # Skip first and last 5%
        start_offset = self.duration * 0.05
        end_offset = self.duration * 0.95
        usable_duration = end_offset - start_offset
        
        # Divide into segments
        segment_duration = usable_duration / num_clips
        
        timestamps = []
        for i in range(num_clips):
            # Take timestamp from middle of each segment
            # Add slight offset to avoid repetitive patterns
            base_time = start_offset + (i * segment_duration)
            offset = segment_duration * 0.3  # 30% into each segment
            timestamp = base_time + offset
            timestamps.append(timestamp)
        
        print(f"[FastSceneDetector] Generated {len(timestamps)} timestamps")
        return timestamps


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fast_scene_detector.py <video_file>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    detector = FastSceneDetector(video_path)
    
    # Test fast detection
    import time
    start = time.time()
    
    timestamps = detector.detect_scenes_fast(num_clips=10)
    
    elapsed = time.time() - start
    
    print(f"\nResults:")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Timestamps: {[f'{t:.1f}s' for t in timestamps]}")
