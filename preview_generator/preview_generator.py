#!/usr/bin/env python3
"""
Advanced Preview Generator
Main orchestrator for creating smart video previews
"""
import os
import sys
from scene_detector import SceneDetector
from clip_extractor import ClipExtractor

class PreviewGenerator:
    def __init__(self, video_path: str, output_dir: str = None):
        self.video_path = video_path
        self.output_dir = output_dir or os.path.dirname(os.path.abspath(video_path)) or '.'
        
        self.detector = SceneDetector(video_path)
        self.extractor = ClipExtractor(video_path, self.output_dir)
    
    def generate_preview(
        self,
        output_path: str = None,
        num_clips: int = 10,
        clip_duration: float = 3.0,
        resolution: str = "720",
        crf: int = 28,
        fps: int = 30,
        create_gif: bool = False,
        gif_width: int = 480,
        cleanup: bool = True,
        parallel: bool = True,
        max_workers: int = None
    ) -> dict:
        """
        Generate smart preview video with parallel processing
        
        Args:
            output_path: Output file path (default: video_preview.mp4)
            num_clips: Number of clips to extract
            clip_duration: Duration of each clip in seconds
            resolution: Target height (720, 480, etc.)
            crf: Compression quality (18-28, lower = better)
            fps: Target frame rate
            create_gif: Also create GIF version
            gif_width: GIF width in pixels
            cleanup: Remove temporary clip files
            parallel: Use parallel processing (faster)
            max_workers: Max parallel workers (default: CPU count)
        
        Returns:
            Dict with preview info and paths
        """
        print("=" * 60)
        print("ADVANCED PREVIEW GENERATOR")
        print("=" * 60)
        
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
            # Step 1: Get video info
            print("\n[1/5] Analyzing video...")
            info = self.detector.get_video_info()
            if not info:
                print("✗ Failed to get video info")
                return result
            
            print(f"✓ Video: {info['duration']:.1f}s, {info['width']}x{info['height']}, {info['fps']:.1f}fps")
            
            # Step 2: Detect scenes and analyze motion
            print("\n[2/5] Detecting scenes and analyzing motion...")
            timestamps = self.detector.get_smart_timestamps(
                num_clips=num_clips,
                clip_duration=clip_duration
            )
            
            if not timestamps:
                print("✗ No timestamps generated")
                return result
            
            print(f"✓ Generated {len(timestamps)} smart timestamps")
            
            # Step 3: Extract clips
            print("\n[3/5] Extracting clips...")
            clip_files = self.extractor.extract_multiple_clips(
                timestamps,
                resolution=resolution,
                crf=crf,
                fps=fps,
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
            print(f"Clips: {result['num_clips']}")
            print(f"Duration: {result['total_duration']:.1f}s")
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
        print("  --clips N           Number of clips (default: 10)")
        print("  --duration N        Clip duration in seconds (default: 3.0)")
        print("  --resolution N      Target height (default: 720)")
        print("  --crf N             Compression quality 18-28 (default: 28)")
        print("  --fps N             Frame rate (default: 30)")
        print("  --gif               Also create GIF version")
        print("  --gif-width N       GIF width (default: 480)")
        print("  --no-cleanup        Keep temporary clip files")
        print("  --no-parallel       Disable parallel processing")
        print("  --workers N         Max parallel workers (default: CPU count)")
        print("\nExample:")
        print("  python preview_generator.py video.mp4 --clips 10 --duration 3 --gif")
        sys.exit(1)
    
    video_file = sys.argv[1]
    
    # Check if video file exists
    if not os.path.exists(video_file):
        print(f"Error: Video file not found: {video_file}")
        sys.exit(1)
    
    # Parse arguments
    args = {
        'output_path': None,
        'num_clips': 10,
        'clip_duration': 3.0,
        'resolution': '720',
        'crf': 28,
        'fps': 30,
        'create_gif': False,
        'gif_width': 480,
        'cleanup': True,
        'parallel': True,
        'max_workers': None
    }
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '--output' and i + 1 < len(sys.argv):
            args['output_path'] = sys.argv[i + 1]
            i += 2
        elif arg == '--clips' and i + 1 < len(sys.argv):
            args['num_clips'] = int(sys.argv[i + 1])
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
