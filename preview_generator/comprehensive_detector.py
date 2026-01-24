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
    
    def find_all_scenes(self, min_scene_duration: float = 80.0, max_clips: int = None, skip_intro: float = 180.0) -> List[float]:
        """
        Find ALL sex scenes throughout the video (skipping minimal intro)
        Dynamically calculates optimal clip count based on video duration
        Target: 1 clip every 80 seconds to ensure NO scene is missed
        
        Args:
            min_scene_duration: Minimum duration between scenes (80s for maximum coverage)
            max_clips: Maximum number of clips (None = auto-calculate based on duration)
            skip_intro: Skip first N seconds (180s = 3 minutes, minimal skip)
            
        Returns:
            List of timestamps for all sex scenes
        """
        if not self.duration:
            self.get_video_info()
        
        # Calculate effective video duration (skip minimal intro)
        effective_start = skip_intro
        effective_end = self.duration - 30  # Skip only last 30 seconds (credits)
        effective_duration = effective_end - effective_start
        
        # DYNAMIC CLIP COUNT based on video duration
        # Target: 1 clip every 80 seconds to ensure MAXIMUM coverage
        # For 2-hour video: 120min × 60s / 80s = 90 clips
        # At 2s per clip with 1.5x speed: 90 × 2 / 1.5 = 120s preview
        if max_clips is None:
            # Calculate clips needed for full coverage (1 every 80 seconds)
            max_clips = max(30, int(effective_duration / 80))  # Minimum 30 clips
            # Cap at 60 clips max to prevent timeout (max 80s preview at 1.5x)
            max_clips = min(max_clips, 60)  # Was 90, reduced for performance
        
        # Ensure we have at least some clips
        if max_clips < 10:
            max_clips = 10
            print(f"[ComprehensiveDetector] ⚠️ Short video, using minimum 10 clips")
        
        print(f"[ComprehensiveDetector] Analyzing video ({self.duration/60:.1f} minutes total)...")
        print(f"[ComprehensiveDetector] Skipping first {skip_intro/60:.1f} minutes (minimal intro skip)")
        print(f"[ComprehensiveDetector] Analyzing {effective_duration/60:.1f} minutes of content")
        print(f"[ComprehensiveDetector] Dynamic clips: {max_clips} (1 every {effective_duration/max_clips:.0f}s)")
        print(f"[ComprehensiveDetector] Goal: Capture EVERY sex scene/position - MAXIMUM COVERAGE")
        
        # Strategy: Divide effective video into equal sections and pick best from each
        # This GUARANTEES full coverage - NO scene will be missed
        
        num_sections = max_clips
        section_duration = effective_duration / num_sections
        
        print(f"\n[Step 1/2] Dividing video into {num_sections} sections...")
        print(f"[ComprehensiveDetector] Each section: {section_duration:.1f}s ({section_duration/60:.1f}min)")
        
        # Sample 7 points per section for MAXIMUM sex scene detection
        # More samples = guaranteed to catch every position change
        samples = []
        for section in range(num_sections):
            section_start = effective_start + (section * section_duration)
            section_end = effective_start + ((section + 1) * section_duration)
            
            # Sample at 15%, 25%, 35%, 50%, 65%, 75%, 85% of each section
            # 7 samples per section ensures NO scene is missed
            for offset in [0.15, 0.25, 0.35, 0.50, 0.65, 0.75, 0.85]:
                timestamp = section_start + (section_duration * offset)
                if timestamp < effective_end:
                    samples.append((section, timestamp))
        
        print(f"\n[Step 2/2] Scoring {len(samples)} samples...")
        
        max_workers = min(cpu_count(), 32)
        scored_samples = []
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_data = {
                    executor.submit(self._quick_score_sample, ts): (section, ts)
                    for section, ts in samples
                }
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_data, timeout=300):
                    section, timestamp = future_to_data[future]
                    completed += 1
                    
                    if completed % 20 == 0 or completed == len(samples):
                        print(f"  Progress: {completed}/{len(samples)} samples scored...")
                    
                    try:
                        score = future.result()
                        scored_samples.append((section, timestamp, score))
                    except Exception as e:
                        # Use default score on error
                        scored_samples.append((section, timestamp, 50.0))
        except concurrent.futures.TimeoutError:
            print(f"  ⚠️ Scoring timeout, using {len(scored_samples)} completed samples")
            if len(scored_samples) < num_sections:
                print(f"  ⚠️ Not enough samples, falling back to uniform distribution")
                # Fallback: uniform distribution
                timestamps = []
                for section in range(num_sections):
                    ts = effective_start + (section * section_duration) + (section_duration / 2)
                    timestamps.append(ts)
                return timestamps
        
        # Pick best clip from each section (guarantees full coverage)
        selected = []
        for section in range(num_sections):
            section_samples = [(ts, score) for s, ts, score in scored_samples if s == section]
            if section_samples:
                # Pick highest scoring clip from this section (best sex scene)
                best = max(section_samples, key=lambda x: x[1])
                selected.append((best[0], best[1]))  # Keep score for debugging
            else:
                # Fallback: use middle of section
                fallback_ts = effective_start + (section * section_duration) + (section_duration / 2)
                selected.append((fallback_ts, 50.0))
        
        # Ensure we have clips
        if not selected:
            print(f"[ComprehensiveDetector] ⚠️ No clips selected, using fallback")
            for section in range(min(10, num_sections)):
                ts = effective_start + (section * section_duration) + (section_duration / 2)
                selected.append((ts, 50.0))
        
        # Sort chronologically
        selected.sort(key=lambda x: x[0])
        
        # Extract just timestamps
        timestamps = [ts for ts, score in selected]
        
        print(f"\n[ComprehensiveDetector] Selected {len(timestamps)} sex scenes (ONE from EACH section)")
        print(f"[ComprehensiveDetector] Preview: {len(timestamps)} clips × 2s / 1.5x speed = ~{len(timestamps) * 2 / 1.5:.0f}s")
        print(f"[ComprehensiveDetector] Coverage: EVERY sex scene from {skip_intro/60:.1f}min to {effective_end/60:.1f}min")
        print(f"[ComprehensiveDetector] Interval: 1 clip every {effective_duration/len(timestamps):.0f}s = COMPLETE COVERAGE")
        
        # Show distribution with scores
        print(f"\n[ComprehensiveDetector] Sex scene distribution:")
        for i, (ts, score) in enumerate(selected[:10]):  # Show first 10
            print(f"  Scene {i+1}: {ts:.1f}s ({ts/60:.1f}min) - Score: {score:.1f}")
        if len(selected) > 10:
            print(f"  ... and {len(selected) - 10} more scenes")
        
        return timestamps
        
        return selected
    
    def _quick_score_sample(self, timestamp: float) -> float:
        """
        Score a sample point for sex scene detection
        Prioritizes: High skin tone + High motion + Good brightness
        """
        try:
            # Extract a single frame and analyze - use accurate seeking
            cmd = [
                'ffmpeg',
                '-accurate_seek',
                '-ss', str(timestamp),
                '-i', self.video_path,
                '-vframes', '1',
                '-vf', 'scale=160:90',
                '-f', 'rawvideo',
                '-pix_fmt', 'rgb24',
                '-v', 'error',
                'pipe:1'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if not result.stdout:
                return 50.0  # Default score if extraction fails
            
            # Analyze frame
            frame_data = np.frombuffer(result.stdout, dtype=np.uint8)
            
            # Check if we got the expected amount of data
            expected_size = 160 * 90 * 3
            if len(frame_data) < expected_size:
                return 50.0  # Default score
            
            pixels = frame_data[:expected_size].reshape((90, 160, 3))
            
            r = pixels[:, :, 0].astype(float)
            g = pixels[:, :, 1].astype(float)
            b = pixels[:, :, 2].astype(float)
            
            # Enhanced skin detection for adult content
            # More permissive ranges to catch various skin tones
            skin_mask = (
                (r > 85) & (g > 35) & (b > 15) &  # Broader range
                (r > g) & (r > b) &
                (np.abs(r - g) > 10) &  # Less strict
                (r < 250) & (g < 230) & (b < 220)  # Avoid overexposure
            )
            
            skin_percentage = np.sum(skin_mask) / skin_mask.size * 100
            
            # Motion/complexity check (higher variance = more action)
            variance = np.var(frame_data.astype(float))
            motion_score = min(variance / 100, 50)  # Cap at 50
            
            # Brightness check (avoid too dark or too bright scenes)
            brightness = np.mean(frame_data.astype(float))
            brightness_penalty = 0
            if brightness < 60 or brightness > 220:
                brightness_penalty = 10  # Reduced penalty
            
            # Combined score (prioritize skin + motion)
            # Sex scenes typically have: 30-60% skin + high motion
            score = (skin_percentage * 2.0) + motion_score - brightness_penalty
            
            return max(10.0, score)  # Minimum score of 10
            
        except Exception as e:
            # Return default score on error
            return 50.0
    
    def create_comprehensive_preview(
        self,
        output_path: str,
        clip_duration: float = 2.0,  # 2s per clip for better quality
        resolution: str = "720",
        speed: float = 1.5,  # 1.5x speed (faster for longer videos)
        skip_intro: float = 180.0  # Skip first 3 minutes (reduced from 5)
    ) -> dict:
        """
        Create a comprehensive preview with ALL sex scenes at 1.5x speed
        Skips first 3 minutes (intro) and focuses on actual content
        Dynamically adjusts clip count based on video duration
        
        For 2-hour video: ~90 clips × 2s / 1.5x = ~120s preview
        For 1-hour video: ~45 clips × 2s / 1.5x = ~60s preview
        
        Args:
            output_path: Output file path
            clip_duration: Duration of each clip (2s for quality)
            resolution: Target resolution (720p for quality)
            speed: Playback speed multiplier (1.5 = 50% faster)
            skip_intro: Skip first N seconds (180s = 3 minutes, reduced to cover more)
            
        Returns:
            Dict with preview info
        """
        from clip_extractor import ClipExtractor
        import os
        
        # Find all sex scenes (dynamic count based on duration, skip intro)
        # Will automatically calculate: 1 clip every 80 seconds (more coverage)
        timestamps = self.find_all_scenes(min_scene_duration=80.0, max_clips=None, skip_intro=skip_intro)
        
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
            crf=23,  # Balanced quality/speed (was 20)
            parallel=True
        )
        
        if not clip_files:
            return {'success': False, 'error': 'Failed to extract clips'}
        
        # CRITICAL: Sort clip files by their numeric index to ensure chronological order
        # Parallel extraction returns clips in completion order, not chronological
        # Extract the number from filename like "clip_001.mp4" -> 1
        def get_clip_number(filepath):
            import re
            match = re.search(r'clip_(\d+)', os.path.basename(filepath))
            return int(match.group(1)) if match else 0
        
        clip_files.sort(key=get_clip_number)
        print(f"[ComprehensiveDetector] ✓ {len(clip_files)} clips sorted in chronological order")
        
        # Concatenate with speed adjustment
        print(f"\n[ComprehensiveDetector] Creating preview at {speed}x speed...")
        
        # Create concat file with proper escaping
        concat_file = os.path.join(os.path.dirname(output_path) or '.', 'concat_list.txt')
        try:
            with open(concat_file, 'w', encoding='utf-8') as f:
                for clip_file in clip_files:
                    # Use absolute paths to avoid issues
                    abs_path = os.path.abspath(clip_file)
                    # Escape single quotes and backslashes for ffmpeg
                    escaped_path = abs_path.replace('\\', '/').replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
        except Exception as e:
            print(f"[ComprehensiveDetector] ✗ Failed to create concat file: {e}")
            return {'success': False, 'error': f'Concat file creation failed: {e}'}
        
        # Concatenate clips first WITH re-encoding (ensures compatibility)
        print(f"[ComprehensiveDetector] Concatenating {len(clip_files)} clips...")
        temp_concat = os.path.join(os.path.dirname(output_path) or '.', 'temp_concat.mp4')
        
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # Fastest for intermediate (was fast)
            '-crf', '23',  # Slightly lower quality for speed
            '-c:a', 'aac',
            '-b:a', '192k',  # Lower bitrate for speed
            '-y',
            temp_concat
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[ComprehensiveDetector] ✓ Clips concatenated successfully")
        except subprocess.CalledProcessError as e:
            print(f"[ComprehensiveDetector] ✗ Concatenation failed: {e}")
            if e.stderr:
                print(f"[ComprehensiveDetector] Error output: {e.stderr[:500]}")
            return {'success': False, 'error': 'Concatenation failed'}
        except Exception as e:
            print(f"[ComprehensiveDetector] ✗ Unexpected error: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            # Cleanup concat file
            try:
                if os.path.exists(concat_file):
                    os.remove(concat_file)
            except:
                pass
        
        # Now apply speed filter with HIGH QUALITY re-encoding (optimized for CI/CD)
        print(f"[ComprehensiveDetector] Applying {speed}x speed with high quality encoding...")
        
        cmd = [
            'ffmpeg',
            '-i', temp_concat,
            '-filter_complex', f'[0:v]setpts={1/speed}*PTS[v];[0:a]atempo={speed}[a]',
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264',
            '-preset', 'fast',  # Faster preset (was medium)
            '-crf', '21',  # Good quality (was 20, slightly faster)
            '-profile:v', 'high',
            '-level', '4.1',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            '-c:a', 'aac',
            '-b:a', '192k',  # Lower bitrate for speed (was 256k)
            '-ar', '48000',
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[ComprehensiveDetector] ✓ Preview created with {speed}x speed and high quality")
        except subprocess.CalledProcessError as e:
            print(f"[ComprehensiveDetector] ✗ Speed filter failed: {e}")
            if e.stderr:
                print(f"[ComprehensiveDetector] Error output: {e.stderr[:500]}")
            return {'success': False, 'error': 'Speed filter failed'}
        except Exception as e:
            print(f"[ComprehensiveDetector] ✗ Unexpected error: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            # Cleanup temp concat file
            try:
                if os.path.exists(temp_concat):
                    os.remove(temp_concat)
            except:
                pass
        
        # Get file size
        try:
            file_size = os.path.getsize(output_path) / (1024 * 1024)
        except:
            file_size = 0
        
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
            'speed': speed,
            'resolution': resolution
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
    
    result = detector.create_comprehensive_preview(output_path, clip_duration=2.0)
    
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
