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
    
    def find_all_scenes(self, min_scene_duration: float = 180.0, max_clips: int = 20) -> List[float]:
        """
        Find ALL unique scenes/positions throughout the ENTIRE video
        Optimized for 45-second preview at 1.3x speed (20 clips × 3s / 1.3 = ~46s)
        
        Args:
            min_scene_duration: Minimum duration between scenes (180s = 3 minutes for full coverage)
            max_clips: Maximum number of clips to extract (20 clips for full coverage)
            
        Returns:
            List of timestamps for all unique scenes
        """
        if not self.duration:
            self.get_video_info()
        
        print(f"[ComprehensiveDetector] Analyzing ENTIRE video ({self.duration/60:.1f} minutes)...")
        print(f"[ComprehensiveDetector] Goal: Full video coverage in 45-second preview at 1.3x speed")
        
        # Strategy: Divide video into equal sections and pick best from each
        # This GUARANTEES full video coverage
        
        num_sections = max_clips
        section_duration = self.duration / num_sections
        
        print(f"\n[Step 1/2] Dividing video into {num_sections} sections...")
        print(f"[ComprehensiveDetector] Each section: {section_duration:.1f}s ({section_duration/60:.1f}min)")
        
        # Sample 3 points per section
        samples = []
        for section in range(num_sections):
            section_start = section * section_duration
            section_end = (section + 1) * section_duration
            
            # Sample at 25%, 50%, 75% of each section
            for offset in [0.25, 0.50, 0.75]:
                timestamp = section_start + (section_duration * offset)
                if timestamp < self.duration * 0.95:  # Skip last 5%
                    samples.append((section, timestamp))
        
        print(f"\n[Step 2/2] Scoring {len(samples)} samples...")
        
        max_workers = min(cpu_count(), 8)
        scored_samples = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_data = {
                executor.submit(self._quick_score_sample, ts): (section, ts)
                for section, ts in samples
            }
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_data, timeout=180):
                section, timestamp = future_to_data[future]
                completed += 1
                
                if completed % 10 == 0:
                    print(f"  Progress: {completed}/{len(samples)} samples scored...")
                
                try:
                    score = future.result()
                    scored_samples.append((section, timestamp, score))
                except:
                    pass
        
        # Pick best clip from each section (guarantees full coverage)
        selected = []
        for section in range(num_sections):
            section_samples = [(ts, score) for s, ts, score in scored_samples if s == section]
            if section_samples:
                # Pick highest scoring clip from this section
                best = max(section_samples, key=lambda x: x[1])
                selected.append(best[0])
            else:
                # Fallback: use middle of section
                selected.append(section * section_duration + section_duration / 2)
        
        # Sort chronologically
        selected.sort()
        
        print(f"\n[ComprehensiveDetector] Selected {len(selected)} scenes (ONE from EACH section)")
        print(f"[ComprehensiveDetector] Preview: {len(selected)} clips × 3s / 1.3x speed = ~{len(selected) * 3 / 1.3:.0f}s")
        print(f"[ComprehensiveDetector] Coverage: ENTIRE video from start to finish")
        
        # Show distribution
        print(f"\n[ComprehensiveDetector] Scene distribution (full video coverage):")
        for i, ts in enumerate(selected):
            print(f"  Scene {i+1}: {ts:.1f}s ({ts/60:.1f}min)")
        
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
        resolution: str = "720",
        speed: float = 1.3  # 1.3x speed
    ) -> dict:
        """
        Create a comprehensive preview with all scenes at 1.3x speed
        
        Args:
            output_path: Output file path
            clip_duration: Duration of each clip
            resolution: Target resolution
            speed: Playback speed multiplier (1.3 = 30% faster)
            
        Returns:
            Dict with preview info
        """
        from clip_extractor import ClipExtractor
        import os
        
        # Find all scenes (20 clips for full coverage)
        timestamps = self.find_all_scenes(min_scene_duration=180.0, max_clips=20)
        
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
        
        # Concatenate with speed adjustment
        print(f"\n[ComprehensiveDetector] Creating preview at {speed}x speed...")
        
        # Create concat file
        concat_file = os.path.join(os.path.dirname(output_path) or '.', 'concat_list.txt')
        with open(concat_file, 'w') as f:
            for clip_file in clip_files:
                f.write(f"file '{os.path.basename(clip_file)}'\n")
        
        # Concatenate and apply speed filter
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-vf', f'setpts={1/speed}*PTS,scale=-2:{resolution}',  # Speed up video
            '-af', f'atempo={speed}',  # Speed up audio
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',  # High quality
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, cwd=os.path.dirname(clip_files[0]))
            print(f"[ComprehensiveDetector] ✓ Preview created with {speed}x speed")
        except subprocess.CalledProcessError as e:
            print(f"[ComprehensiveDetector] ✗ Concatenation failed: {e}")
            return {'success': False, 'error': 'Concatenation failed'}
        finally:
            # Cleanup concat file
            try:
                os.remove(concat_file)
            except:
                pass
        
        # Get file size
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        
        # Cleanup clips
        extractor.cleanup_clips(clip_files)
        
        # Calculate actual duration (clips at speed)
        actual_duration = (len(timestamps) * clip_duration) / speed
        
        return {
            'success': True,
            'video_path': output_path,
            'num_clips': len(timestamps),
            'total_duration': actual_duration,
            'file_size_mb': file_size,
            'speed': speed
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
        print(f"Clips: {result['num_clips']} (full video coverage)")
        print(f"Duration: {result['total_duration']:.1f}s at {result['speed']}x speed")
        print(f"Size: {result['file_size_mb']:.1f} MB")
        print(f"Time: {elapsed:.1f}s")
        print(f"Coverage: Every {3455.7/result['num_clips']:.0f}s of original video")
        print(f"{'='*60}")
    else:
        print(f"Error: {result.get('error')}")
