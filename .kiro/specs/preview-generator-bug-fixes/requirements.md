# Requirements Document

## Introduction

The preview generation system is a Python-based video processing pipeline that creates preview videos from adult content. The system consists of multiple modules that work together to detect scenes, extract clips, and generate previews. This specification addresses critical bugs, edge cases, and robustness issues that prevent the system from handling real-world scenarios reliably.

## Glossary

- **Preview_Generator**: Main system that orchestrates preview video creation
- **Scene_Detector**: Module that identifies interesting scenes in videos using various detection methods
- **Clip_Extractor**: Module that extracts video segments and concatenates them
- **FFmpeg**: External command-line tool for video processing
- **FFprobe**: External command-line tool for video metadata extraction
- **Subprocess**: Python mechanism for executing external commands
- **CRF**: Constant Rate Factor - video quality parameter (lower = better quality)
- **Timestamp**: Position in video measured in seconds
- **Concat_File**: Text file listing video clips for concatenation

## Requirements

### Requirement 1: Import System Robustness

**User Story:** As a developer, I want the modules to import correctly regardless of how they are executed, so that the system works in different deployment scenarios.

#### Acceptance Criteria

1. WHEN a module is run as a standalone script, THE Import_System SHALL resolve all dependencies correctly
2. WHEN a module is imported from a different directory, THE Import_System SHALL locate sibling modules correctly
3. WHEN modules are packaged as a Python package, THE Import_System SHALL use relative imports appropriately
4. IF an import fails, THEN THE System SHALL provide a clear error message indicating which module is missing

### Requirement 2: Division by Zero Prevention

**User Story:** As a system operator, I want the system to handle videos with zero or invalid durations gracefully, so that processing does not crash.

#### Acceptance Criteria

1. WHEN calculating intervals with zero duration, THE System SHALL detect the condition and return an error
2. WHEN a video has zero frames per second, THE System SHALL use a default FPS value
3. WHEN dividing by segment count, THE System SHALL validate that the divisor is non-zero
4. IF any division operation would result in division by zero, THEN THE System SHALL log a warning and use a safe default value

### Requirement 3: File Path Handling

**User Story:** As a system operator, I want the system to handle file paths correctly on both Windows and Unix systems, so that video processing works across platforms.

#### Acceptance Criteria

1. WHEN creating concat files on Windows, THE System SHALL escape backslashes in file paths
2. WHEN passing paths to FFmpeg, THE System SHALL use forward slashes or properly escaped backslashes
3. WHEN handling Unicode filenames, THE System SHALL encode paths correctly for subprocess calls
4. WHEN constructing absolute paths, THE System SHALL use os.path functions for platform independence
5. IF a file path contains special characters, THEN THE System SHALL escape them appropriately for FFmpeg

### Requirement 4: Subprocess Timeout and Cleanup

**User Story:** As a system operator, I want subprocess operations to timeout gracefully and clean up resources, so that hung processes do not block the system.

#### Acceptance Criteria

1. WHEN a subprocess exceeds its timeout, THE System SHALL terminate the process
2. WHEN a subprocess is terminated, THE System SHALL clean up any temporary files created
3. WHEN a subprocess fails, THE System SHALL capture and log stderr output
4. WHEN multiple subprocesses are running in parallel, THE System SHALL track and clean up all of them
5. IF a subprocess hangs, THEN THE System SHALL not wait indefinitely

### Requirement 5: Memory Management

**User Story:** As a system operator, I want the system to handle large video files without exhausting memory, so that processing does not crash or slow down the system.

#### Acceptance Criteria

1. WHEN processing large videos, THE System SHALL use streaming operations instead of loading entire files into memory
2. WHEN extracting frames, THE System SHALL limit frame resolution to reduce memory usage
3. WHEN analyzing multiple segments, THE System SHALL release memory after each segment
4. WHEN using numpy arrays, THE System SHALL explicitly delete arrays after use
5. IF available memory is low, THEN THE System SHALL reduce the number of parallel workers

### Requirement 6: Race Condition Prevention

**User Story:** As a system operator, I want parallel clip extraction to avoid file conflicts, so that clips are not corrupted or overwritten.

#### Acceptance Criteria

1. WHEN extracting clips in parallel, THE System SHALL use unique filenames for each clip
2. WHEN multiple processes access temporary files, THE System SHALL use file locking or unique directories
3. WHEN concatenating clips, THE System SHALL ensure all clips are fully written before reading
4. IF a clip file already exists, THEN THE System SHALL either overwrite it safely or generate a new filename

### Requirement 7: Error Handling for External Commands

**User Story:** As a system operator, I want all FFmpeg and FFprobe calls to handle errors gracefully, so that failures provide actionable information.

#### Acceptance Criteria

1. WHEN FFmpeg fails, THE System SHALL capture and log the error message
2. WHEN FFprobe returns invalid JSON, THE System SHALL handle the parsing error
3. WHEN a subprocess returns a non-zero exit code, THE System SHALL raise an appropriate exception
4. WHEN FFmpeg is not installed, THE System SHALL provide a clear error message
5. IF a video file is corrupted, THEN THE System SHALL detect it during metadata extraction and report the issue

### Requirement 8: Short Video Handling

**User Story:** As a system operator, I want the system to handle very short videos correctly, so that videos under 30 seconds can be processed.

#### Acceptance Criteria

1. WHEN a video is shorter than the minimum clip duration, THE System SHALL adjust the number of clips
2. WHEN calculating timestamps for short videos, THE System SHALL ensure timestamps are within bounds
3. WHEN a video is too short for the requested number of clips, THE System SHALL reduce the clip count
4. IF a video is less than 10 seconds, THEN THE System SHALL create a single clip or return an error

### Requirement 9: Long Video Handling

**User Story:** As a system operator, I want the system to handle very long videos efficiently, so that videos over 4 hours can be processed without timeouts.

#### Acceptance Criteria

1. WHEN processing videos longer than 1 hour, THE System SHALL skip expensive scene detection
2. WHEN analyzing long videos, THE System SHALL use sampling instead of full analysis
3. WHEN extracting clips from long videos, THE System SHALL use accurate seeking to avoid delays
4. WHEN concatenating many clips, THE System SHALL use appropriate timeout values
5. IF a video is longer than 4 hours, THEN THE System SHALL use a reduced sample size

### Requirement 10: Corrupted Video Detection

**User Story:** As a system operator, I want the system to detect corrupted video files early, so that processing fails fast with clear error messages.

#### Acceptance Criteria

1. WHEN getting video info, THE System SHALL validate that duration is positive and finite
2. WHEN FFprobe fails to read a video, THE System SHALL report the file as corrupted
3. WHEN video dimensions are invalid, THE System SHALL reject the video
4. IF a video file is truncated or incomplete, THEN THE System SHALL detect it during metadata extraction

### Requirement 11: Missing Audio Stream Handling

**User Story:** As a system operator, I want the system to handle videos without audio streams correctly, so that audio-based detection does not crash.

#### Acceptance Criteria

1. WHEN a video has no audio stream, THE System SHALL skip audio analysis
2. WHEN detecting audio peaks, THE System SHALL check if audio exists before processing
3. WHEN extracting clips from videos without audio, THE System SHALL not include audio codec parameters
4. IF audio detection is attempted on a video without audio, THEN THE System SHALL return a default score

### Requirement 12: Invalid Frame Rate Handling

**User Story:** As a system operator, I want the system to handle videos with invalid or zero frame rates, so that FPS calculations do not crash.

#### Acceptance Criteria

1. WHEN parsing frame rate from FFprobe, THE System SHALL validate the numerator and denominator
2. WHEN the frame rate denominator is zero, THE System SHALL use a default FPS value
3. WHEN the frame rate is invalid or missing, THE System SHALL default to 30 FPS
4. IF the frame rate is extremely high or low, THEN THE System SHALL clamp it to reasonable bounds

### Requirement 13: Disk Space Validation

**User Story:** As a system operator, I want the system to check available disk space before extracting clips, so that processing does not fail due to disk full errors.

#### Acceptance Criteria

1. WHEN starting clip extraction, THE System SHALL check available disk space
2. WHEN estimated output size exceeds available space, THE System SHALL return an error
3. WHEN temporary files are created, THE System SHALL monitor disk space usage
4. IF disk space falls below a threshold during processing, THEN THE System SHALL stop and clean up

### Requirement 14: Empty Clip List Handling

**User Story:** As a system operator, I want the system to handle cases where no clips are extracted, so that concatenation does not fail with cryptic errors.

#### Acceptance Criteria

1. WHEN no clips are successfully extracted, THE System SHALL return an error before attempting concatenation
2. WHEN clip extraction fails for all timestamps, THE System SHALL log the reasons
3. WHEN the clip list is empty, THE System SHALL not create a concat file
4. IF concatenation is attempted with zero clips, THEN THE System SHALL raise a clear error

### Requirement 15: Invalid Timestamp Handling

**User Story:** As a system operator, I want the system to validate timestamps before extraction, so that clips are not extracted beyond video duration.

#### Acceptance Criteria

1. WHEN a timestamp exceeds video duration, THE System SHALL adjust it to a valid range
2. WHEN a timestamp is negative, THE System SHALL reject it or adjust to zero
3. WHEN clip end time exceeds video duration, THE System SHALL reduce the clip duration
4. IF a timestamp is invalid, THEN THE System SHALL log a warning and skip that clip

### Requirement 16: Concurrent Access Safety

**User Story:** As a system operator, I want the system to handle concurrent processing safely, so that multiple instances do not interfere with each other.

#### Acceptance Criteria

1. WHEN multiple processes use the same temporary directory, THE System SHALL use unique subdirectories or filenames
2. WHEN accessing shared resources, THE System SHALL use appropriate locking mechanisms
3. WHEN cleaning up temporary files, THE System SHALL only remove files it created
4. IF another process is using a file, THEN THE System SHALL wait or use a different filename

### Requirement 17: Performance Optimization

**User Story:** As a system operator, I want the system to avoid redundant operations, so that processing is as fast as possible.

#### Acceptance Criteria

1. WHEN video info is needed multiple times, THE System SHALL cache the result
2. WHEN extracting frames for analysis, THE System SHALL use reduced resolution
3. WHEN possible, THE System SHALL use parallel processing for independent operations
4. IF video info has already been retrieved, THEN THE System SHALL not call FFprobe again

### Requirement 18: Consistent Error Messages

**User Story:** As a developer, I want error messages to be consistent and informative, so that debugging is easier.

#### Acceptance Criteria

1. WHEN an error occurs, THE System SHALL include the module name in the log message
2. WHEN logging errors, THE System SHALL use consistent formatting across all modules
3. WHEN an exception is caught, THE System SHALL log the full traceback in debug mode
4. IF an operation fails, THEN THE System SHALL indicate which file or timestamp caused the failure

### Requirement 19: Input Validation

**User Story:** As a developer, I want all function parameters to be validated, so that invalid inputs are caught early.

#### Acceptance Criteria

1. WHEN a function receives parameters, THE System SHALL validate types and ranges
2. WHEN a file path is provided, THE System SHALL check if the file exists
3. WHEN numeric parameters are provided, THE System SHALL ensure they are within valid ranges
4. IF a parameter is invalid, THEN THE System SHALL raise a ValueError with a descriptive message

### Requirement 20: Configuration Constants

**User Story:** As a developer, I want magic numbers to be replaced with named constants, so that the code is more maintainable.

#### Acceptance Criteria

1. WHEN hardcoded values are used, THE System SHALL define them as module-level constants
2. WHEN timeout values are needed, THE System SHALL use configurable constants
3. WHEN quality parameters are used, THE System SHALL define them with descriptive names
4. IF a constant needs to be changed, THEN it SHALL be changed in one place only
