# Design Document

## Overview

This design addresses critical bugs, edge cases, and robustness issues in the preview generation system. The system consists of 8 Python modules that work together to create video previews from adult content. The primary issues include import errors, division by zero, file path handling, subprocess management, memory leaks, race conditions, and insufficient error handling.

The design focuses on making the system production-ready by:
1. Fixing import mechanisms to work in all execution contexts
2. Adding comprehensive input validation and error handling
3. Implementing proper resource cleanup and timeout management
4. Handling edge cases for very short and very long videos
5. Ensuring cross-platform compatibility (Windows/Unix)
6. Preventing race conditions in parallel processing
7. Optimizing memory usage for large video files

## Architecture

### Module Structure

The system maintains its existing modular architecture with the following components:

```
preview_generator/
├── __init__.py                    # Package initialization with proper imports
├── preview_generator.py           # Main orchestrator
├── comprehensive_detector.py      # Full video scene detection
├── scene_detector.py              # Advanced scene detection
├── fast_scene_detector.py         # Fast parallel detection
├── motion_detector.py             # Motion-based detection
├── adult_scene_detector.py        # Multi-factor detection
├── clip_extractor.py              # Clip extraction and concatenation
└── workflow_integration.py        # Pipeline integration
```

### Import Resolution Strategy

To fix import errors, we implement a dual-import strategy:

1. **Relative imports** for package usage: `from .module import Class`
2. **Absolute imports** with fallback for standalone execution:
   ```python
   try:
       from .module import Class  # Package import
   except ImportError:
       from module import Class   # Standalone import
   ```

3. **Path manipulation** for standalone scripts:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
   ```

### Error Handling Architecture

All modules follow a consistent error handling pattern:

1. **Input Validation Layer**: Validates all inputs before processing
2. **Subprocess Wrapper Layer**: Wraps all FFmpeg/FFprobe calls with timeout and error handling
3. **Resource Cleanup Layer**: Ensures cleanup in finally blocks
4. **Logging Layer**: Provides consistent, informative error messages

### Resource Management

Implement context managers and explicit cleanup:

1. **Temporary File Manager**: Tracks and cleans up all temporary files
2. **Subprocess Manager**: Tracks and terminates all subprocesses
3. **Memory Manager**: Explicitly releases large numpy arrays

## Components and Interfaces

### 1. Import System (`__init__.py`)

**Purpose**: Provide clean package-level imports and handle import errors gracefully.

**Interface**:
```python
# __init__.py
__version__ = "1.0.0"

# Import main classes with error handling
try:
    from .preview_generator import PreviewGenerator
    from .comprehensive_detector import ComprehensiveDetector
    from .scene_detector import SceneDetector
    from .fast_scene_detector import FastSceneDetector
    from .motion_detector import MotionDetector
    from .adult_scene_detector import AdultSceneDetector
    from .clip_extractor import ClipExtractor
    from .workflow_integration import WorkflowIntegration
    
    __all__ = [
        'PreviewGenerator',
        'ComprehensiveDetector',
        'SceneDetector',
        'FastSceneDetector',
        'MotionDetector',
        'AdultSceneDetector',
        'ClipExtractor',
        'WorkflowIntegration'
    ]
except ImportError as e:
    import sys
    print(f"Warning: Failed to import preview_generator modules: {e}", file=sys.stderr)
    __all__ = []
```

### 2. Validation Module (`validation.py`)

**Purpose**: Centralized input validation for all modules.

**Interface**:
```python
class ValidationError(Exception):
    """Raised when validation fails"""
    pass

def validate_video_path(path: str) -> str:
    """Validate video file path exists and is readable"""
    
def validate_timestamp(timestamp: float, duration: float) -> float:
    """Validate timestamp is within video duration"""
    
def validate_duration(duration: float, max_duration: float = None) -> float:
    """Validate duration is positive and within bounds"""
    
def validate_resolution(resolution: str) -> int:
    """Validate resolution string and return height as int"""
    
def validate_fps(fps: float) -> float:
    """Validate FPS is positive and reasonable"""
    
def validate_crf(crf: int) -> int:
    """Validate CRF is in valid range (0-51)"""
```

### 3. Subprocess Wrapper (`subprocess_utils.py`)

**Purpose**: Wrap all subprocess calls with consistent error handling, timeouts, and logging.

**Interface**:
```python
class SubprocessError(Exception):
    """Raised when subprocess fails"""
    pass

class SubprocessTimeoutError(SubprocessError):
    """Raised when subprocess times out"""
    pass

def run_ffmpeg(
    args: List[str],
    timeout: int = 120,
    check: bool = True,
    capture_output: bool = True
) -> subprocess.CompletedProcess:
    """Run FFmpeg command with error handling"""
    
def run_ffprobe(
    args: List[str],
    timeout: int = 10,
    check: bool = True
) -> subprocess.CompletedProcess:
    """Run FFprobe command with error handling"""
    
def check_ffmpeg_installed() -> bool:
    """Check if FFmpeg is installed and accessible"""
```

### 4. Path Utilities (`path_utils.py`)

**Purpose**: Handle file paths correctly across platforms.

**Interface**:
```python
def normalize_path(path: str) -> str:
    """Normalize path for current platform"""
    
def escape_path_for_ffmpeg(path: str) -> str:
    """Escape path for FFmpeg concat file"""
    
def get_safe_filename(filename: str) -> str:
    """Remove or escape special characters in filename"""
    
def ensure_unique_path(path: str) -> str:
    """Generate unique path if file exists"""
```

### 5. Resource Manager (`resource_manager.py`)

**Purpose**: Track and clean up temporary files and subprocesses.

**Interface**:
```python
class ResourceManager:
    """Context manager for temporary resources"""
    
    def __init__(self, temp_dir: str = None):
        self.temp_dir = temp_dir
        self.temp_files: List[str] = []
        self.temp_dirs: List[str] = []
        
    def create_temp_file(self, suffix: str = ".mp4") -> str:
        """Create temporary file and track it"""
        
    def create_temp_dir(self) -> str:
        """Create temporary directory and track it"""
        
    def cleanup(self):
        """Clean up all tracked resources"""
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
```

### 6. Video Info Cache (`video_info.py`)

**Purpose**: Cache video metadata to avoid redundant FFprobe calls.

**Interface**:
```python
@dataclass
class VideoInfo:
    """Video metadata"""
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool
    file_path: str
    
class VideoInfoCache:
    """Cache for video metadata"""
    
    def __init__(self):
        self._cache: Dict[str, VideoInfo] = {}
        
    def get_video_info(self, video_path: str, force_refresh: bool = False) -> VideoInfo:
        """Get video info with caching"""
        
    def clear(self):
        """Clear cache"""
```

### 7. Constants Module (`constants.py`)

**Purpose**: Define all magic numbers as named constants.

**Interface**:
```python
# Timeout values (seconds)
FFPROBE_TIMEOUT = 10
FFMPEG_EXTRACT_TIMEOUT = 120
FFMPEG_CONCAT_TIMEOUT = 300
FFMPEG_SPEED_TIMEOUT = 600

# Default values
DEFAULT_FPS = 30.0
DEFAULT_RESOLUTION = "720"
DEFAULT_CRF = 23
DEFAULT_AUDIO_BITRATE = "192k"

# Validation bounds
MIN_VIDEO_DURATION = 1.0
MAX_VIDEO_DURATION = 36000.0  # 10 hours
MIN_FPS = 1.0
MAX_FPS = 120.0
MIN_CRF = 0
MAX_CRF = 51

# Memory limits
MAX_FRAME_WIDTH = 320
MAX_FRAME_HEIGHT = 180
MAX_PARALLEL_WORKERS = 8

# Disk space
MIN_FREE_SPACE_MB = 1000  # 1 GB minimum
```

### 8. Updated Module Interfaces

Each existing module is updated to use the new utility modules:

**ComprehensiveDetector**:
- Add input validation for all parameters
- Use VideoInfoCache instead of direct FFprobe calls
- Use SubprocessWrapper for all FFmpeg calls
- Use ResourceManager for temporary files
- Handle division by zero in interval calculations
- Validate timestamps before returning

**SceneDetector**:
- Add timeout handling for long videos
- Use path utilities for file operations
- Validate FPS before division
- Handle missing audio streams gracefully

**ClipExtractor**:
- Use ResourceManager for clip files
- Escape paths in concat files correctly
- Add disk space checks before extraction
- Handle empty clip lists
- Use unique filenames for parallel extraction

**All Detectors**:
- Add try-except blocks around numpy operations
- Explicitly delete large arrays after use
- Validate timestamps against video duration
- Handle corrupted video files gracefully

## Data Models

### VideoInfo

```python
@dataclass
class VideoInfo:
    """Video metadata with validation"""
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool
    file_path: str
    
    def __post_init__(self):
        """Validate fields after initialization"""
        if self.duration <= 0:
            raise ValueError(f"Invalid duration: {self.duration}")
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Invalid dimensions: {self.width}x{self.height}")
        if self.fps <= 0:
            raise ValueError(f"Invalid FPS: {self.fps}")
```

### ClipInfo

```python
@dataclass
class ClipInfo:
    """Information about an extracted clip"""
    timestamp: float
    duration: float
    file_path: str
    file_size_bytes: int
    
    def __post_init__(self):
        """Validate fields"""
        if self.timestamp < 0:
            raise ValueError(f"Invalid timestamp: {self.timestamp}")
        if self.duration <= 0:
            raise ValueError(f"Invalid duration: {self.duration}")
```

### ProcessingResult

```python
@dataclass
class ProcessingResult:
    """Result of a processing operation"""
    success: bool
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Error Handling

### Error Hierarchy

```python
class PreviewGeneratorError(Exception):
    """Base exception for preview generator"""
    pass

class ValidationError(PreviewGeneratorError):
    """Input validation failed"""
    pass

class VideoError(PreviewGeneratorError):
    """Video file or metadata error"""
    pass

class SubprocessError(PreviewGeneratorError):
    """Subprocess execution error"""
    pass

class SubprocessTimeoutError(SubprocessError):
    """Subprocess timeout"""
    pass

class ResourceError(PreviewGeneratorError):
    """Resource management error (disk space, memory)"""
    pass
```

### Error Handling Patterns

1. **Validation Errors**: Raise immediately with descriptive message
2. **Subprocess Errors**: Log stderr, clean up resources, then raise
3. **Timeout Errors**: Terminate process, clean up, log timeout duration
4. **Resource Errors**: Clean up partial work, log resource state
5. **Unexpected Errors**: Log full traceback, clean up, re-raise

### Logging Strategy

```python
import logging

# Module-level logger
logger = logging.getLogger(__name__)

# Log levels:
# - DEBUG: Detailed information for debugging
# - INFO: Progress updates and successful operations
# - WARNING: Recoverable issues (using defaults, skipping items)
# - ERROR: Operation failures
# - CRITICAL: System-level failures

# Format: [Module] Level: Message
# Example: [ComprehensiveDetector] ERROR: Failed to extract clip at 120.5s: timeout
```

## Testing Strategy

### Unit Tests

Focus on specific edge cases and error conditions:

1. **Validation Tests**:
   - Test each validation function with valid and invalid inputs
   - Test boundary conditions (zero, negative, extremely large values)
   - Test special characters in file paths

2. **Path Handling Tests**:
   - Test Windows paths with backslashes
   - Test Unix paths with forward slashes
   - Test Unicode filenames
   - Test paths with spaces and special characters

3. **Error Handling Tests**:
   - Test subprocess timeout handling
   - Test FFmpeg failure scenarios
   - Test corrupted video file handling
   - Test missing FFmpeg/FFprobe

4. **Edge Case Tests**:
   - Test very short videos (< 10 seconds)
   - Test very long videos (> 4 hours)
   - Test videos without audio
   - Test videos with invalid FPS
   - Test empty clip lists

5. **Resource Management Tests**:
   - Test temporary file cleanup
   - Test cleanup on exception
   - Test concurrent access to temp files

### Property-Based Tests

Property-based tests will be written after completing the prework analysis in the next section.

### Integration Tests

1. **End-to-End Tests**:
   - Test complete preview generation workflow
   - Test with various video formats and durations
   - Test parallel processing with multiple videos

2. **Cross-Platform Tests**:
   - Test on Windows and Linux
   - Test path handling on both platforms
   - Test subprocess execution on both platforms

### Test Configuration

- Minimum 100 iterations per property test
- Each property test tagged with: **Feature: preview-generator-bug-fixes, Property {N}: {description}**
- Use pytest for test framework
- Use hypothesis for property-based testing
- Mock FFmpeg/FFprobe calls where appropriate for speed


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection

After analyzing all acceptance criteria, several redundancies were identified:
- Properties 4.1 and 4.5 both test subprocess timeout handling (consolidated into Property 1)
- Properties 8.1 and 8.3 both test clip count adjustment for short videos (consolidated into Property 8)
- Properties 10.2 and 10.4 both test corrupted file detection (consolidated into Property 11)
- Properties 11.1 and 11.2 both test audio existence checking (consolidated into Property 13)
- Properties 14.1, 14.3, and 14.4 all test empty clip list handling (consolidated into Property 17)
- Properties 15.1, 15.2, and 15.4 all test timestamp validation (consolidated into Property 18)
- Properties 17.1 and 17.4 both test video info caching (consolidated into Property 22)
- Properties 5.2 and 17.2 both test frame resolution limiting (consolidated into Property 5)

### Property 1: Subprocess Timeout Enforcement

*For any* subprocess operation with a specified timeout, if the subprocess exceeds the timeout duration, the system should terminate the process and raise a SubprocessTimeoutError.

**Validates: Requirements 4.1, 4.5**

### Property 2: Zero Division Prevention

*For any* division operation in the system, if the divisor is zero or would result in division by zero, the system should either use a safe default value or raise a ValidationError.

**Validates: Requirements 2.2, 2.3, 2.4**

### Property 3: Windows Path Escaping

*For any* file path on Windows platform, when creating a concat file, backslashes should be converted to forward slashes or properly escaped.

**Validates: Requirements 3.1**

### Property 4: FFmpeg Path Formatting

*For any* file path passed to FFmpeg commands, the path should be properly formatted with forward slashes or escaped backslashes.

**Validates: Requirements 3.2**

### Property 5: Frame Resolution Limiting

*For any* frame extraction operation, the extracted frame resolution should not exceed MAX_FRAME_WIDTH × MAX_FRAME_HEIGHT.

**Validates: Requirements 5.2, 17.2**

### Property 6: Unique Parallel Filenames

*For any* parallel clip extraction operation, all generated clip filenames should be unique (no duplicates).

**Validates: Requirements 6.1**

### Property 7: Clip File Synchronization

*For any* clip concatenation operation, all input clip files should exist and be fully written (non-zero size) before concatenation begins.

**Validates: Requirements 6.3**

### Property 8: Short Video Clip Adjustment

*For any* video where duration is less than (num_clips × clip_duration), the system should reduce the number of clips to fit within the video duration.

**Validates: Requirements 8.1, 8.3**

### Property 9: Timestamp Bounds Validation

*For any* timestamp calculation, the resulting timestamp should be greater than or equal to 0 and less than or equal to the video duration.

**Validates: Requirements 8.2**

### Property 10: Long Video Optimization

*For any* video with duration greater than 3600 seconds (1 hour), expensive scene detection operations should be skipped.

**Validates: Requirements 9.1**

### Property 11: Video Duration Validation

*For any* video info retrieval, the duration value should be positive, finite, and less than MAX_VIDEO_DURATION.

**Validates: Requirements 10.1, 10.2, 10.4**

### Property 12: Video Dimension Validation

*For any* video info retrieval, the width and height values should be positive integers greater than zero.

**Validates: Requirements 10.3**

### Property 13: Audio Stream Conditional Processing

*For any* video without an audio stream (has_audio = False), audio analysis operations should be skipped and return default values.

**Validates: Requirements 11.1, 11.2, 11.4**

### Property 14: Audio Codec Parameter Omission

*For any* clip extraction from a video without audio, the FFmpeg command should not include audio codec parameters (-c:a, -b:a).

**Validates: Requirements 11.3**

### Property 15: FPS Validation and Clamping

*For any* frame rate value, if the FPS is zero, negative, or outside the range [MIN_FPS, MAX_FPS], the system should clamp it to valid bounds or use DEFAULT_FPS.

**Validates: Requirements 12.1, 12.3, 12.4**

### Property 16: Disk Space Pre-Check

*For any* clip extraction operation, before starting extraction, the system should verify that available disk space exceeds MIN_FREE_SPACE_MB plus estimated output size.

**Validates: Requirements 13.1, 13.2**

### Property 17: Empty Clip List Rejection

*For any* concatenation operation, if the clip list is empty (length = 0), the system should raise an error before attempting to create a concat file or call FFmpeg.

**Validates: Requirements 14.1, 14.3, 14.4**

### Property 18: Timestamp Adjustment

*For any* timestamp value, if the timestamp is negative, it should be adjusted to 0; if it exceeds video duration, it should be adjusted to (duration - clip_duration).

**Validates: Requirements 15.1, 15.2, 15.4**

### Property 19: Clip Duration Adjustment

*For any* clip extraction where (timestamp + clip_duration) exceeds video duration, the clip duration should be reduced to (video_duration - timestamp).

**Validates: Requirements 15.3**

### Property 20: Concurrent Filename Uniqueness

*For any* set of concurrent operations using the same temporary directory, all generated temporary filenames should be unique across all operations.

**Validates: Requirements 16.1**

### Property 21: Cleanup Safety

*For any* cleanup operation, only files that were created by the current ResourceManager instance should be removed.

**Validates: Requirements 16.3**

### Property 22: Video Info Caching

*For any* video file path, if get_video_info() is called multiple times with the same path and force_refresh=False, FFprobe should only be executed once (subsequent calls return cached result).

**Validates: Requirements 17.1, 17.4**

### Property 23: Error Log Module Identification

*For any* error log message, the message should include the module name in the format "[ModuleName]".

**Validates: Requirements 18.1**

### Property 24: Error Log Consistency

*For any* two error log messages from different modules, they should follow the same format pattern: "[ModuleName] Level: Message".

**Validates: Requirements 18.2**

### Property 25: Parameter Type Validation

*For any* function call with typed parameters, if a parameter has the wrong type, the system should raise a TypeError or ValidationError before processing.

**Validates: Requirements 19.1**

### Property 26: File Existence Validation

*For any* function parameter that expects a file path, if the file does not exist, the system should raise a FileNotFoundError or ValidationError.

**Validates: Requirements 19.2**

### Property 27: Numeric Range Validation

*For any* numeric parameter with defined bounds, if the value is outside the valid range, the system should raise a ValueError with a message indicating the valid range.

**Validates: Requirements 19.3, 19.4**

### Property 28: Subprocess Error Capture

*For any* subprocess that fails (non-zero exit code), the system should capture stderr output and include it in the raised exception message.

**Validates: Requirements 4.3, 7.1**

### Property 29: Subprocess Cleanup on Failure

*For any* subprocess that fails or times out, all temporary files created by that subprocess should be cleaned up.

**Validates: Requirements 4.2**

### Property 30: Parallel Subprocess Tracking

*For any* set of parallel subprocesses, all subprocess handles should be tracked and all should be terminated/cleaned up when the operation completes or fails.

**Validates: Requirements 4.4**

### Property 31: Unicode Path Handling

*For any* file path containing Unicode characters, the path should be correctly encoded for subprocess calls without raising UnicodeEncodeError.

**Validates: Requirements 3.3**

### Property 32: Special Character Escaping

*For any* file path containing special characters (spaces, quotes, parentheses), the path should be properly escaped for FFmpeg concat files.

**Validates: Requirements 3.5**

### Property 33: File Conflict Resolution

*For any* file creation operation, if the target file already exists, the system should either overwrite it safely (with -y flag) or generate a unique filename.

**Validates: Requirements 6.4**

### Property 34: JSON Parse Error Handling

*For any* FFprobe output, if the JSON parsing fails, the system should raise a VideoError with a message indicating JSON parse failure.

**Validates: Requirements 7.2**

### Property 35: Non-Zero Exit Code Handling

*For any* subprocess with check=True, if the exit code is non-zero, the system should raise a SubprocessError.

**Validates: Requirements 7.3**

### Property 36: Corrupted Video Detection

*For any* video file where FFprobe fails to extract metadata, the system should raise a VideoError indicating the file may be corrupted.

**Validates: Requirements 7.5**

### Property 37: Long Video Sample Reduction

*For any* video with duration greater than 14400 seconds (4 hours), the sample size for analysis should be reduced to avoid excessive processing time.

**Validates: Requirements 9.5**

### Property 38: Concatenation Timeout Scaling

*For any* concatenation operation with N clips, the timeout value should scale appropriately (e.g., base_timeout + N × per_clip_timeout).

**Validates: Requirements 9.4**

### Property 39: Extraction Failure Logging

*For any* clip extraction operation where all clips fail, the system should log the failure reason for each timestamp.

**Validates: Requirements 14.2**

### Property 40: Debug Mode Traceback Logging

*For any* exception caught in debug mode (logging level DEBUG), the full traceback should be logged.

**Validates: Requirements 18.3**

### Property 41: Error Context Inclusion

*For any* operation failure, the error message should include context information (file path, timestamp, or operation type).

**Validates: Requirements 18.4**
