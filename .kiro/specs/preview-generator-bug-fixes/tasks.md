# Implementation Plan: Preview Generator Bug Fixes

## Overview

This implementation plan addresses critical bugs, edge cases, and robustness issues in the preview generation system. The approach is to create new utility modules first (validation, subprocess handling, path utilities, resource management), then systematically update each existing module to use these utilities and add proper error handling.

## Tasks

- [ ] 1. Create utility modules foundation
  - [ ] 1.1 Create constants.py with all configuration constants
    - Define timeout values (FFPROBE_TIMEOUT, FFMPEG_EXTRACT_TIMEOUT, etc.)
    - Define default values (DEFAULT_FPS, DEFAULT_RESOLUTION, etc.)
    - Define validation bounds (MIN_VIDEO_DURATION, MAX_FPS, etc.)
    - Define memory and disk space limits
    - _Requirements: 20.1, 20.2, 20.3, 20.4_
  
  - [ ] 1.2 Create custom exception classes in exceptions.py
    - Implement PreviewGeneratorError base class
    - Implement ValidationError, VideoError, SubprocessError, SubprocessTimeoutError, ResourceError
    - Add descriptive __str__ methods for each exception
    - _Requirements: 7.3, 19.4_
  
  - [ ] 1.3 Create validation.py module with input validation functions
    - Implement validate_video_path() with file existence check
    - Implement validate_timestamp() with bounds checking
    - Implement validate_duration() with positive value check
    - Implement validate_resolution(), validate_fps(), validate_crf()
    - _Requirements: 19.1, 19.2, 19.3, 19.4_
  
  - [ ]* 1.4 Write property tests for validation module
    - **Property 25: Parameter Type Validation** - For any function call with typed parameters, wrong types should raise TypeError/ValidationError
    - **Property 26: File Existence Validation** - For any file path parameter, non-existent files should raise error
    - **Property 27: Numeric Range Validation** - For any numeric parameter outside bounds, should raise ValueError
    - **Validates: Requirements 19.1, 19.2, 19.3, 19.4**

- [ ] 2. Create subprocess and path utilities
  - [ ] 2.1 Create subprocess_utils.py with FFmpeg/FFprobe wrappers
    - Implement check_ffmpeg_installed() function
    - Implement run_ffmpeg() with timeout, error capture, and logging
    - Implement run_ffprobe() with timeout and JSON parsing
    - Add stderr capture and logging for all subprocess failures
    - _Requirements: 4.1, 4.3, 4.5, 7.1, 7.2, 7.3, 7.4_
  
  - [ ]* 2.2 Write property tests for subprocess utilities
    - **Property 1: Subprocess Timeout Enforcement** - For any subprocess exceeding timeout, should terminate and raise SubprocessTimeoutError
    - **Property 28: Subprocess Error Capture** - For any failed subprocess, should capture stderr in exception
    - **Property 34: JSON Parse Error Handling** - For any invalid FFprobe JSON, should raise VideoError
    - **Property 35: Non-Zero Exit Code Handling** - For any non-zero exit, should raise SubprocessError
    - **Validates: Requirements 4.1, 4.3, 4.5, 7.1, 7.2, 7.3**
  
  - [ ] 2.3 Create path_utils.py with cross-platform path handling
    - Implement normalize_path() for platform-independent paths
    - Implement escape_path_for_ffmpeg() with Windows backslash handling
    - Implement get_safe_filename() for special character handling
    - Implement ensure_unique_path() for file conflict resolution
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.4_
  
  - [ ]* 2.4 Write property tests for path utilities
    - **Property 3: Windows Path Escaping** - For any Windows path, backslashes should be escaped in concat files
    - **Property 4: FFmpeg Path Formatting** - For any path to FFmpeg, should use forward slashes or escaped backslashes
    - **Property 31: Unicode Path Handling** - For any Unicode path, should encode correctly without UnicodeEncodeError
    - **Property 32: Special Character Escaping** - For any path with special chars, should escape properly
    - **Property 33: File Conflict Resolution** - For any existing file, should overwrite safely or generate unique name
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.5, 6.4**

- [ ] 3. Create resource management and caching
  - [ ] 3.1 Create resource_manager.py with ResourceManager class
    - Implement __init__ with temp_files and temp_dirs tracking
    - Implement create_temp_file() with unique filename generation
    - Implement create_temp_dir() with unique directory creation
    - Implement cleanup() that removes only tracked resources
    - Implement context manager methods (__enter__, __exit__)
    - _Requirements: 4.2, 16.1, 16.3_
  
  - [ ]* 3.2 Write property tests for resource manager
    - **Property 29: Subprocess Cleanup on Failure** - For any failed subprocess, temp files should be cleaned up
    - **Property 21: Cleanup Safety** - For any cleanup, only owned files should be removed
    - **Property 20: Concurrent Filename Uniqueness** - For any concurrent operations, filenames should be unique
    - **Validates: Requirements 4.2, 16.1, 16.3**
  
  - [ ] 3.3 Create video_info.py with VideoInfo dataclass and caching
    - Implement VideoInfo dataclass with validation in __post_init__
    - Implement VideoInfoCache class with dictionary cache
    - Implement get_video_info() with caching logic and force_refresh parameter
    - Add validation for duration, dimensions, and FPS
    - _Requirements: 10.1, 10.2, 10.3, 17.1, 17.4_
  
  - [ ]* 3.4 Write property tests for video info caching
    - **Property 22: Video Info Caching** - For any repeated get_video_info() call, FFprobe should execute only once
    - **Property 11: Video Duration Validation** - For any video info, duration should be positive and finite
    - **Property 12: Video Dimension Validation** - For any video info, width and height should be positive
    - **Validates: Requirements 10.1, 10.2, 10.3, 17.1, 17.4**

- [ ] 4. Checkpoint - Ensure all utility modules work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Update comprehensive_detector.py with bug fixes
  - [ ] 5.1 Fix imports with dual-import strategy
    - Add try-except for relative imports with absolute fallback
    - Add sys.path manipulation for standalone execution
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ] 5.2 Add division by zero prevention
    - Validate segment_duration before division
    - Check num_sections is non-zero before division
    - Use safe defaults when divisor is zero
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ] 5.3 Fix file path handling in concat file creation
    - Use path_utils.escape_path_for_ffmpeg() for all paths
    - Convert Windows backslashes to forward slashes
    - Handle Unicode filenames correctly
    - _Requirements: 3.1, 3.2, 3.3, 3.5_
  
  - [ ] 5.4 Replace direct subprocess calls with subprocess_utils wrappers
    - Use run_ffmpeg() and run_ffprobe() wrappers
    - Add proper timeout handling for all operations
    - Capture and log stderr on failures
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 7.1, 7.3_
  
  - [ ] 5.5 Add video duration and timestamp validation
    - Validate timestamps are within video duration
    - Adjust timestamps that exceed duration
    - Handle negative timestamps
    - Validate clip durations don't exceed video end
    - _Requirements: 8.1, 8.2, 15.1, 15.2, 15.3_
  
  - [ ] 5.6 Use ResourceManager for temporary file cleanup
    - Wrap operations in ResourceManager context
    - Track concat files and temp clips
    - Ensure cleanup on exceptions
    - _Requirements: 4.2, 16.3_
  
  - [ ]* 5.7 Write property tests for comprehensive_detector fixes
    - **Property 2: Zero Division Prevention** - For any division, zero divisors should use safe defaults
    - **Property 9: Timestamp Bounds Validation** - For any timestamp, should be within [0, duration]
    - **Property 18: Timestamp Adjustment** - For any invalid timestamp, should adjust to valid range
    - **Property 19: Clip Duration Adjustment** - For any clip extending beyond video, duration should be reduced
    - **Validates: Requirements 2.2, 2.3, 2.4, 8.2, 15.1, 15.2, 15.3**

- [ ] 6. Update scene_detector.py with bug fixes
  - [ ] 6.1 Fix imports and add input validation
    - Add dual-import strategy
    - Validate all input parameters
    - _Requirements: 1.1, 1.2, 19.1, 19.2, 19.3_
  
  - [ ] 6.2 Add FPS validation and zero division prevention
    - Validate FPS before division operations
    - Use DEFAULT_FPS for zero or invalid FPS
    - Clamp FPS to reasonable bounds
    - _Requirements: 12.1, 12.2, 12.3, 12.4_
  
  - [ ] 6.3 Replace subprocess calls with wrappers
    - Use subprocess_utils for all FFmpeg/FFprobe calls
    - Add timeout handling for long videos
    - _Requirements: 4.1, 4.3, 7.1, 7.3_
  
  - [ ] 6.4 Add short and long video handling
    - Skip scene detection for videos > 1 hour
    - Adjust clip count for short videos
    - Validate video is long enough for requested clips
    - _Requirements: 8.1, 8.3, 9.1_
  
  - [ ]* 6.5 Write property tests for scene_detector fixes
    - **Property 15: FPS Validation and Clamping** - For any FPS value, should clamp to valid bounds or use default
    - **Property 8: Short Video Clip Adjustment** - For any short video, should reduce clip count to fit
    - **Property 10: Long Video Optimization** - For any video > 1 hour, should skip expensive operations
    - **Validates: Requirements 8.1, 8.3, 9.1, 12.1, 12.3, 12.4**

- [ ] 7. Update clip_extractor.py with bug fixes
  - [ ] 7.1 Fix imports and add validation
    - Add dual-import strategy
    - Validate all parameters (timestamps, resolution, CRF, FPS)
    - _Requirements: 1.1, 1.2, 19.1, 19.3_
  
  - [ ] 7.2 Fix concat file path escaping
    - Use path_utils.escape_path_for_ffmpeg()
    - Handle Windows paths correctly
    - Handle Unicode and special characters
    - _Requirements: 3.1, 3.2, 3.3, 3.5_
  
  - [ ] 7.3 Add unique filename generation for parallel extraction
    - Use ResourceManager for clip tracking
    - Ensure unique filenames across parallel workers
    - Add file conflict resolution
    - _Requirements: 6.1, 6.4, 16.1_
  
  - [ ] 7.4 Add disk space validation
    - Check available disk space before extraction
    - Estimate output size and validate sufficient space
    - Raise error if insufficient space
    - _Requirements: 13.1, 13.2_
  
  - [ ] 7.5 Add empty clip list handling
    - Validate clip list is not empty before concatenation
    - Log reasons for extraction failures
    - Raise clear error for empty lists
    - _Requirements: 14.1, 14.2, 14.3, 14.4_
  
  - [ ] 7.6 Add clip file synchronization
    - Verify all clip files exist before concatenation
    - Check files are non-zero size
    - Sort clips chronologically by filename
    - _Requirements: 6.3_
  
  - [ ]* 7.7 Write property tests for clip_extractor fixes
    - **Property 6: Unique Parallel Filenames** - For any parallel extraction, filenames should be unique
    - **Property 7: Clip File Synchronization** - For any concatenation, all clips should exist and be complete
    - **Property 16: Disk Space Pre-Check** - For any extraction, should verify sufficient disk space
    - **Property 17: Empty Clip List Rejection** - For any empty clip list, should raise error before concatenation
    - **Validates: Requirements 6.1, 6.3, 13.1, 13.2, 14.1, 14.3, 14.4**

- [ ] 8. Update motion_detector.py and fast_scene_detector.py
  - [ ] 8.1 Fix imports in both modules
    - Add dual-import strategy
    - Add input validation
    - _Requirements: 1.1, 1.2, 19.1_
  
  - [ ] 8.2 Add FPS and duration validation
    - Validate FPS before use
    - Handle zero or invalid FPS
    - Validate video duration
    - _Requirements: 10.1, 12.1, 12.3_
  
  - [ ] 8.3 Replace subprocess calls with wrappers
    - Use subprocess_utils wrappers
    - Add timeout handling
    - _Requirements: 4.1, 4.3, 7.1_
  
  - [ ] 8.4 Add memory management for numpy arrays
    - Limit frame resolution for analysis
    - Explicitly delete arrays after use
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [ ]* 8.5 Write property tests for detector fixes
    - **Property 5: Frame Resolution Limiting** - For any frame extraction, resolution should not exceed limits
    - **Property 30: Parallel Subprocess Tracking** - For any parallel subprocesses, all should be tracked and cleaned up
    - **Validates: Requirements 4.4, 5.2, 17.2**

- [ ] 9. Update adult_scene_detector.py with bug fixes
  - [ ] 9.1 Fix imports and add validation
    - Add dual-import strategy
    - Validate all parameters
    - _Requirements: 1.1, 1.2, 19.1_
  
  - [ ] 9.2 Add audio stream handling
    - Check has_audio before audio operations
    - Skip audio analysis for videos without audio
    - Return default scores when audio missing
    - Omit audio codec parameters for no-audio videos
    - _Requirements: 11.1, 11.2, 11.3, 11.4_
  
  - [ ] 9.3 Replace subprocess calls and add timeout handling
    - Use subprocess_utils wrappers
    - Add appropriate timeouts for all operations
    - _Requirements: 4.1, 4.3, 7.1_
  
  - [ ] 9.4 Add memory management for frame analysis
    - Limit frame resolution
    - Delete numpy arrays after use
    - _Requirements: 5.2, 5.4_
  
  - [ ]* 9.5 Write property tests for adult_scene_detector fixes
    - **Property 13: Audio Stream Conditional Processing** - For any video without audio, audio operations should be skipped
    - **Property 14: Audio Codec Parameter Omission** - For any no-audio video, FFmpeg commands should omit audio parameters
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4**

- [ ] 10. Update preview_generator.py with bug fixes
  - [ ] 10.1 Fix imports and add validation
    - Add dual-import strategy
    - Validate video_path exists
    - Validate all parameters
    - _Requirements: 1.1, 1.2, 19.1, 19.2_
  
  - [ ] 10.2 Use VideoInfoCache for video metadata
    - Replace direct get_video_info() calls with cached version
    - Avoid redundant FFprobe calls
    - _Requirements: 17.1, 17.4_
  
  - [ ] 10.3 Add ResourceManager for cleanup
    - Wrap operations in ResourceManager context
    - Ensure cleanup on exceptions
    - _Requirements: 4.2, 16.3_
  
  - [ ] 10.4 Add consistent error logging
    - Include module name in all log messages
    - Use consistent format across all errors
    - Include context (file, timestamp) in errors
    - _Requirements: 18.1, 18.2, 18.4_
  
  - [ ]* 10.5 Write property tests for preview_generator fixes
    - **Property 23: Error Log Module Identification** - For any error log, should include module name
    - **Property 24: Error Log Consistency** - For any two error logs, should follow same format
    - **Property 41: Error Context Inclusion** - For any failure, should include context information
    - **Validates: Requirements 18.1, 18.2, 18.4**

- [ ] 11. Update workflow_integration.py with bug fixes
  - [ ] 11.1 Fix imports and add validation
    - Add dual-import strategy
    - Validate video_path, video_code, video_title
    - _Requirements: 1.1, 1.2, 19.1, 19.2_
  
  - [ ] 11.2 Add error handling for upload failures
    - Wrap upload operations in try-except
    - Clean up preview files on upload failure
    - Log detailed error information
    - _Requirements: 7.1, 18.4_
  
  - [ ] 11.3 Use ResourceManager for preview file cleanup
    - Track preview and GIF files
    - Ensure cleanup after upload
    - _Requirements: 4.2, 16.3_
  
  - [ ] 11.4 Add long video handling
    - Reduce sample size for videos > 4 hours
    - Scale timeouts based on video duration
    - _Requirements: 9.4, 9.5_
  
  - [ ]* 11.5 Write property tests for workflow_integration fixes
    - **Property 37: Long Video Sample Reduction** - For any video > 4 hours, sample size should be reduced
    - **Property 38: Concatenation Timeout Scaling** - For any concatenation with N clips, timeout should scale appropriately
    - **Validates: Requirements 9.4, 9.5**

- [ ] 12. Checkpoint - Ensure all modules updated correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Update __init__.py for proper package imports
  - [ ] 13.1 Create comprehensive __init__.py
    - Add try-except for all imports
    - Define __all__ with exported classes
    - Add version information
    - Handle import errors gracefully
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ]* 13.2 Write integration tests for package imports
    - Test importing as package
    - Test running modules as standalone scripts
    - Test importing from different directories
    - Test error messages for missing dependencies
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [ ] 14. Add edge case handling tests
  - [ ]* 14.1 Write unit tests for very short videos
    - Test videos < 10 seconds
    - Test videos < clip duration
    - Test single-clip generation
    - **Validates: Requirements 8.1, 8.4**
  
  - [ ]* 14.2 Write unit tests for very long videos
    - Test videos > 1 hour (scene detection skip)
    - Test videos > 4 hours (sample reduction)
    - Test timeout scaling
    - **Validates: Requirements 9.1, 9.5**
  
  - [ ]* 14.3 Write unit tests for corrupted videos
    - Test FFprobe failures
    - Test invalid JSON from FFprobe
    - Test truncated video files
    - **Validates: Requirements 7.5, 10.2, 10.4**
  
  - [ ]* 14.4 Write unit tests for videos without audio
    - Test audio detection skipping
    - Test default score returns
    - Test FFmpeg command parameter omission
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
  
  - [ ]* 14.5 Write unit tests for invalid FPS
    - Test zero FPS
    - Test negative FPS
    - Test extremely high/low FPS
    - Test missing FPS
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4**

- [ ] 15. Add cross-platform compatibility tests
  - [ ]* 15.1 Write tests for Windows path handling
    - Test backslash escaping
    - Test UNC paths
    - Test drive letters
    - **Validates: Requirements 3.1, 3.2**
  
  - [ ]* 15.2 Write tests for Unix path handling
    - Test forward slashes
    - Test absolute paths
    - Test relative paths
    - **Validates: Requirements 3.2, 3.4**
  
  - [ ]* 15.3 Write tests for Unicode filenames
    - Test various Unicode characters
    - Test emoji in filenames
    - Test non-ASCII characters
    - **Validates: Requirements 3.3**
  
  - [ ]* 15.4 Write tests for special characters
    - Test spaces in paths
    - Test quotes in paths
    - Test parentheses and brackets
    - **Validates: Requirements 3.5**

- [ ] 16. Add resource management tests
  - [ ]* 16.1 Write tests for disk space validation
    - Test insufficient disk space detection
    - Test space estimation
    - Test error raising on low space
    - **Validates: Requirements 13.1, 13.2, 13.4**
  
  - [ ]* 16.2 Write tests for temporary file cleanup
    - Test cleanup on success
    - Test cleanup on exception
    - Test cleanup with ResourceManager
    - **Validates: Requirements 4.2, 16.3**
  
  - [ ]* 16.3 Write tests for concurrent access
    - Test unique filename generation
    - Test file locking behavior
    - Test cleanup safety
    - **Validates: Requirements 16.1, 16.3, 16.4**

- [ ] 17. Add debug logging tests
  - [ ]* 17.1 Write tests for traceback logging
    - Test traceback logging in debug mode
    - Test no traceback in non-debug mode
    - **Validates: Requirements 18.3**
  
  - [ ]* 17.2 Write tests for error context
    - Test file path in error messages
    - Test timestamp in error messages
    - Test operation type in error messages
    - **Validates: Requirements 18.4**

- [ ] 18. Final checkpoint - Run full test suite
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- All property tests should be tagged with: **Feature: preview-generator-bug-fixes, Property {N}: {description}**
