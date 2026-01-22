#!/usr/bin/env python3
"""
Comprehensive Scene Detector for Adult Content
Detects ALL unique scenes/positions throughout the entire video
Creates a complete preview showing every position
"""
import subprocess
import re
import json
import numpy as np
import concurrent.futures
from typing import List, Tuple, Dict
from multiprocessing import cpu_count

class ComprehensiveDetector:
    """Detects all unique scenes/positions in adult content"""
    
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
            print(f"[ComprehensiveDetector] Error getting video info: {e}")
            return None
    
    def find_all_scenes(self, min_scene_duration: float = 20.0, max_clips: int = 40) -> List[float]:
        """
        Find ALL unique scenes/positions throughout the video (FAST method)
        
        Args:
            min_scene_duration: Minimum duration between scenes (seconds)
            max_clips: Maximum number of clips to extract
            
        Returns:
            List of timestamps for all unique scenes
        """
        if not self.duration:
            self.get_video_info()
        
        print(f"[ComprehensiveDetector] Analyzing entire video ({self.duration/60:.1f} minutes)...")
        print(f"[ComprehensiveDetector] Goal: Capture EVERY position/scene change")
        
        # Fast method: Sample densely throughout the video
        # Then score each sample to find the best representatives
        
        # Sample every 20 seconds (will give us ~170 samples for 57min video)
        sample_interval = 20
        num_samples = int(self.duration / sample_interval)
        
        print(f"\n[Step 1/2] Sampling {num_samples} points throughout video...")
        
        samples = []
        start_offset = self.duration * 0.05
        end_offset = self.duration * 0.95
        
        for i in range(num_samples):
            timestamp = start_offset + (i * sample_interval)
            if timestamp < end_offset:
                samples.append(timestamp)
        
        # Score each sample in parallel
        print(f"\n[Step 2/2] Scoring {len(samples)} samples...")
        
        max_workers = min(cpu_count(), 8)
        scored_samples = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_timestamp = {
                executor.submit(self._quick_score_sample, ts): ts
                for ts in samples
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_timestamp, timeout=180):
                timestamp = future_to_timestamp[future]
                completed += 1
                
                if completed % 20 == 0:
                    print(f"  Progress: {completed}/{len(samples)} samples scored...")
                
                try:
                    score = future.result()
                    if score > 0:
                        scored_samples.append((timestamp, score))
                except:
                    pass
        
        # Sort by score
        scored_samples.sort(key=lambda x: x[1], reverse=True)
        
        # Take top max_clips, but ensure they're spread out
        selected = []
        for timestamp, score in scored_samples:
            # Check if this timestamp is far enough from already selected ones
            if all(abs(timestamp - s) >= min_scene_duration for s in selected):
                selected.append(timestamp)
                if len(selected) >= max_clips:
                    break
        
        # Sort chronologically
        selected.sort()
        
        print(f"\n[ComprehensiveDetector] Selected {len(selected)} unique scenes")
        print(f"[ComprehensiveDetector] Coverage: Every ~{self.duration/len(selected):.1f} seconds")
        
        # Show distribution
        print(f"\n[ComprehensiveDetector] Scene distribution:")
        for i, ts in enumerate(selected[:15]):  # Show first 15
            print(f"  Scene {i+1}: {ts:.1f}s ({ts/60:.1f}min)")
        if len(selected) > 15:
            print(f"  ... and {len(selected)-15} more scenes")
        
        return selected
    
    def _quick_score_sample(self, timestamp: float) -> float:
        """
        Quickly score a sample point (skin + motion + audio)
        """
        try:
            # Extract a single frame and analyze
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', self.video_path,
                '-frames:v', '1',
                '-vf', 'scale=160:90',  # Very small for speed
                '-f', 'rawvideo',
                '-pix_fmt', 'rgb24',
                'pipe:1'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=3)
            
            if not result.stdout or len(result.stdout) < 100:
                return 0
            
            # Quick skin tone check
            frame_data = np.frombuffer(result.stdout, dtype=np.uint8)
            pixels = frame_data.reshape((-1, 3))
            
            r = pixels[:, 0].astype(float)
            g = pixels[:, 1].astype(float)
            b = pixels[:, 2].astype(float)
            
            # Skin detection
            skin_mask = (
                (r > 95) & (g > 40) & (b > 20) &
                (r > g) & (r > b) &
                (np.abs(r - g) > 15)
            )
            
            skin_percentage = np.sum(skin_mask) / len(skin_mask) * 100
            
            # Motion check (variance)
            variance = np.var(frame_data)
            
            # Combined score
            score = skin_percentage + (variance / 10)
            
            return score
            
        except:
            return 0
    
    def create_comprehensive_preview(
        self,
        output_path: str,
        clip_duration: float = 3.0,
        resolution: str = "720"
    ) -> dict:
        """
        Create a comprehensive preview with all scenes
        
        Args:
            output_path: Output file path
            clip_duration: Duration of each clip
            resolution: Target resolution
            
        Returns:
            Dict with preview info
        """
        from clip_extractor import ClipExtractor
        import os
        
        # Find all scenes
        timestamps = self.find_all_scenes(min_scene_duration=20.0, max_clips=40)
        
        if not timestamps:
            return {'success': False, 'error': 'No scenes found'}
        
        # Extract clips
        print(f"\n[ComprehensiveDetector] Extracting {len(timestamps)} clips...")
        
        extractor = ClipExtractor(self.video_path, os.path.dirname(output_path) or '.')
        
        # Convert to (timestamp, duration) tuples
        timestamp_tuples = [(t, clip_duration) for t in timestamps]
        
        clip_files = extractor.extract_multiple_clips(
            timestamp_tuples,
            resolution=resolution,
            parallel=True
        )
        
        if not clip_files:
            return {'success': False, 'error': 'Failed to extract clips'}
        
        # Concatenate
        print(f"\n[ComprehensiveDetector] Creating comprehensive preview...")
        preview_path = extractor.concatenate_clips(clip_files, output_path)
        
        if not preview_path:
            return {'success': False, 'error': 'Failed to concatenate clips'}
        
        # Get file size
        file_size = os.path.getsize(preview_path) / (1024 * 1024)
        
        # Cleanup
        extractor.cleanup_clips(clip_files)
        
        return {
            'success': True,
            'video_path': preview_path,
            'num_clips': len(timestamps),
            'total_duration': len(timestamps) * clip_duration,
            'file_size_mb': file_size
        }


if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python comprehensive_detector.py <video_file> [output_file]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "comprehensive_preview.mp4"
    
    detector = ComprehensiveDetector(video_path)
    
    import time
    start = time.time()
    
    result = detector.create_comprehensive_preview(output_path, clip_duration=3.0)
    
    elapsed = time.time() - start
    
    if result['success']:
        print(f"\n{'='*60}")
        print(f"COMPREHENSIVE PREVIEW COMPLETE")
        print(f"{'='*60}")
        print(f"Output: {result['video_path']}")
        print(f"Clips: {result['num_clips']}")
        print(f"Duration: {result['total_duration']:.1f}s")
        print(f"Size: {result['file_size_mb']:.1f} MB")
        print(f"Time: {elapsed:.1f}s")
        print(f"{'='*60}")
    else:
        print(f"Error: {result.get('error')}")
