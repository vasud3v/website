#!/usr/bin/env python3
"""
Advanced Adult Content Scene Detector
Uses multiple detection methods to find the most interesting scenes:
1. Motion intensity (high activity)
2. Skin tone detection (more skin = more interesting)
3. Audio analysis (moaning/sounds)
4. Scene diversity (avoid repetitive scenes)
"""
import subprocess
import re
import json
import numpy as np
import concurrent.futures
from typing import List, Tuple, Dict
from multiprocessing import cpu_count

class AdultSceneDetector:
    """Advanced detector for adult content scenes"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.duration = None
        self.width = None
        self.height = None
        self.fps = None
        self.has_audio = False
        
    def get_video_info(self) -> dict:
        """Get video metadata"""
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
            
            audio_stream = next(
                (s for s in data['streams'] if s['codec_type'] == 'audio'),
                None
            )
            
            if video_stream:
                self.duration = float(data['format']['duration'])
                self.width = int(video_stream['width'])
                self.height = int(video_stream['height'])
                
                fps_str = video_stream.get('r_frame_rate', '30/1')
                num, den = map(int, fps_str.split('/'))
                self.fps = num / den if den != 0 else 30.0
                
                self.has_audio = audio_stream is not None
                
                return {
                    'duration': self.duration,
                    'width': self.width,
                    'height': self.height,
                    'fps': self.fps,
                    'has_audio': self.has_audio
                }
        except Exception as e:
            print(f"[AdultDetector] Error getting video info: {e}")
            return None
    
    def find_best_scenes(self, num_clips: int = 10, sample_size: int = 60) -> List[float]:
        """
        Find the best adult scenes using multiple detection methods
        
        Args:
            num_clips: Number of clips to return
            sample_size: Number of segments to analyze
            
        Returns:
            List of timestamps with best scenes
        """
        if not self.duration:
            self.get_video_info()
        
        print(f"[AdultDetector] Analyzing video ({self.duration/60:.1f} minutes)...")
        print(f"[AdultDetector] Using advanced multi-factor analysis...")
        
        # Skip first and last 5% (intro/outro)
        start_offset = self.duration * 0.05
        end_offset = self.duration * 0.95
        usable_duration = end_offset - start_offset
        
        # Calculate sample points
        interval = usable_duration / sample_size
        sample_points = [start_offset + (i * interval) for i in range(sample_size)]
        
        print(f"[AdultDetector] Analyzing {sample_size} segments in parallel...")
        
        # Analyze all segments in parallel
        max_workers = min(cpu_count(), 8)
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_timestamp = {
                executor.submit(self._analyze_segment_advanced, timestamp, 5.0): timestamp
                for timestamp in sample_points
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_timestamp, timeout=180):
                timestamp = future_to_timestamp[future]
                completed += 1
                
                if completed % 10 == 0:
                    print(f"[AdultDetector] Progress: {completed}/{sample_size} segments analyzed...")
                
                try:
                    score_data = future.result()
                    if score_data['total_score'] > 0:
                        results.append((timestamp, score_data))
                except Exception as e:
                    print(f"[AdultDetector] Segment analysis failed at {timestamp:.1f}s: {e}")
        
        # Sort by total score (highest first)
        results.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        # Apply diversity filter to avoid similar scenes
        diverse_results = self._apply_diversity_filter(results, num_clips)
        
        # Sort chronologically
        timestamps = sorted([t for t, s in diverse_results])
        
        print(f"[AdultDetector] Selected {len(timestamps)} best scenes")
        print(f"[AdultDetector] Score breakdown:")
        for t, score_data in sorted(diverse_results, key=lambda x: x[0]):
            print(f"  {t:.1f}s: Motion={score_data['motion']:.1f}, Skin={score_data['skin']:.1f}, "
                  f"Audio={score_data['audio']:.1f}, Total={score_data['total_score']:.1f}")
        
        return timestamps
    
    def _analyze_segment_advanced(self, start_time: float, duration: float) -> Dict:
        """
        Advanced segment analysis using multiple factors
        """
        scores = {
            'motion': 0.0,
            'skin': 0.0,
            'audio': 0.0,
            'brightness': 0.0,
            'total_score': 0.0
        }
        
        try:
            # 1. Motion Analysis (40% weight)
            motion_score = self._analyze_motion(start_time, duration)
            scores['motion'] = motion_score
            
            # 2. Skin Tone Detection (30% weight)
            skin_score = self._analyze_skin_tones(start_time, duration)
            scores['skin'] = skin_score
            
            # 3. Audio Analysis (20% weight)
            if self.has_audio:
                audio_score = self._analyze_audio(start_time, duration)
                scores['audio'] = audio_score
            
            # 4. Brightness Check (10% weight)
            brightness_score = self._analyze_brightness(start_time, duration)
            scores['brightness'] = brightness_score
            
            # Calculate weighted total score
            scores['total_score'] = (
                motion_score * 0.4 +
                skin_score * 0.3 +
                scores['audio'] * 0.2 +
                brightness_score * 0.1
            )
            
        except Exception as e:
            pass
        
        return scores
    
    def _analyze_motion(self, start_time: float, duration: float) -> float:
        """Analyze motion intensity"""
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', self.video_path,
                '-t', str(duration),
                '-vf', 'fps=2,scale=320:180',
                '-f', 'rawvideo',
                '-pix_fmt', 'gray',
                'pipe:1'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=6)
            
            if not result.stdout:
                return 0
            
            frame_data = np.frombuffer(result.stdout, dtype=np.uint8)
            if len(frame_data) == 0:
                return 0
            
            # Calculate standard deviation (variation = motion)
            std_dev = np.std(frame_data)
            return float(std_dev)
            
        except:
            return 0
    
    def _analyze_skin_tones(self, start_time: float, duration: float) -> float:
        """
        Detect skin tones in the scene
        More skin = higher score (indicates nudity/activity)
        """
        try:
            # Extract frames and analyze color distribution
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', self.video_path,
                '-t', str(duration),
                '-vf', 'fps=1,scale=320:180',
                '-f', 'rawvideo',
                '-pix_fmt', 'rgb24',
                'pipe:1'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=6)
            
            if not result.stdout:
                return 0
            
            # Convert to numpy array
            frame_data = np.frombuffer(result.stdout, dtype=np.uint8)
            if len(frame_data) < 320 * 180 * 3:
                return 0
            
            # Reshape to RGB image
            pixels = frame_data.reshape(-1, 3)
            
            # Skin tone detection (RGB ranges)
            # Typical skin tones: R > 95, G > 40, B > 20, R > G, R > B
            r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
            
            skin_mask = (
                (r > 95) & (g > 40) & (b > 20) &
                (r > g) & (r > b) &
                (np.abs(r.astype(int) - g.astype(int)) > 15)
            )
            
            # Calculate percentage of skin pixels
            skin_percentage = np.sum(skin_mask) / len(pixels) * 100
            
            # Score based on skin percentage (more skin = higher score)
            return float(skin_percentage * 2)  # Scale up
            
        except:
            return 0
    
    def _analyze_audio(self, start_time: float, duration: float) -> float:
        """
        Analyze audio intensity (volume/activity)
        Higher audio activity often indicates interesting scenes
        """
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', self.video_path,
                '-t', str(duration),
                '-af', 'volumedetect',
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
            
            # Parse mean volume
            mean_volume_match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', result.stderr)
            max_volume_match = re.search(r'max_volume:\s*([-\d.]+)\s*dB', result.stderr)
            
            if mean_volume_match and max_volume_match:
                mean_vol = float(mean_volume_match.group(1))
                max_vol = float(max_volume_match.group(1))
                
                # Higher (less negative) = louder
                # Convert to positive score
                audio_score = (mean_vol + 60) + (max_vol + 60) * 0.5
                return max(0, audio_score)
            
            return 0
            
        except:
            return 0
    
    def _analyze_brightness(self, start_time: float, duration: float) -> float:
        """
        Check brightness - avoid too dark or too bright scenes
        """
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', self.video_path,
                '-t', str(duration),
                '-vf', 'fps=1,scale=320:180',
                '-f', 'rawvideo',
                '-pix_fmt', 'gray',
                'pipe:1'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=6)
            
            if not result.stdout:
                return 0
            
            frame_data = np.frombuffer(result.stdout, dtype=np.uint8)
            if len(frame_data) == 0:
                return 0
            
            mean_brightness = np.mean(frame_data)
            
            # Optimal brightness: 80-180 (well-lit scenes)
            if 80 <= mean_brightness <= 180:
                return 100.0
            elif mean_brightness < 80:
                # Too dark
                return mean_brightness / 80 * 50
            else:
                # Too bright
                return (255 - mean_brightness) / 75 * 50
            
        except:
            return 50.0  # Default neutral score
    
    def _apply_diversity_filter(self, results: List[Tuple[float, Dict]], num_clips: int) -> List[Tuple[float, Dict]]:
        """
        Apply diversity filter to avoid selecting similar/adjacent scenes
        """
        if len(results) <= num_clips:
            return results
        
        selected = []
        min_gap = self.duration / (num_clips * 2)  # Minimum time gap between clips
        
        for timestamp, score_data in results:
            # Check if this timestamp is far enough from already selected ones
            is_diverse = True
            for selected_timestamp, _ in selected:
                if abs(timestamp - selected_timestamp) < min_gap:
                    is_diverse = False
                    break
            
            if is_diverse:
                selected.append((timestamp, score_data))
                
                if len(selected) >= num_clips:
                    break
        
        # If we don't have enough, fill with best remaining
        if len(selected) < num_clips:
            for timestamp, score_data in results:
                if (timestamp, score_data) not in selected:
                    selected.append((timestamp, score_data))
                    if len(selected) >= num_clips:
                        break
        
        return selected


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python adult_scene_detector.py <video_file>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    detector = AdultSceneDetector(video_path)
    
    import time
    start = time.time()
    
    timestamps = detector.find_best_scenes(num_clips=10, sample_size=60)
    
    elapsed = time.time() - start
    
    print(f"\nResults:")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Timestamps: {[f'{t:.1f}s' for t in timestamps]}")
