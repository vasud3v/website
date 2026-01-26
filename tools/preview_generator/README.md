# Advanced Preview Generator

Intelligent video preview generator that captures ALL sex scenes, intro, and outro in under 45 seconds using multi-factor scene detection and parallel processing.

## Features

### 🎯 Full Video Coverage
- **Captures entire video**: Analyzes from 0% to 100% (including intro and outro)
- **Smart scene detection**: Uses multi-factor analysis to find the best moments
- **No skipping**: Unlike basic generators that skip first/last 5%, this covers everything

### 🚀 High-Performance Parallel Processing
- **32 parallel workers** by default (configurable)
- **Concurrent analysis**: Analyzes multiple segments simultaneously
- **Fast extraction**: Extracts clips in parallel using multiprocessing
- **Optimized for speed**: Processes long videos quickly

### 🧠 Multi-Factor Scene Detection
Intelligent scene scoring based on:
- **Skin tone detection** (40% weight) - Identifies adult content scenes
- **Motion intensity** (30% weight) - Finds dynamic, action-filled moments
- **Audio levels** (20% weight) - Detects moaning, talking, and sound peaks
- **Visual complexity** (10% weight) - Prefers detailed, interesting frames

### 🎯 Creampie/Climax Scene Detection
**GUARANTEED capture of creampie/climax scenes:**
- **Automatic detection**: Analyzes last 20% of video for climax scenes
- **Priority selection**: Ensures 2-3 clips (or 20% of total) from climax region
- **Smart identification**: Detects high skin tone + intense motion + loud audio
- **Never miss**: Always includes the money shot in your preview

### ⚙️ Configurable Output
- **Target duration**: Default 45 seconds (configurable)
- **Clip duration**: 2.5 seconds per clip (configurable)
- **Quality**: CRF 23 (high quality) by default
- **Resolution**: 720p default (maintains aspect ratio)
- **Format**: MP4 with H.264 + AAC
- **Optional GIF**: Can generate animated GIF version

## Usage

### Basic Usage

```bash
python preview_generator.py video.mp4
```

This will:
- Analyze the entire video (0-100%)
- **Detect and prioritize creampie/climax scenes** (last 20%)
- Extract ~18 clips (45s ÷ 2.5s per clip)
- **Guarantee 2-3 clips from creampie region**
- Create a 45-second preview at 720p
- Use 32 parallel workers for speed

### Advanced Usage

```bash
# Custom target duration and workers
python preview_generator.py video.mp4 --target 60 --workers 16

# Specific clip duration
python preview_generator.py video.mp4 --duration 3.0 --target 45

# With GIF output
python preview_generator.py video.mp4 --gif --gif-width 640

# Custom quality and resolution
python preview_generator.py video.mp4 --crf 20 --resolution 1080 --fps 60

# Keep temporary clips for inspection
python preview_generator.py video.mp4 --no-cleanup
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--target N` | Target total duration in seconds | 45.0 |
| `--duration N` | Duration of each clip in seconds | 2.5 |
| `--workers N` | Max parallel workers | 32 |
| `--resolution N` | Target height (width auto-calculated) | 720 |
| `--crf N` | Compression quality (18-28, lower=better) | 23 |
| `--fps N` | Target frame rate | 30 |
| `--gif` | Also create GIF version | false |
| `--gif-width N` | GIF width in pixels | 480 |
| `--output PATH` | Custom output file path | auto |
| `--no-cleanup` | Keep temporary clip files | false |
| `--no-parallel` | Disable parallel processing | false |

## Workflow Integration

### Python API

```python
from preview_generator import PreviewGenerator

# Initialize
generator = PreviewGenerator("video.mp4")

# Generate preview
result = generator.generate_preview(
    target_duration=45.0,  # 45 seconds total
    clip_duration=2.5,     # 2.5s per clip
    resolution="720",      # 720p
    crf=23,                # High quality
    max_workers=32,        # 32 parallel workers
    create_gif=False,      # No GIF
    parallel=True          # Enable parallel processing
)

if result['success']:
    print(f"Preview: {result['video_path']}")
    print(f"Size: {result['file_size_mb']:.1f} MB")
    print(f"Duration: {result['total_duration']:.1f}s")
    print(f"Clips: {result['num_clips']}")
```

### Workflow Integration

```python
from preview_generator.workflow_integration import integrate_with_workflow

# Integrate with upload workflow
result = integrate_with_workflow(
    video_path="video.mp4",
    video_code="CODE-123",
    video_title="Video Title",
    upload_function=upload_to_streamwish,
    folder_name="JAV_VIDEOS/CODE-123",
    enable_preview=True,
    enable_gif=False,
    target_duration=45.0,
    max_workers=32
)

if result and result['success']:
    print(f"Preview URL: {result['preview_video_url']}")
```

## How It Works

### 1. Video Analysis
- Extracts video metadata (duration, resolution, fps, audio)
- Calculates number of clips needed for target duration
- Determines sample points across entire video (0-100%)

### 2. Scene Detection (Parallel)
- **Keyframe detection**: Samples every 8 seconds across full video
- **Sound peak detection**: Analyzes 40 points for audio peaks
- **Creampie detection**: Focuses on last 20% for climax scenes (PRIORITY)
- **Candidate selection**: Combines all detection methods
- **Parallel analysis**: Uses 32 workers to analyze segments simultaneously

### 3. Multi-Factor Scoring
Each segment is scored on:
- **Skin tone** (40%): RGB-based skin detection
- **Motion** (30%): Frame-to-frame variance
- **Audio** (20%): Volume levels (mean + max)
- **Complexity** (10%): Visual entropy

### 4. Diversity Enforcement with Creampie Priority
- **PRIORITY 1**: Selects 2-3 best clips from last 20% (creampie/climax region)
- **PRIORITY 2**: Divides remaining video into sections
- Selects best clip from each section
- Ensures coverage across entire video
- **Guarantees creampie scenes are included**

### 5. Clip Extraction (Parallel)
- Extracts clips using 32 parallel workers
- Applies quality settings (CRF, resolution, fps)
- Optimizes for fast encoding (preset: fast)

### 6. Concatenation
- Combines clips into single preview
- Optional fade transitions
- Optimized for streaming (faststart flag)

## Performance

### Speed Improvements
- **32 parallel workers**: 10-20x faster than sequential processing
- **Concurrent analysis**: Analyzes multiple segments at once
- **Optimized sampling**: Smart sampling reduces analysis time
- **Fast encoding**: Uses FFmpeg fast preset

### Example Timings
| Video Length | Analysis Time | Extraction Time | Total Time |
|--------------|---------------|-----------------|------------|
| 30 minutes | ~15-20s | ~30-40s | ~50-60s |
| 60 minutes | ~25-30s | ~40-50s | ~70-80s |
| 120 minutes | ~40-50s | ~60-70s | ~110-120s |

*Times with 32 workers on modern CPU*

## Requirements

- Python 3.7+
- FFmpeg (with libx264 and AAC support)
- NumPy
- Sufficient CPU cores for parallel processing

### Installation

```bash
# Install Python dependencies
pip install numpy

# Install FFmpeg (if not already installed)
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Output Quality

### Video Preview
- **Format**: MP4 (H.264 + AAC)
- **Quality**: CRF 23 (high quality, ~3-5 MB for 45s)
- **Resolution**: 720p default (maintains aspect ratio)
- **Frame rate**: 30 fps default
- **Audio**: AAC 96kbps
- **Optimization**: Fast start enabled for streaming

### GIF Preview (Optional)
- **Format**: Animated GIF
- **Quality**: 128 colors with dithering
- **Size**: 480px width default
- **Frame rate**: 15 fps
- **Optimization**: Palette-based encoding

## Advanced Configuration

### Custom Scene Detection

```python
from preview_generator.adult_scene_detector import AdultSceneDetector

detector = AdultSceneDetector("video.mp4")

# Find best scenes with custom parameters
timestamps = detector.find_best_scenes(
    num_clips=20,        # More clips
    sample_size=150,     # Analyze more segments
    max_workers=64       # More workers
)
```

### Custom Clip Extraction

```python
from preview_generator.clip_extractor import ClipExtractor

extractor = ClipExtractor("video.mp4")

# Extract clips with custom settings
clips = extractor.extract_multiple_clips(
    timestamps=[(10.0, 3.0), (30.0, 3.0)],  # (start, duration)
    resolution="1080",
    crf=18,              # Very high quality
    fps=60,              # High frame rate
    parallel=True,
    max_workers=32
)
```

## Troubleshooting

### "FFmpeg not found"
Install FFmpeg and ensure it's in your PATH.

### "Too slow"
- Increase `max_workers` (up to CPU core count)
- Reduce `sample_size` for faster analysis
- Lower resolution or increase CRF for faster encoding

### Poor scene selection
- Increase `sample_size` for more thorough analysis
- Adjust `target_duration` and `clip_duration`
- Check video has audio (audio detection helps)
- Creampie scenes are automatically prioritized from last 20%

### "Out of memory"
- Reduce `max_workers`
- Process shorter videos
- Lower resolution

## License

MIT License - See LICENSE file for details
