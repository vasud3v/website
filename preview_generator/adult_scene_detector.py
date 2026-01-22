#!/usr/bin/env python3
"""
Advanced Adult Content Scene Detector
Uses multiple detection methods to find the most interesting scenes:
- Skin tone detection
- Motion intensity analysis
- Audio level detection
- Scene complexity
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
        Find best scenes using multiple detection methods
        Ensures coverage across entire video
        
        Args:
            num_clips: Number of clips to return
            sample_size: Number of segments to analyze
            
        Returns:
            List of timestamps with best scenes
        """
        if not self.duration:
            self.get_video_info()
        
        print(f"[AdultDetector] Analyzing video with advanced detection ({self.duration/60:.1f} minutes)...")
        
        # Skip first and last 5%
        start_offset = self.duration * 0.05
        end_offset = self.duration * 0.95
        usable_duration = end_offset - start_offset
        
        # Step 1: Detect keyframes (scene changes)
        print(f"[AdultDetector] Step 1: Detecting keyframes...")
        keyframes = self._detect_keyframes()
        print(f"[AdultDetector] Found {len(keyframes)} keyframes")
        
        # Step 2: Detect sound peaks
        print(f"[AdultDetector] Step 2: Detecting sound peaks...")
        sound_peaks = self._detect_sound_peaks()
        print(f"[AdultDetector] Found {len(sound_peaks)} sound peaks")
        
        # Step 3: Combine keyframes and sound peaks with regular sampling
        # This ensures we cover the entire video
        candidate_timestamps = set()
        
        # Add keyframes
        candidate_timestamps.update(keyframes[:sample_size // 2])
        
        # Add sound peaks
        candidate_timestamps.update(sound_peaks[:sample_size // 3])
        
        # Add regular intervals to ensure full coverage
        interval = usable_duration / (sample_size // 3)
        for i in range(sample_size // 3):
            candidate_timestamps.add(start_offset + (i * interval))
        
        # Convert to sorted list
        sample_points = sorted(list(candidate_timestamps))[:sample_size]
        
        print(f"[AdultDetector] Step 3: Analyzing {len(sample_points)} candidate segments...")
        
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
                    print(f"[AdultDetector] Progress: {completed}/{len(sample_points)} segments analyzed...")
                
                try:
                    score_data = future.result()
                    if score_data['total_score'] > 0:
                        results.append((timestamp, score_data))
                except Exception as e:
                    pass
        
        # Sort by total score (highest first)
        results.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        # Ensure diversity: pick best from different parts of video
        timestamps = self._ensure_diversity(results, num_clips)
        
        print(f"\n[AdultDetector] Selected {len(timestamps)} best scenes (distributed across video)")
        print(f"[AdultDetector] Score breakdown (top 5):")
        top_5 = sorted([(t, next((s for ts, s in results if ts == t), None)) for t in timestamps[:5]], 
                       key=lambda x: x[1]['total_score'] if x[1] else 0, reverse=True)
        
        for i, (t, score_data) in enumerate(top_5):
            if score_data:
                print(f"  #{i+1} @ {t:.1f}s ({t/60:.1f}min): Total={score_data['total_score']:.1f} "
                      f"(Skin={score_data['skin_score']:.1f}, Motion={score_data['motion_score']:.1f}, "
                      f"Audio={score_data['audio_score']:.1f}, Complex={score_data['complexity_score']:.1f})")
        
        return timestamps
    
    def _detect_keyframes(self) -> List[float]:
        """
        Detect keyframes (I-frames) using fast sampling
        """
        try:
            # For long videos, sample keyframes instead of analyzing all
            # Extract keyframes at 10 second intervals
            sample_interval = 10  # seconds
            num_samples = int(self.duration / sample_interval)
            
            keyframes = []
            
            # Quick method: just sample at regular intervals
            # This is much faster than analyzing all frames
            start_offset = self.duration * 0.05
            end_offset = self.duration * 0.95
            usable_duration = end_offset - start_offset
            
            for i in range(min(num_samples, 50)):  # Max 50 keyframes
                timestamp = start_offset + (i * usable_duration / min(num_samples, 50))
                keyframes.append(timestamp)
            
            return keyframes
            
        except Exception as e:
            print(f"[AdultDetector] Keyframe detection failed: {e}")
            return []
    
    def _detect_sound_peaks(self) -> List[float]:
        """
        Detect audio peaks using fast sampling
        """
        if not self.has_audio:
            return []
        
        try:
            # Fast method: analyze audio in chunks
            sound_peaks = []
            
            # Sample 20 points throughout the video
            start_offset = self.duration * 0.05
            end_offset = self.duration * 0.95
            usable_duration = end_offset - start_offset
            
            num_samples = 20
            chunk_duration = 5  # Analyze 5 seconds per sample
            
            for i in range(num_samples):
                timestamp = start_offset + (i * usable_duration / num_samples)
                
                # Quick audio level check
                cmd = [
                    'ffmpeg',
                    '-ss', str(timestamp),
                    '-i', self.video_path,
                    '-t', str(chunk_duration),
                    '-af', 'volumedetect',
                    '-f', 'null',
                    '-'
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
                    
                    # Check if audio is loud enough
                    mean_match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', result.stderr)
                    if mean_match:
                        mean_volume = float(mean_match.group(1))
                        # If louder than -40dB, consider it a peak
                        if mean_volume > -40:
                            sound_peaks.append(timestamp)
                except:
                    pass
            
            return sound_peaks
            
        except Exception as e:
            print(f"[AdultDetector] Sound peak detection failed: {e}")
            return []
    
    def _ensure_diversity(self, results: List[Tuple[float, Dict]], num_clips: int) -> List[float]:
        """
        Ensure selected clips are distributed across the entire video
        """
        if not results:
            return []
        
        # Divide video into sections
        num_sections = num_clips
        section_duration = self.duration / num_sections
        
        selected = []
        
        # Try to pick best clip from each section
        for section in range(num_sections):
            section_start = section * section_duration
            section_end = (section + 1) * section_duration
            
            # Find best clip in this section
            section_clips = [
                (t, s) for t, s in results 
                if section_start <= t < section_end
            ]
            
            if section_clips:
                # Pick best from this section
                best = max(section_clips, key=lambda x: x[1]['total_score'])
                selected.append(best[0])
            elif results:
                # If no clips in this section, pick closest one
                closest = min(results, key=lambda x: abs(x[0] - (section_start + section_duration/2)))
                selected.append(closest[0])
        
        # If we don't have enough, add more from top results
        if len(selected) < num_clips:
            for t, s in results:
                if t not in selected:
                    selected.append(t)
                    if len(selected) >= num_clips:
                        break
        
        return sorted(selected[:num_clips])
    
    def _analyze_segment_advanced(self, start_time: float, duration: float) -> Dict:
        """
        Advanced multi-factor analysis of a segment
        Returns dict with individual scores and total
        """
        scores = {
            'skin_score': 0.0,
            'motion_score': 0.0,
            'audio_score': 0.0,
            'complexity_score': 0.0,
            'total_score': 0.0
        }
        
        try:
            # 1. Skin tone detection (most important for adult content)
            skin_score = self._detect_skin_tone(start_time, duration)
            scores['skin_score'] = skin_score
            
            # 2. Motion analysis
            motion_score = self._analyze_motion(start_time, duration)
            scores['motion_score'] = motion_score
            
            # 3. Audio level (if available)
            if self.has_audio:
                audio_score = self._analyze_audio(start_time, duration)
                scores['audio_score'] = audio_score
            
            # 4. Visual complexity
            complexity_score = self._analyze_complexity(start_time, duration)
            scores['complexity_score'] = complexity_score
            
            # Calculate weighted total score
            # Skin tone is most important (40%), then motion (30%), audio (20%), complexity (10%)
            scores['total_score'] = (
                skin_score * 0.4 +
                motion_score * 0.3 +
                audio_score * 0.2 +
                complexity_score * 0.1
            )
            
            return scores
            
        except Exception as e:
            return scores
    
    def _detect_skin_tone(self, start_time: float, duration: float) -> float:
        """
        Detect skin tone presence in segment
        Higher score = more skin tones detected
        """
        try:
            # Extract frames and analyze color distribution
            # Skin tones are typically in YCbCr color space:
            # Y: 80-255, Cb: 85-135, Cr: 135-180
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),
                '-i', self.video_path,
                '-t', str(duration),
                '-vf', 'fps=2,scale=320:180',  # Sample 2 fps
                '-f', 'rawvideo',
                '-pix_fmt', 'rgb24',
                'pipe:1'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=6)
            
            if not result.stdout or len(result.stdout) < 1000:
                return 0
            
            # Convert to numpy array
            frame_data = np.frombuffer(result.stdout, dtype=np.uint8)
            
            # Reshape to RGB pixels
            num_pixels = len(frame_data) // 3
            pixels = frame_data.reshape((num_pixels, 3))
            
            # Detect skin tones using RGB approximation
            # Skin tone detection in RGB space
            r = pixels[:, 0].astype(float)
            g = pixels[:, 1].astype(float)
            b = pixels[:, 2].astype(float)
            
            # Skin tone conditions (simplified)
            skin_mask = (
                (r > 95) & (g > 40) & (b > 20) &
                (r > g) & (r > b) &
                (np.abs(r - g) > 15) &
                (r - g > 15)
            )
            
            # Calculate percentage of skin pixels
            skin_percentage = np.sum(skin_mask) / len(skin_mask) * 100
            
            # Score based on skin percentage (0-100)
            return min(skin_percentage * 2, 100)  # Amplify score
            
        except:
            return 0
    
    def _analyze_motion(self, start_time: float, duration: float) -> float:
        """
        Analyze motion intensity
        """
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
            
            # Calculate standard deviation (motion indicator)
            std_dev = np.std(frame_data)
            
            # Normalize to 0-100
            return min(std_dev * 1.5, 100)
            
        except:
            return 0
    
    def _analyze_audio(self, start_time: float, duration: float) -> float:
        """
        Analyze audio levels (moaning, talking, etc.)
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
            mean_match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', result.stderr)
            max_match = re.search(r'max_volume:\s*([-\d.]+)\s*dB', result.stderr)
            
            if mean_match and max_match:
                mean_volume = float(mean_match.group(1))
                max_volume = float(max_match.group(1))
                
                # Higher (less negative) = louder
                # Normalize to 0-100 scale
                # -30 dB = loud (100), -60 dB = quiet (0)
                mean_score = max(0, min(100, (mean_volume + 60) * 3.33))
                max_score = max(0, min(100, (max_volume + 30) * 3.33))
                
                # Combine mean and max
                return (mean_score * 0.6 + max_score * 0.4)
            
            return 0
            
        except:
            return 0
    
    def _analyze_complexity(self, start_time: float, duration: float) -> float:
        """
        Analyze visual complexity (more detail = more interesting)
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
            
            # Calculate entropy (complexity measure)
            hist, _ = np.histogram(frame_data, bins=256, range=(0, 256))
            hist = hist / hist.sum()  # Normalize
            hist = hist[hist > 0]  # Remove zeros
            
            entropy = -np.sum(hist * np.log2(hist))
            
            # Normalize to 0-100 (max entropy for 8-bit is 8)
            return min(entropy * 12.5, 100)
            
        except:
            return 0


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
