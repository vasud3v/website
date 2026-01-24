# Preview Generator - Quick Reference

## 🚀 Quick Start

```bash
# Basic usage (recommended)
python preview_generator.py video.mp4

# Output: 45-second preview with creampie scenes guaranteed
```

## 📋 Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--target N` | 45.0 | Target duration in seconds |
| `--duration N` | 2.5 | Duration of each clip |
| `--workers N` | 32 | Parallel workers |
| `--resolution N` | 720 | Target height (width auto) |
| `--crf N` | 23 | Quality (18-28, lower=better) |
| `--fps N` | 30 | Frame rate |
| `--gif` | false | Also create GIF |
| `--output PATH` | auto | Custom output path |

## 💻 Python API

### Basic Usage
```python
from preview_generator import PreviewGenerator

generator = PreviewGenerator("video.mp4")
result = generator.generate_preview()

if result['success']:
    print(f"Preview: {result['video_path']}")
    print(f"Duration: {result['total_duration']}s")
    print(f"Clips: {result['num_clips']}")
```

### Advanced Usage
```python
result = generator.generate_preview(
    target_duration=60.0,   # 60 seconds
    clip_duration=3.0,      # 3s per clip
    resolution="1080",      # 1080p
    crf=20,                 # Very high quality
    max_workers=64,         # 64 workers
    create_gif=True         # Also create GIF
)
```

### Workflow Integration
```python
from preview_generator.workflow_integration import integrate_with_workflow

result = integrate_with_workflow(
    video_path="video.mp4",
    video_code="CODE-123",
    video_title="Video Title",
    upload_function=upload_to_streamwish,
    folder_name="JAV_VIDEOS/CODE-123",
    target_duration=45.0,
    max_workers=32
)

if result and result['success']:
    print(f"Preview URL: {result['preview_video_url']}")
```

## 🎯 Key Features

### ✅ Creampie Detection (GUARANTEED)
- Analyzes last 20% of video
- Guarantees 2-3 clips from climax region
- High skin + intense motion + loud audio
- **Never miss the money shot!**

### ✅ Full Video Coverage
- 0% to 100% (includes intro/outro)
- Better scene distribution
- More representative preview

### ✅ 32 Parallel Workers
- 5-10x faster processing
- Concurrent analysis and extraction
- Optimized for multi-core CPUs

### ✅ High Quality Output
- CRF 23 (high quality)
- 720p default
- MP4 format (H.264 + AAC)
- 3-5 MB for 45 seconds

## 📊 Performance

| Video Length | Processing Time | Output Size |
|--------------|-----------------|-------------|
| 30 minutes | ~50-60 seconds | 3-4 MB |
| 60 minutes | ~70-80 seconds | 3-5 MB |
| 120 minutes | ~110-120 seconds | 3-5 MB |

*With 32 workers on modern CPU*

## 🎬 Scene Distribution

For 45-second preview (18 clips):
- **Clips 1-3**: Intro/setup (0-20%)
- **Clips 4-12**: Main action (20-80%)
- **Clips 13-18**: **CREAMPIE** (80-100%) ⭐

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| FFmpeg not found | Install FFmpeg, add to PATH |
| Too slow | Increase `--workers` |
| Out of memory | Reduce `--workers` |
| Poor quality | Lower `--crf` (18-20) |
| Large file size | Increase `--crf` (25-28) |

## 📝 Examples

### Example 1: Basic Preview
```bash
python preview_generator.py video.mp4
```
**Output**: 45s preview, 720p, CRF 23, 32 workers

### Example 2: High Quality
```bash
python preview_generator.py video.mp4 --crf 18 --resolution 1080
```
**Output**: 45s preview, 1080p, CRF 18 (very high quality)

### Example 3: Longer Preview
```bash
python preview_generator.py video.mp4 --target 60
```
**Output**: 60s preview with more clips

### Example 4: Maximum Speed
```bash
python preview_generator.py video.mp4 --workers 64
```
**Output**: 45s preview with 64 workers (fastest)

### Example 5: With GIF
```bash
python preview_generator.py video.mp4 --gif --gif-width 640
```
**Output**: 45s preview + animated GIF

## 🎯 Best Practices

### For Adult Content
- Use default settings (optimized for adult content)
- Creampie detection is automatic
- 45 seconds is ideal length
- 720p is good balance of quality/size

### For Large Libraries
- Use 32+ workers for speed
- Process in batches
- Monitor CPU/memory usage
- Consider lower CRF for smaller files

### For High Quality
- Use CRF 18-20
- Use 1080p resolution
- Use 60 fps if source supports
- Expect larger file sizes

## 📈 Quality Settings

| CRF | Quality | File Size | Use Case |
|-----|---------|-----------|----------|
| 18 | Excellent | Large | Archive quality |
| 20 | Very High | Medium-Large | Premium content |
| 23 | High | Medium | **Recommended** |
| 25 | Good | Small | Web streaming |
| 28 | Medium | Very Small | Low bandwidth |

## 🔍 Detection Thresholds

### Creampie Detection
- **Skin tone**: > 40 (high skin presence)
- **Motion**: > 30 OR **Audio**: > 40
- **Location**: Last 20% of video
- **Guaranteed**: 2-3 clips minimum

### Scene Scoring
- **Skin tone**: 40% weight
- **Motion**: 30% weight
- **Audio**: 20% weight
- **Complexity**: 10% weight

## 💡 Tips

1. **Default settings work great** - No need to customize for most cases
2. **Creampie detection is automatic** - Just run and it works
3. **More workers = faster** - Use up to your CPU core count
4. **Lower CRF = better quality** - But larger files
5. **Test with one video first** - Then batch process

## 📚 Documentation

- **README.md**: Full documentation
- **IMPROVEMENTS.md**: Detailed improvements
- **FEATURES.md**: Visual feature highlights
- **CHANGELOG.md**: Version history
- **QUICK_REFERENCE.md**: This file

## 🎉 Summary

**One command to rule them all:**
```bash
python preview_generator.py video.mp4
```

**Result:**
- ✅ 45-second preview
- ✅ Creampie scenes guaranteed
- ✅ Full video coverage
- ✅ High quality (CRF 23)
- ✅ Fast processing (32 workers)
- ✅ Professional output

**Perfect for adult content!**
