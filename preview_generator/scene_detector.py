#!/usr/bin/env python3
"""
Advanced Scene Detection
Detects scene changes, motion intensity, and interesting moments with parallel processing
"""
import subprocess
import json
import re
from typing import List, Dict, Tuple
from multiprocessing import Pool, cpu_count
from functools import partial

class SceneDetector:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.duration = None
        self.scenes = []
        
    def get_video_info(self) -> Dict:
        """Get video metadata"""
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,r_frame_rate,duration',
                '-show_entries', 'format=duration',
                '-of', 'json',
                self.video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"[SceneDetector] FFprobe error: {result.stderr}")
                return None
            
            data = json.loads(result.stdout)
            
            # Get duration
            duration = None
            if 'format' in data and 'duration' in data['format']:
                duration = float(data['format']['duration'])
            elif 'streams' in data and len(data['streams']) > 0:
                if 'duration' in data['streams'][0]:
                    duration = float(data['streams'][0]['duration'])
            
            if not duration or duration <= 0:
                print(f"[SceneDetector] Invalid duration: {duration}")
                return None
            
            # Get dimensions
            width = data['streams'][0].get('width', 1920)
            height = data['streams'][0].get('height', 1080)
            
            # Get frame rate
            fps_str = data['streams'][0].get('r_frame_rate', '30/1')
            fps_parts = fps_str.split('/')
            fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0
            
            self.duration = duration
            
            return {
                'duration': duration,
                'width': width,
                'height': height,
                'fps': fps
            }
        except FileNotFoundError:
            print(f"[SceneDetector] Error: FFmpeg/FFprobe not found. Please install FFmpeg.")
            return None
        except json.JSONDecodeError as e:
            print(f"[SceneDetector] Error parsing ffprobe output: {e}")
            return None
        except Exception as e:
            print(f"[SceneDetector] Error getting video info: {e}")
            return None
    
    def detect_scenes(self, threshold: float = 0.4) -> List[Dict]:
        """
        Detect scene changes using FFmpeg
        
        Args:
            threshold: Scene change sensitivity (0.0-1.0, higher = less sensitive)
        
        Returns:
            List of scenes with timestamps
        """
        print(f"[SceneDetector] Detecting scenes (threshold={threshold})...")
        
        try:
            # Use FFmpeg scene detection filter
            cmd = [
                'ffmpeg', '-i', self.video_path,
                '-filter:v', f"select='gt(scene,{threshold})',showinfo",
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300
            )
            
            # Parse scene timestamps from stderr
            scenes = []
            for line in result.stderr.split('\n'):
                if 'pts_time' in line:
                    # Extract timestamp
                    match = re.search(r'pts_time:(\d+\.?\d*)', line)
                    if match:
                        timestamp = float(match.group(1))
                        scenes.append({
                            'timestamp': timestamp,
                            'type': 'scene_change'
                        })
            
            print(f"[SceneDetector] Found {len(scenes)} scene changes")
            self.scenes = scenes
            return scenes
            
        except Exception as e:
            print(f"[SceneDetector] Error detecting scenes: {e}")
            return []
    
    def analyze_motion(self, num_segments: int = 20, parallel: bool = True) -> List[Dict]:
        """
        Analyze motion intensity across video segments with parallel processing
        
        Args:
            num_segments: Number of segments to analyze
            parallel: Use parallel processing
        
        Returns:
            List of segments with motion scores
        """
        print(f"[SceneDetector] Analyzing motion in {num_segments} segments...")
        
        if not self.duration:
            self.get_video_info()
        
        segment_duration = self.duration / num_segments
        
        if parallel and num_segments > 1:
            # Use parallel processing
            workers = min(cpu_count(), num_segments)
            print(f"[SceneDetector] Using {workers} parallel workers")
            
            # Prepare analysis tasks
            tasks = []
            for i in range(num_segments):
                start_time = i * segment_duration
                tasks.append((i, start_time, segment_duration, self.video_path))
            
            # Execute in parallel
            with Pool(processes=workers) as pool:
                segments = pool.map(self._analyze_segment_worker, tasks)
            
            # Filter out None results
            segments = [s for s in segments if s is not None]
        else:
            # Sequential processing
            segments = []
            for i in range(num_segments):
                start_time = i * segment_duration
                segment = self._analyze_segment(i, start_time, segment_duration)
                if segment:
                    segments.append(segment)
                
                if (i + 1) % 5 == 0:
                    print(f"[SceneDetector] Analyzed {i + 1}/{num_segments} segments...")
        
        # Sort by motion score
        segments.sort(key=lambda x: x['motion_score'], reverse=True)
        
        print(f"[SceneDetector] Motion analysis complete")
        if segments:
            print(f"[SceneDetector] Top segment: {segments[0]['motion_score']} motion score")
        
        return segments
    
    def _analyze_segment(self, index: int, start_time: float, duration: float) -> Dict:
        """Analyze a single segment"""
        try:
            # Calculate motion vectors for this segment
            cmd = [
                'ffmpeg', '-ss', str(start_time),
                '-i', self.video_path,
                '-t', str(min(duration, 10)),  # Max 10s per segment
                '-vf', 'select=gt(scene\\,0.01),metadata=print:file=-',
                '-an', '-f', 'null', '-'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Count frame changes as motion indicator
            motion_score = result.stderr.count('lavfi.scene_score')
            
            return {
                'start': start_time,
                'end': start_time + duration,
                'duration': duration,
                'motion_score': motion_score,
                'type': 'motion_analysis'
            }
        except Exception as e:
            print(f"[SceneDetector] Error analyzing segment {index}: {e}")
            return None
    
    @staticmethod
    def _analyze_segment_worker(task):
        """Worker function for parallel segment analysis"""
        index, start_time, duration, video_path = task
        
        try:
            cmd = [
                'ffmpeg', '-ss', str(start_time),
                '-i', video_path,
                '-t', str(min(duration, 10)),
                '-vf', 'select=gt(scene\\,0.01),metadata=print:file=-',
                '-an', '-f', 'null', '-'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            motion_score = result.stderr.count('lavfi.scene_score')
            
            if (index + 1) % 5 == 0:
                print(f"[Worker] Analyzed segment {index + 1}")
            
            return {
                'start': start_time,
                'end': start_time + duration,
                'duration': duration,
                'motion_score': motion_score,
                'type': 'motion_analysis'
            }
        except Exception as e:
            print(f"[Worker] Error analyzing segment {index}: {e}")
            return None
    
    def get_smart_timestamps(self, num_clips: int = 10, clip_duration: float = 3.0) -> List[Tuple[float, float]]:
        """
        Get smart timestamps for preview clips
        Combines scene detection and motion analysis
        
        Args:
            num_clips: Number of clips to extract
            clip_duration: Duration of each clip in seconds
        
        Returns:
            List of (start_time, duration) tuples
        """
        print(f"[SceneDetector] Calculating smart timestamps for {num_clips} clips...")
        
        if not self.duration:
            info = self.get_video_info()
            if not info:
                print(f"[SceneDetector] Cannot get video info")
                return []
        
        # Check if video is too short
        min_duration = num_clips * clip_duration + 10  # Need at least this much
        if self.duration < min_duration:
            print(f"[SceneDetector] Video too short ({self.duration:.1f}s), reducing clips")
            # Adjust number of clips
            num_clips = max(1, int((self.duration - 10) / clip_duration))
            if num_clips < 1:
                print(f"[SceneDetector] Video too short for any clips")
                return []
        
        # Strategy 1: Use scene detection if available
        if not self.scenes:
            self.detect_scenes(threshold=0.3)
        
        # Strategy 2: Analyze motion
        num_segments = min(30, max(10, int(self.duration / 60)))
        motion_segments = self.analyze_motion(num_segments=num_segments)
        
        timestamps = []
        used_ranges = []  # Track used time ranges to avoid overlap
        
        # Combine scene changes and high-motion segments
        candidates = []
        
        # Add scene changes
        for scene in self.scenes[:num_clips * 2]:  # Get more candidates
            candidates.append({
                'timestamp': scene['timestamp'],
                'score': 10,  # Scene changes are high priority
                'type': 'scene'
            })
        
        # Add high-motion segments
        for segment in motion_segments[:num_clips * 2]:
            candidates.append({
                'timestamp': segment['start'] + segment['duration'] / 2,  # Middle of segment
                'score': segment['motion_score'],
                'type': 'motion'
            })
        
        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Select non-overlapping clips
        for candidate in candidates:
            if len(timestamps) >= num_clips:
                break
            
            start_time = candidate['timestamp']
            
            # Ensure clip doesn't go past video end
            if start_time + clip_duration > self.duration - 1:
                start_time = max(5, self.duration - clip_duration - 1)
            
            # Ensure clip doesn't start too early
            if start_time < 5:
                start_time = 5
            
            # Check for overlap with existing clips
            overlap = False
            for used_start, used_duration in used_ranges:
                if (start_time < used_start + used_duration and 
                    start_time + clip_duration > used_start):
                    overlap = True
                    break
            
            if not overlap:
                timestamps.append((start_time, clip_duration))
                used_ranges.append((start_time, clip_duration))
                print(f"[SceneDetector] Clip {len(timestamps)}: {start_time:.1f}s ({candidate['type']})")
        
        # If we don't have enough clips, fill with evenly spaced clips
        if len(timestamps) < num_clips:
            print(f"[SceneDetector] Only found {len(timestamps)} clips, filling with evenly spaced clips...")
            
            safe_duration = self.duration - 10
            segment_size = safe_duration / num_clips
            
            for i in range(num_clips - len(timestamps)):
                start_time = 5 + (i * segment_size)
                
                # Ensure within bounds
                if start_time + clip_duration > self.duration - 1:
                    continue
                
                # Check for overlap
                overlap = False
                for used_start, used_duration in used_ranges:
                    if (start_time < used_start + used_duration and 
                        start_time + clip_duration > used_start):
                        overlap = True
                        break
                
                if not overlap:
                    timestamps.append((start_time, clip_duration))
                    used_ranges.append((start_time, clip_duration))
        
        # Sort by timestamp
        timestamps.sort(key=lambda x: x[0])
        
        print(f"[SceneDetector] Selected {len(timestamps)} clips")
        return timestamps


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scene_detector.py <video_file>")
        sys.exit(1)
    
    video_file = sys.argv[1]
    
    detector = SceneDetector(video_file)
    
    # Get video info
    info = detector.get_video_info()
    print(f"\nVideo Info:")
    print(f"  Duration: {info['duration']:.1f}s")
    print(f"  Resolution: {info['width']}x{info['height']}")
    print(f"  FPS: {info['fps']:.2f}")
    
    # Detect scenes
    scenes = detector.detect_scenes()
    
    # Get smart timestamps
    timestamps = detector.get_smart_timestamps(num_clips=10, clip_duration=3.0)
    
    print(f"\nSmart Timestamps:")
    for i, (start, duration) in enumerate(timestamps, 1):
        print(f"  Clip {i}: {start:.1f}s - {start + duration:.1f}s")
