#!/usr/bin/env python3
"""
Create video preview/highlight from downloaded video
Extracts 10-15 second clips from different parts of the video
"""
import os
import subprocess
import random

def create_preview(video_path, output_path=None, duration=15, num_clips=3):
    """
    Create a preview video by extracting clips from different parts
    
    Args:
        video_path: Path to the full video file
        output_path: Path for output preview (default: video_path with _preview suffix)
        duration: Duration of each clip in seconds (default: 15)
        num_clips: Number of clips to extract (default: 3)
    
    Returns:
        Path to created preview file, or None if failed
    """
    if not os.path.exists(video_path):
        print(f"[Preview] ❌ Video file not found: {video_path}")
        return None
    
    # Get video duration
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ], capture_output=True, text=True, timeout=30)
        
        total_duration = float(result.stdout.strip())
        print(f"[Preview] Video duration: {total_duration:.1f}s")
    except Exception as e:
        print(f"[Preview] ❌ Could not get video duration: {e}")
        return None
    
    # Skip if video is too short
    if total_duration < duration * num_clips + 60:
        print(f"[Preview] ⚠️ Video too short for preview ({total_duration:.1f}s)")
        return None
    
    # Generate output path
    if not output_path:
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_preview{ext}"
    
    print(f"[Preview] Creating {num_clips} clips of {duration}s each...")
    
    # Calculate clip positions (avoid first/last 30 seconds)
    safe_duration = total_duration - 60
    segment_size = safe_duration / num_clips
    
    clip_files = []
    temp_dir = os.path.dirname(video_path)
    
    try:
        # Extract clips
        for i in range(num_clips):
            # Random position within each segment
            segment_start = 30 + (i * segment_size)
            segment_end = segment_start + segment_size
            start_time = random.uniform(segment_start, segment_end - duration)
            
            clip_path = os.path.join(temp_dir, f"clip_{i}.mp4")
            clip_files.append(clip_path)
            
            print(f"[Preview] Extracting clip {i+1} from {start_time:.1f}s...")
            
            # Extract clip with re-encoding for consistency
            subprocess.run([
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', video_path,
                '-t', str(duration),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                clip_path
            ], capture_output=True, timeout=120)
            
            if not os.path.exists(clip_path):
                print(f"[Preview] ❌ Failed to create clip {i+1}")
                raise Exception(f"Clip {i+1} creation failed")
        
        # Create concat file
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for clip in clip_files:
                # Use forward slashes and escape for ffmpeg
                clip_basename = os.path.basename(clip)
                f.write(f"file '{clip_basename}'\n")
        
        print(f"[Preview] Concatenating clips...")
        
        # Concatenate clips - use absolute path for concat file
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', os.path.abspath(concat_file),
            '-c', 'copy',
            os.path.abspath(output_path)
        ], capture_output=True, timeout=60)
        
        # Cleanup temp files
        for clip in clip_files:
            try:
                os.remove(clip)
            except:
                pass
        try:
            os.remove(concat_file)
        except:
            pass
        
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"[Preview] ✅ Created preview: {output_path} ({size_mb:.1f} MB)")
            return output_path
        else:
            print(f"[Preview] ❌ Preview file not created")
            return None
            
    except Exception as e:
        print(f"[Preview] ❌ Error creating preview: {e}")
        # Cleanup on error
        for clip in clip_files:
            try:
                os.remove(clip)
            except:
                pass
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python create_video_preview.py <video_file> [output_file]")
        sys.exit(1)
    
    video_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = create_preview(video_file, output_file)
    if result:
        print(f"✅ Preview created: {result}")
    else:
        print("❌ Failed to create preview")
        sys.exit(1)
