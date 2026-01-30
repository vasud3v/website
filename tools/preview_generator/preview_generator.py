#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Preview Generator for Adult Content
Uses multi-factor analysis: motion, skin detection, audio, brightness
Optimized to find the most interesting scenes
"""
import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from adult_scene_detector import AdultSceneDetector
from clip_extractor import ClipExtractor

class PreviewGenerator:
    def __init__(self, video_path: str, output_dir: str = None):
        self.video_path = video_path
        self.output_dir = output_dir or os.path.dirname(os.path.abspath(video_path)) or '.'
        
        self.detector = AdultSceneDetector(video_path)
        self.extractor = ClipExtractor(video_path, self.output_dir)
    
    def generate_preview(
        self,
        output_path: str = None,
        target_duration: float = None,  # Auto-calculate if not specified
        clip_duration: float = 2.5,  # Duration of each clip in seconds
        resolution: str = "360",
        crf: int = 23,  # Better quality (lower = better, 23 is high quality)
        fps: int = 30,
        create_gif: bool = False,
        gif_width: int = 480,
        cleanup: bool = True,
        parallel: bool = True,
        max_workers: int = 32  # Default 32 workers
    ) -> dict:
        """
        Generate smart preview video with DYNAMIC clip selection
        Automatically captures ALL sex scenes, drama, creampie moments, and outro
        
        Args:
            output_path: Output file path (default: video_preview.mp4)
            target_duration: Target total duration (auto-calculated if None)
            clip_duration: Duration of each clip in seconds
            resolution: Target height (720, 480, etc.)
            crf: Compression quality (18-28, lower = better)
            fps: Target frame rate
            create_gif: Also create GIF version
            gif_width: GIF width in pixels
            cleanup: Remove temporary clip files
            parallel: Use parallel processing (faster)
            max_workers: Max parallel workers (default: 32)
        
        Returns:
            Dict with preview info and paths
        """
        print("=" * 60)
        print("DYNAMIC PREVIEW GENERATOR")
        
        # Get video info first
        info = self.detector.get_video_info()
        if not info:
            print("✗ Failed to get video info")
            return {'success': False}
        
        video_duration_minutes = info['duration'] / 60
        
        # DYNAMIC calculation: Determine optimal clips based on video length
        # Goal: Capture all sex scenes, drama, and outro comprehensively
        if target_duration is None:
            # Auto-calculate based on video length
            # Formula: Longer videos need more clips to capture all content
            if video_duration_minutes <= 30:
                # Short videos: 1 clip per 2 minutes, normal speed
                num_clips = max(15, int(video_duration_minutes / 2))
                speed_multiplier = 1.0
            elif video_duration_minutes <= 60:
                # Medium videos: 1 clip per 2.5 minutes, slight speedup
                num_clips = max(20, int(video_duration_minutes / 2.5))
                speed_multiplier = 1.1
            elif video_duration_minutes <= 90:
                # Long videos: 1 clip per 3 minutes, moderate speedup
                num_clips = max(25, int(video_duration_minutes / 3))
                speed_multiplier = 1.25
            else:
                # Very long videos: 1 clip per 3.5 minutes, max speedup
                num_clips = max(30, int(video_duration_minutes / 3.5))
                speed_multiplier = 1.5
            
            target_duration = num_clips * clip_duration
            print(f"Auto-calculated: {num_clips} clips × {clip_duration}s @ {speed_multiplier}x speed = {target_duration/speed_multiplier:.0f}s preview")
        else:
            num_clips = int(target_duration / clip_duration)
            speed_multiplier = 1.0
            print(f"Manual target: {num_clips} clips × {clip_duration}s = {target_duration:.0f}s preview")
        
        print(f"Video: {video_duration_minutes:.1f} minutes")
        print(f"Coverage: ALL sex scenes + drama + creampie + outro")
        if speed_multiplier > 1.0:
            print(f"Speed: {speed_multiplier}x (dynamic adjustment for long video)")
        print(f"Workers: {max_workers}")
        print("=" * 60)
        
        # Calculate number of clips to fit target duration
        num_clips = int(target_duration / clip_duration)
        
        # Generate output path
        if not output_path:
            base, ext = os.path.splitext(self.video_path)
            output_path = f"{base}_preview.mp4"
        
        gif_path = None
        if create_gif:
            gif_path = output_path.replace('.mp4', '.gif')
        
        result = {
            'success': False,
            'video_path': None,
            'gif_path': None,
            'num_clips': 0,
            'total_duration': 0,
            'file_size_mb': 0
        }
        
        try:
            # Step 1: Get video info (already done above)
            print("\n[1/5] Analyzing video...")
            print(f"✓ Video: {info['duration']:.1f}s, {info['width']}x{info['height']}, {info['fps']:.1f}fps")
            
            # Step 2: Dynamic scene detection with comprehensive sampling
            print("\n[2/5] Detecting best scenes (multi-factor analysis)...")
            print("         Analyzing: Motion + Skin Tones + Audio + Brightness")
            print(f"         Coverage: ALL sex scenes + drama + creampie + outro")
            
            # Dynamic sampling: More samples for longer videos
            sample_density = max(100, int(video_duration_minutes * 1.2))  # ~1.2 samples per minute
            
            timestamps = self.detector.find_best_scenes(
                num_clips=num_clips,
                sample_size=sample_density,
                max_workers=max_workers
            )
            
            if not timestamps or len(timestamps) < num_clips:
                print(f"⚠️ Only found {len(timestamps)} scenes")
                # Fallback shouldn't happen with advanced detector
            
            # Convert timestamps to (timestamp, duration) tuples
            timestamps = [(t, clip_duration) for t in timestamps]
            
            print(f"✓ Selected {len(timestamps)} best scenes across entire video")
            
            # Step 3: Extract clips
            print("\n[3/5] Extracting clips...")
            clip_files = self.extractor.extract_multiple_clips(
                timestamps,
                resolution=resolution,
                crf=crf,
                fps=fps,
                speed=speed_multiplier,
                parallel=parallel,
                max_workers=max_workers
            )
            
            if not clip_files:
                print("✗ No clips extracted")
                return result
            
            print(f"✓ Extracted {len(clip_files)} clips")
            
            # Step 4: Concatenate clips
            print("\n[4/5] Creating preview video...")
            success = self.extractor.concatenate_clips(
                clip_files,
                output_path,
                add_transitions=False  # Set to True for fade transitions
            )
            
            if not success:
                print("✗ Failed to create preview")
                if cleanup:
                    self.extractor.cleanup_clips(clip_files)
                return result
            
            print(f"✓ Preview created: {output_path}")
            
            # Step 5: Create GIF (optional)
            if create_gif:
                print("\n[5/5] Creating GIF version...")
                gif_success = self.extractor.create_gif(
                    output_path,
                    gif_path,
                    width=gif_width,
                    fps=15,
                    max_colors=128
                )
                
                if gif_success:
                    print(f"✓ GIF created: {gif_path}")
                else:
                    print("✗ GIF creation failed")
            else:
                print("\n[5/5] Skipping GIF creation")
            
            # Cleanup temporary files
            if cleanup:
                print("\nCleaning up temporary files...")
                self.extractor.cleanup_clips(clip_files)
                print("✓ Cleanup complete")
            
            # Calculate results
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                result = {
                    'success': True,
                    'video_path': output_path,
                    'gif_path': gif_path if create_gif and os.path.exists(gif_path) else None,
                    'num_clips': len(clip_files),
                    'total_duration': len(timestamps) * clip_duration,
                    'actual_duration': len(timestamps) * clip_duration / speed_multiplier,
                    'speed_multiplier': speed_multiplier,
                    'file_size_mb': file_size / (1024 * 1024),
                    'resolution': resolution,
                    'fps': fps,
                    'crf': crf
                }
                
                if result['gif_path']:
                    gif_size = os.path.getsize(result['gif_path'])
                    result['gif_size_mb'] = gif_size / (1024 * 1024)
            
            print("\n" + "=" * 60)
            print("PREVIEW GENERATION COMPLETE")
            print("=" * 60)
            print(f"Video: {result['video_path']}")
            print(f"Size: {result['file_size_mb']:.1f} MB")
            print(f"Clips: {result['num_clips']} (dynamically selected)")
            if result.get('speed_multiplier', 1.0) > 1.0:
                print(f"Duration: {result['actual_duration']:.1f}s @ {result['speed_multiplier']}x speed")
            else:
                print(f"Duration: {result['total_duration']:.1f}s")
            print(f"Coverage: Full video - all sex scenes + drama + outro")
            if result['gif_path']:
                print(f"GIF: {result['gif_path']} ({result['gif_size_mb']:.1f} MB)")
            print("=" * 60)
            
            return result
            
        except Exception as e:
            print(f"\n✗ Error generating preview: {e}")
            import traceback
            traceback.print_exc()
            return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python preview_generator.py <video_file> [options]")
        print("\nOptions:")
        print("  --output PATH       Output file path")
        print("  --target N          Target duration in seconds (default: auto-calculated)")
        print("  --clips N           Number of clips (default: auto-calculated)")
        print("  --duration N        Clip duration in seconds (default: 2.5)")
        print("  --resolution N      Target height (default: 360)")
        print("  --crf N             Compression quality 18-28 (default: 23)")
        print("  --fps N             Frame rate (default: 30)")
        print("  --gif               Also create GIF version")
        print("  --gif-width N       GIF width (default: 480)")
        print("  --no-cleanup        Keep temporary clip files")
        print("  --no-parallel       Disable parallel processing")
        print("  --workers N         Max parallel workers (default: 32)")
        print("\nDynamic Mode (default):")
        print("  Automatically determines optimal number of clips based on video length")
        print("  Captures ALL sex scenes, drama, creampie moments, and outro")
        print("\nExamples:")
        print("  python preview_generator.py video.mp4")
        print("  python preview_generator.py video.mp4 --target 60")
        print("  python preview_generator.py video.mp4 --workers 32 --gif")
        sys.exit(1)
    
    video_file = sys.argv[1]
    
    # Check if video file exists
    if not os.path.exists(video_file):
        print(f"Error: Video file not found: {video_file}")
        sys.exit(1)
    
    # Parse arguments
    args = {
        'output_path': None,
        'target_duration': None,  # Auto-calculate by default
        'clip_duration': 2.5,
        'resolution': '360',
        'crf': 23,
        'fps': 30,
        'create_gif': False,
        'gif_width': 480,
        'cleanup': True,
        'parallel': True,
        'max_workers': 32
    }
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '--output' and i + 1 < len(sys.argv):
            args['output_path'] = sys.argv[i + 1]
            i += 2
        elif arg == '--target' and i + 1 < len(sys.argv):
            args['target_duration'] = float(sys.argv[i + 1])
            i += 2
        elif arg == '--clips' and i + 1 < len(sys.argv):
            # Override auto-calculation
            target = float(sys.argv[i + 1]) * args['clip_duration']
            args['target_duration'] = target
            i += 2
        elif arg == '--duration' and i + 1 < len(sys.argv):
            args['clip_duration'] = float(sys.argv[i + 1])
            i += 2
        elif arg == '--resolution' and i + 1 < len(sys.argv):
            args['resolution'] = sys.argv[i + 1]
            i += 2
        elif arg == '--crf' and i + 1 < len(sys.argv):
            args['crf'] = int(sys.argv[i + 1])
            i += 2
        elif arg == '--fps' and i + 1 < len(sys.argv):
            args['fps'] = int(sys.argv[i + 1])
            i += 2
        elif arg == '--gif':
            args['create_gif'] = True
            i += 1
        elif arg == '--gif-width' and i + 1 < len(sys.argv):
            args['gif_width'] = int(sys.argv[i + 1])
            i += 2
        elif arg == '--no-cleanup':
            args['cleanup'] = False
            i += 1
        elif arg == '--no-parallel':
            args['parallel'] = False
            i += 1
        elif arg == '--workers' and i + 1 < len(sys.argv):
            args['max_workers'] = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    # Generate preview
    try:
        generator = PreviewGenerator(video_file)
        result = generator.generate_preview(**args)
        
        if result['success']:
            sys.exit(0)
        else:
            print(f"\nError: Preview generation failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
