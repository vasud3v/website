#!/usr/bin/env python3
"""
Quick Preview Generator - No scene detection, just fast clip extraction
"""
import subprocess
import os
import sys

def get_video_duration(video_path):
    """Get video duration in seconds"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def create_quick_preview(video_path, output_path, num_clips=10, clip_duration=3):
    """Create preview by extracting clips at regular intervals"""
    print(f"Creating quick preview of {video_path}...")
    
    # Get video duration
    duration = get_video_duration(video_path)
    print(f"Video duration: {duration:.1f}s ({duration/60:.1f} minutes)")
    
    # Calculate timestamps at regular intervals
    # Skip first and last 5% to avoid intro/outro
    start_offset = duration * 0.05
    end_offset = duration * 0.95
    usable_duration = end_offset - start_offset
    
    interval = usable_duration / num_clips
    timestamps = [start_offset + (i * interval) for i in range(num_clips)]
    
    print(f"Extracting {num_clips} clips of {clip_duration}s each...")
    
    # Create filter complex for extracting all clips
    filter_parts = []
    for i, ts in enumerate(timestamps):
        filter_parts.append(f"[0:v]trim=start={ts:.2f}:duration={clip_duration},setpts=PTS-STARTPTS,scale=1280:720[v{i}]")
    
    # Concatenate all clips
    concat_inputs = ''.join(f"[v{i}]" for i in range(num_clips))
    filter_complex = ';'.join(filter_parts) + f";{concat_inputs}concat=n={num_clips}:v=1:a=0[outv]"
    
    # Build ffmpeg command
    cmd = [
        'ffmpeg', '-i', video_path,
        '-filter_complex', filter_complex,
        '-map', '[outv]',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '28',
        '-r', '30',
        '-y',
        output_path
    ]
    
    print("Running ffmpeg...")
    subprocess.run(cmd, check=True)
    
    # Get output file size
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n✓ Preview created: {output_path}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Duration: {num_clips * clip_duration}s")
    print(f"  Clips: {num_clips}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_preview.py <video_file> [output_file]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "preview.mp4"
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)
    
    create_quick_preview(video_path, output_path)
