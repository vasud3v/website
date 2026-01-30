#!/usr/bin/env python3
"""
Advanced Clip Extraction
Extracts and processes video clips with quality optimization and parallel processing
"""
import subprocess
import os
from typing import List, Tuple
from multiprocessing import Pool, cpu_count
from functools import partial

class ClipExtractor:
    def __init__(self, video_path: str, output_dir: str = None):
        self.video_path = video_path
        self.output_dir = output_dir or os.path.dirname(os.path.abspath(video_path)) or '.'
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_clip(
        self, 
        start_time: float, 
        duration: float, 
        output_path: str,
        resolution: str = "360",
        crf: int = 28,
        fps: int = 30,
        speed: float = 1.0
    ) -> bool:
        """
        Extract a single clip with quality optimization and speed adjustment
        
        Args:
            start_time: Start time in seconds
            duration: Duration in seconds
            output_path: Output file path
            resolution: Target height (width auto-calculated)
            crf: Compression quality (18-28, lower = better quality)
            fps: Target frame rate
            speed: Speed multiplier (1.0 = normal, 1.5 = 1.5x faster)
        
        Returns:
            True if successful
        """
        try:
            # Build video filter with speed adjustment
            if speed > 1.0:
                # Speed up video and audio
                video_filter = f'scale=-2:{resolution},fps={fps},setpts={1/speed}*PTS'
                audio_filter = f'atempo={min(speed, 2.0)}'  # atempo max is 2.0
                
                # If speed > 2.0, chain multiple atempo filters
                if speed > 2.0:
                    audio_filter = f'atempo=2.0,atempo={speed/2.0}'
            else:
                video_filter = f'scale=-2:{resolution},fps={fps}'
                audio_filter = None
            
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', self.video_path,
                '-t', str(duration),
                '-vf', video_filter,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', str(crf),
            ]
            
            # Add audio filter if speed adjustment needed
            if audio_filter:
                cmd.extend(['-af', audio_filter])
            
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '96k',
                '-movflags', '+faststart',
                output_path
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120
            )
            
            return result.returncode == 0 and os.path.exists(output_path)
            
        except Exception as e:
            print(f"[ClipExtractor] Error extracting clip: {e}")
            return False
    
    def extract_multiple_clips(
        self,
        timestamps: List[Tuple[float, float]],
        resolution: str = "360",
        crf: int = 23,
        fps: int = 30,
        speed: float = 1.0,
        parallel: bool = True,
        max_workers: int = 32  # Default 32 workers
    ) -> List[str]:
        """
        Extract multiple clips with parallel processing and speed adjustment
        
        Args:
            timestamps: List of (start_time, duration) tuples
            resolution: Target height
            crf: Compression quality
            fps: Target frame rate
            speed: Speed multiplier (1.0 = normal, 1.5 = 1.5x faster)
            parallel: Use parallel processing
            max_workers: Max parallel workers (default: 32)
        
        Returns:
            List of output file paths
        """
        print(f"[ClipExtractor] Extracting {len(timestamps)} clips...")
        if speed > 1.0:
            print(f"[ClipExtractor] Speed: {speed}x (faster playback)")
        
        if parallel and len(timestamps) > 1:
            # Use parallel processing with specified workers
            workers = min(max_workers, len(timestamps))
            print(f"[ClipExtractor] Using {workers} parallel workers")
            
            # Prepare extraction tasks
            tasks = []
            for i, (start_time, duration) in enumerate(timestamps, 1):
                output_path = os.path.join(self.output_dir, f"clip_{i:03d}.mp4")
                tasks.append((i, start_time, duration, output_path, resolution, crf, fps, speed))
            
            # Create partial function with self reference
            extract_func = partial(self._extract_clip_worker, video_path=self.video_path)
            
            # Execute in parallel
            with Pool(processes=workers) as pool:
                results = pool.map(extract_func, tasks)
            
            # Filter successful extractions
            clip_files = [path for success, path in results if success]
            
            print(f"[ClipExtractor] Extracted {len(clip_files)}/{len(timestamps)} clips")
            return clip_files
        else:
            # Sequential processing
            clip_files = []
            
            for i, (start_time, duration) in enumerate(timestamps, 1):
                output_path = os.path.join(self.output_dir, f"clip_{i:03d}.mp4")
                
                print(f"[ClipExtractor] Extracting clip {i}/{len(timestamps)} from {start_time:.1f}s...")
                
                success = self.extract_clip(
                    start_time,
                    duration,
                    output_path,
                    resolution=resolution,
                    crf=crf,
                    fps=fps,
                    speed=speed
                )
                
                if success:
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"[ClipExtractor] ✓ Clip {i} extracted ({size_mb:.1f} MB)")
                    clip_files.append(output_path)
                else:
                    print(f"[ClipExtractor] ✗ Failed to extract clip {i}")
            
            print(f"[ClipExtractor] Extracted {len(clip_files)}/{len(timestamps)} clips")
            return clip_files
    
    @staticmethod
    def _extract_clip_worker(task, video_path):
        """
        Worker function for parallel clip extraction with speed adjustment
        
        Args:
            task: Tuple of (index, start_time, duration, output_path, resolution, crf, fps, speed)
            video_path: Path to source video
        
        Returns:
            Tuple of (success, output_path)
        """
        i, start_time, duration, output_path, resolution, crf, fps, speed = task
        
        try:
            # Build video filter with speed adjustment
            if speed > 1.0:
                video_filter = f'scale=-2:{resolution},fps={fps},setpts={1/speed}*PTS'
                audio_filter = f'atempo={min(speed, 2.0)}'
                
                if speed > 2.0:
                    audio_filter = f'atempo=2.0,atempo={speed/2.0}'
            else:
                video_filter = f'scale=-2:{resolution},fps={fps}'
                audio_filter = None
            
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', video_path,
                '-t', str(duration),
                '-vf', video_filter,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', str(crf),
            ]
            
            if audio_filter:
                cmd.extend(['-af', audio_filter])
            
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '96k',
                '-movflags', '+faststart',
                output_path
            ])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"[Worker] ✓ Clip {i} extracted ({size_mb:.1f} MB)")
                return (True, output_path)
            else:
                print(f"[Worker] ✗ Clip {i} failed")
                return (False, None)
                
        except Exception as e:
            print(f"[Worker] ✗ Clip {i} error: {e}")
            return (False, None)
    
    def concatenate_clips(
        self,
        clip_files: List[str],
        output_path: str,
        add_transitions: bool = False
    ) -> bool:
        """
        Concatenate clips into single video
        
        Args:
            clip_files: List of clip file paths
            output_path: Output file path
            add_transitions: Add fade transitions between clips
        
        Returns:
            True if successful
        """
        print(f"[ClipExtractor] Concatenating {len(clip_files)} clips...")
        
        try:
            # Create concat file
            concat_file = os.path.join(self.output_dir, "concat_list.txt")
            with open(concat_file, 'w') as f:
                for clip in clip_files:
                    f.write(f"file '{os.path.abspath(clip)}'\n")
            
            if add_transitions:
                # Use xfade filter for smooth transitions
                print(f"[ClipExtractor] Adding fade transitions...")
                
                # Build complex filter for transitions
                filter_complex = []
                for i in range(len(clip_files) - 1):
                    if i == 0:
                        filter_complex.append(f"[0:v][1:v]xfade=transition=fade:duration=0.5:offset=2.5[v01]")
                    else:
                        prev = f"v0{i}" if i == 1 else f"v{i-1}{i}"
                        curr = f"v{i}{i+1}"
                        filter_complex.append(f"[{prev}][{i+1}:v]xfade=transition=fade:duration=0.5:offset=2.5[{curr}]")
                
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', os.path.abspath(concat_file),
                    '-filter_complex', ';'.join(filter_complex),
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '28',
                    '-c:a', 'aac',
                    '-b:a', '96k',
                    output_path
                ]
            else:
                # Simple concatenation
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', os.path.abspath(concat_file),
                    '-c', 'copy',
                    output_path
                ]
            
            result = subprocess.run(
                cmd,
                capture_output=True
            )
            
            # Cleanup concat file
            try:
                os.remove(concat_file)
            except:
                pass
            
            if result.returncode == 0 and os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"[ClipExtractor] ✓ Concatenated preview created ({size_mb:.1f} MB)")
                return True
            else:
                print(f"[ClipExtractor] ✗ Concatenation failed")
                return False
                
        except Exception as e:
            print(f"[ClipExtractor] Error concatenating clips: {e}")
            return False
    
    def create_gif(
        self,
        video_path: str,
        output_path: str,
        width: int = 480,
        fps: int = 15,
        max_colors: int = 128
    ) -> bool:
        """
        Convert video to optimized GIF
        
        Args:
            video_path: Input video path
            output_path: Output GIF path
            width: Target width
            fps: Frame rate
            max_colors: Maximum colors (lower = smaller file)
        
        Returns:
            True if successful
        """
        print(f"[ClipExtractor] Creating GIF (width={width}, fps={fps})...")
        
        try:
            # Generate palette first for better quality
            palette_path = os.path.join(self.output_dir, "palette.png")
            
            # Generate palette
            cmd_palette = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vf', f'fps={fps},scale={width}:-1:flags=lanczos,palettegen=max_colors={max_colors}',
                palette_path
            ]
            
            subprocess.run(cmd_palette, capture_output=True, timeout=60)
            
            # Create GIF using palette
            cmd_gif = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', palette_path,
                '-filter_complex', f'fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5',
                output_path
            ]
            
            result = subprocess.run(cmd_gif, capture_output=True, timeout=120)
            
            # Cleanup palette
            try:
                os.remove(palette_path)
            except:
                pass
            
            if result.returncode == 0 and os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"[ClipExtractor] ✓ GIF created ({size_mb:.1f} MB)")
                return True
            else:
                print(f"[ClipExtractor] ✗ GIF creation failed")
                return False
                
        except Exception as e:
            print(f"[ClipExtractor] Error creating GIF: {e}")
            return False
    
    def cleanup_clips(self, clip_files: List[str]):
        """Remove temporary clip files"""
        print(f"[ClipExtractor] Cleaning up {len(clip_files)} temporary clips...")
        
        for clip in clip_files:
            try:
                if os.path.exists(clip):
                    os.remove(clip)
            except Exception as e:
                print(f"[ClipExtractor] Warning: Could not remove {clip}: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python clip_extractor.py <video_file>")
        sys.exit(1)
    
    video_file = sys.argv[1]
    
    # Test extraction
    extractor = ClipExtractor(video_file)
    
    # Extract a test clip
    test_clip = "test_clip.mp4"
    success = extractor.extract_clip(10.0, 5.0, test_clip, resolution="360", crf=28)
    
    if success:
        print(f"✓ Test clip created: {test_clip}")
    else:
        print("✗ Test clip failed")
