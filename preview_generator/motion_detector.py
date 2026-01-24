#!/usr/bin/env python3
"""
Motion-Based Scene Detector for Adult Content
Finds high-motion/high-activity scenes using parallel processing
"""
import subprocess
import re
import json
import concurrent.futures
from typing import List, Tuple
from multiprocessing import cpu_count

class MotionDetector:
    """Detects high-motion scenes in parallel"""
    
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
            
            video_stream = next(
                (s for s in data['streams'] if s['codec_type'] == 'video'),
                None
            )
            
            if video_stream:
                self.duration = float(data['format']['duration'])
                self.width = int(video_stream['width'])
                self.height = int(video_stream['height'])
                
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
            print(f"[MotionDetector] Error getting video info: {e}")
            return None
    
    def find_high_motion_scenes(self, num_clips: int = 10, sample_size: int = 50) -> List[float]:
        """
        Find scenes with highest motion/activity
        
        Args:
            num_clips: Number of clips to return
            sample_size: Number of segments to analyze (more = better accuracy)
            
        Returns:
            List of timestamps with highest motion
        """
        if not self.duration:
            self.get_video_info()
        
        print(f"[MotionDetector] Analyzing motion in video ({self.duration/60:.1f} minutes)...")
        
        # Skip first and last 5% (intro/outro)
        start_offset = self.duration * 0.05
        end_offset = self.duration * 0.95
        usable_duration = end_offset - start_offset
        
        # Calculate sample points
        interval = usable_duration / sample_size
        sample_points = [start_offset + (i * interval) for i in range(sample_size)]
        
        print(f"[MotionDetector] Analyzing {sample_size} segments in parallel...")
        
        # Analyze all segments in parallel
        max_workers = min(cpu_count(), 32)
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_timestamp = {
                executor.submit(self._analyze_motion_segment, timestamp, 5.0): timestamp
                for timestamp in sample_points
            }
            
            for future in concurrent.futures.as_completed(future_to_timestamp, timeout=120):
                timestamp = future_to_timestamp[future]
                try:
                    motion_score = future.result()
                    if motion_score > 0:
                        results.append((timestamp, motion_score))
                except Exception as e:
                    print(f"[MotionDetector] Segment analysis failed at {timestamp:.1f}s: {e}")
        
        # Sort by motion score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Take top N with highest motion
        top_results = results[:num_clips]
        
        # Sort chronologically
        timestamps = sorted([t for t, s in top_results])
        
        print(f"[MotionDetector] Selected {len(timestamps)} high-motion scenes")
        print(f"[MotionDetector] Motion scores: {[f'{s:.1f}' for t, s in sorted(top_results, key=lambda x: x[0])]}")
        
        return timestamps
    
    def _analyze_motion_segment(self, start_time: float, duration: float) -> float:
        """
        Analyze motion intensity in a segment using frame statistics
        Returns motion score (higher = more motion/activity)
        """
        try:
            # Extract a few frames and analyze their complexity
            # More complex frames = more activity/motion
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', self.video_path,
                '-t', str(duration),
                '-vf', 'fps=2,scale=320:180',  # Sample 2 fps, downscale for speed
                '-f', 'rawvideo',
                '-pix_fmt', 'gray',
                'pipe:1'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=8
            )
            
            if not result.stdout:
                return 0
            
            # Calculate variance in pixel values (higher = more detail/motion)
            import numpy as np
            
            # Convert bytes to numpy array
            frame_data = np.frombuffer(result.stdout, dtype=np.uint8)
            
            if len(frame_data) == 0:
                return 0
            
            # Calculate standard deviation (measure of variation/activity)
            std_dev = np.std(frame_data)
            
            # Calculate mean (avoid very dark or very bright scenes)
            mean_val = np.mean(frame_data)
            
            # Penalize very dark or very bright scenes
            brightness_penalty = 1.0
            if mean_val < 30 or mean_val > 225:
                brightness_penalty = 0.5
            
            # Motion score based on variation and brightness
            motion_score = std_dev * brightness_penalty
            
            return float(motion_score)
            
        except subprocess.TimeoutExpired:
            return 0
        except Exception as e:
            # Fallback: use simpler method
            try:
                # Just count frames as a basic measure
                cmd = [
                    'ffprobe',
                    '-v', 'error',
                    '-ss', str(start_time),
                    '-t', str(duration),
                    '-count_frames',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=nb_read_frames',
                    '-of', 'default=nokey=1:noprint_wrappers=1',
                    self.video_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                frame_count = int(result.stdout.strip() or 0)
                
                # More frames = potentially more motion
                return float(frame_count)
            except:
                return 0
    
    def find_diverse_high_motion_scenes(self, num_clips: int = 10) -> List[float]:
        """
        Find high-motion scenes that are spread throughout the video
        Ensures good coverage of the entire video
        """
        if not self.duration:
            self.get_video_info()
        
        print(f"[MotionDetector] Finding diverse high-motion scenes...")
        
        # Divide video into sections
        num_sections = num_clips
        section_duration = self.duration / num_sections
        
        # Skip first and last 5%
        start_offset = self.duration * 0.05
        end_offset = self.duration * 0.95
        
        timestamps = []
        
        # Analyze 3 samples per section and pick the best
        max_workers = min(cpu_count(), 32)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(num_sections):
                section_start = start_offset + (i * section_duration)
                section_end = min(section_start + section_duration, end_offset)
                
                # Sample 3 points in this section
                sample_points = [
                    section_start + (section_duration * 0.25),
                    section_start + (section_duration * 0.50),
                    section_start + (section_duration * 0.75)
                ]
                
                # Analyze all samples in parallel
                futures = {
                    executor.submit(self._analyze_motion_segment, t, 5.0): t
                    for t in sample_points
                }
                
                # Find best sample in this section
                best_timestamp = sample_points[1]  # Default to middle
                best_score = 0
                
                for future in concurrent.futures.as_completed(futures, timeout=30):
                    timestamp = futures[future]
                    try:
                        score = future.result()
                        if score > best_score:
                            best_score = score
                            best_timestamp = timestamp
                    except:
                        pass
                
                timestamps.append(best_timestamp)
        
        print(f"[MotionDetector] Selected {len(timestamps)} diverse high-motion scenes")
        return timestamps


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python motion_detector.py <video_file>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    detector = MotionDetector(video_path)
    
    import time
    start = time.time()
    
    # Test motion detection
    timestamps = detector.find_high_motion_scenes(num_clips=10, sample_size=50)
    
    elapsed = time.time() - start
    
    print(f"\nResults:")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Timestamps: {[f'{t:.1f}s' for t in timestamps]}")
