# Implementation Plan: GitHub Workflow Bug Fixes

## Overview

This implementation plan addresses 15 critical bugs and edge cases in the GitHub Actions workflow and Python scraping pipeline. The tasks are organized to fix the most critical issues first (syntax errors, race conditions) before moving to resilience improvements (retry logic, cleanup) and finally observability enhancements (logging, monitoring).

The implementation follows a test-driven approach where possible, with property-based tests written alongside core functionality to catch edge cases early.

## Tasks

### Phase 1: Critical Workflow Fixes (Requirements 1-2)

- [x] 1. Fix workflow YAML syntax error
  - [x] 1.1 Fix bash conditional syntax: change `else:` to `else` on line 127 of `.github/workflows/integrated_scraper.yml`
  - [x] 1.2 Add `fi` statement to close the if block properly
  - [x] 1.3 Test workflow parsing with `yamllint` or GitHub Actions validator
  **Validates: Requirements 1.1, 1.2, 1.3**

- [x] 2. Fix time extraction edge cases
  - [x] 2.1 Replace `sed 's/^0//'` with `sed 's/^0*$/0/' | sed 's/^0\([1-9]\)/\1/'` for CURRENT_MINUTE
  - [x] 2.2 Replace `sed 's/^0//'` with `sed 's/^0*$/0/' | sed 's/^0\([1-9]\)/\1/'` for CURRENT_HOUR
  - [x] 2.3 Alternative: Use `$((10#$(date +%M)))` and `$((10#$(date +%H)))` for more robust parsing
  - [x] 2.4 Add test cases for midnight (00:00) and top-of-hour (XX:00) scenarios
  **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 3. Align workflow and script timeout values
  - [x] 3.1 Update workflow timeout from 350 minutes to 360 minutes (6 hours)
  - [x] 3.2 Update Python script TIME_LIMIT from 5.5 hours to 5.25 hours (315 minutes)
  - [x] 3.3 Ensure 45-minute gap for cleanup and commit operations
  - [x] 3.4 Add time-remaining check before starting new videos in run_continuous.py
  **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

### Phase 2: Resource Management (Requirements 3, 7, 15)

- [-] 4. Implement atomic disk space reservation
  - [x] 4.1 Create `jable/disk_space_manager.py` with DiskSpaceManager class
  - [x] 4.2 Implement `reserve_space()` method with file locking
  - [x] 4.3 Implement `release_space()` method
  - [x] 4.4 Implement `get_available_space()` method that accounts for reservations
  - [x] 4.5 Implement `cleanup_stale_reservations()` method for orphaned reservations
  - [x] 4.6 Integrate disk space reservation into run_continuous.py before downloads
  - [ ] 4.7 Write property-based test for atomic reservation (Property 3)
  - [ ] 4.8 Write property-based test for reservation cleanup (Property 4)
  **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [-] 5. Implement comprehensive cleanup on crash
  - [x] 5.1 Create CleanupManager class in run_continuous.py
  - [x] 5.2 Register signal handlers for SIGTERM and SIGINT
  - [x] 5.3 Register atexit handler for normal exit cleanup
  - [x] 5.4 Implement cleanup_orphaned_files() to remove old temp files (>2 hours)
  - [x] 5.5 Implement segment folder cleanup (pattern: `.*_segments`)
  - [x] 5.6 Add workflow-level cleanup step with `if: always()` condition
  - [x] 5.7 Add emergency git stash and commit on workflow cancellation
  - [ ] 5.8 Write property-based test for temp file cleanup (Property 9)
  **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 15.1, 15.2, 15.3, 15.4**

### Phase 3: Data Integrity (Requirements 4, 8)

- [-] 6. Enhance database file locking
  - [x] 6.1 Add `filelock` library to requirements.txt
  - [x] 6.2 Update database_manager.py to use filelock library instead of custom FileLock
  - [x] 6.3 Implement `_get_lock()` method to manage lock instances
  - [x] 6.4 Implement `_read_json_locked()` with shared lock support
  - [x] 6.5 Implement `_write_json_locked()` with exclusive lock support
  - [x] 6.6 Add exponential backoff retry logic (2^attempt seconds, max 3 retries)
  - [x] 6.7 Update all database read/write operations to use locked methods
  - [ ] 6.8 Write property-based test for lock acquisition (Property 5)
  - [ ] 6.9 Write property-based test for lock retry with backoff (Property 6)
  **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [-] 7. Implement URL normalization and deduplication
  - [x] 7.1 Enhance `_normalize_url()` in database_manager.py to handle www prefix
  - [x] 7.2 Update `is_processed()` to use normalized URL comparison
  - [x] 7.3 Add URL normalization to video discovery in run_continuous.py
  - [x] 7.4 Add duplicate detection logging
  - [ ] 7.5 Write property-based test for URL normalization consistency (Property 10)
  **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Phase 4: Error Handling and Resilience (Requirements 6, 9, 10, 11, 14)

- [-] 8. Implement git push retry with exponential backoff
  - [x] 8.1 Refactor commit_database() into commit_database_with_retry()
  - [x] 8.2 Implement retry loop with max 3 attempts
  - [x] 8.3 Add exponential backoff (2, 4, 8 seconds)
  - [x] 8.4 Add pull-rebase on conflict detection
  - [x] 8.5 Add local backup creation if all retries fail
  - [x] 8.6 Add timeout handling for git operations
  - [ ] 8.7 Write property-based test for git push retry (Property 8)
  **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

- [x] 9. Implement API key validation
  - [x] 9.1 Add "Validate API keys" step to workflow before scraping
  - [x] 9.2 Check for required STREAMWISH_API_KEY environment variable
  - [x] 9.3 Check for optional LULUSTREAM_API_KEY and STREAMTAPE credentials
  - [x] 9.4 Add test API call to StreamWish to verify key validity
  - [x] 9.5 Fail workflow immediately with clear error if validation fails
  - [x] 9.6 Log which API keys are valid and which are missing
  **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

- [-] 10. Implement browser memory leak prevention
  - [x] 10.1 Create BrowserManager class in run_continuous.py
  - [x] 10.2 Implement get_scraper() with restart interval (every 5 videos)
  - [x] 10.3 Implement close() with process verification and force kill
  - [x] 10.4 Add orphaned browser process detection and cleanup
  - [x] 10.5 Integrate BrowserManager into main processing loop
  - [x] 10.6 Add browser restart after each successful video
  - [ ] 10.7 Write property-based test for browser lifecycle (Property 11)
  - [ ] 10.8 Write property-based test for browser restart policy (Property 12)
  **Validates: Requirements 10.1, 10.2, 10.3, 10.4**

- [-] 11. Implement discovery failure backoff
  - [x] 11.1 Create DiscoveryBackoff class in run_continuous.py
  - [x] 11.2 Implement record_failure() with backoff schedule (3→60s, 5→300s, 7→900s, 10→exit)
  - [x] 11.3 Implement record_success() to reset counter
  - [x] 11.4 Integrate backoff into main discovery loop
  - [x] 11.5 Add logging for failure count and wait times
  - [ ] 11.6 Write property-based test for discovery failure counter (Property 13)
  **Validates: Requirements 11.1, 11.2, 11.3, 11.4**

- [-] 12. Implement JAVDatabase integration fallback
  - [x] 12.1 Create JAVDatabaseClient class in run_continuous.py
  - [x] 12.2 Implement enrich_video() with max 2 retries and exponential backoff
  - [x] 12.3 Add consecutive failure tracking (mark unavailable after 5 failures)
  - [x] 12.4 Add availability check before enrichment attempts
  - [x] 12.5 Integrate JAVDatabaseClient into video processing workflow
  - [x] 12.6 Add logging for JAVDatabase availability status
  - [ ] 12.7 Write property-based test for JAVDatabase retry (Property 15)
  - [ ] 12.8 Write property-based test for availability tracking (Property 16)
  **Validates: Requirements 14.1, 14.2, 14.3, 14.4**

### Phase 5: Security and Observability (Requirements 12, 13)

- [-] 13. Implement credential masking
  - [x] 13.1 Create mask_credentials() function in run_continuous.py
  - [x] 13.2 Mask GITHUB_TOKEN, STREAMWISH_API_KEY, LULUSTREAM_API_KEY, STREAMTAPE_API_KEY
  - [x] 13.3 Add regex patterns for URL-embedded tokens (https://TOKEN@github.com)
  - [x] 13.4 Add regex patterns for API keys in URLs (?key=TOKEN)
  - [x] 13.5 Update log() function to apply credential masking
  - [x] 13.6 Update commit_database() to mask credentials in git output
  - [ ] 13.7 Write property-based test for credential masking (Property 14)
  **Validates: Requirements 12.1, 12.2, 12.3, 12.4**

- [ ] 14. Implement workflow cancellation handling
  - [ ] 14.1 Add trap for SIGTERM and SIGINT in workflow commit step
  - [ ] 14.2 Implement git stash on cancellation signal
  - [ ] 14.3 Add uncommitted changes detection
  - [ ] 14.4 Implement stash pop and commit on cancellation
  - [ ] 14.5 Add push with error handling (continue if push fails)
  - [ ] 14.6 Ensure commit step runs with `if: always()` condition
  **Validates: Requirements 13.1, 13.2, 13.3, 13.4**

### Phase 6: Testing and Validation

- [-] 15. Write unit tests
  - [x] 15.1 Create `tests/test_time_extraction.py` for time parsing edge cases
  - [x] 15.2 Create `tests/test_url_normalization.py` for URL normalization
  - [x] 15.3 Create `tests/test_credential_masking.py` for credential masking
  - [-] 15.4 Create `tests/test_backoff_calculation.py` for exponential backoff
  - [ ] 15.5 Create `tests/test_lock_acquisition.py` for file locking
  **Validates: Testing Strategy - Unit Testing**

- [ ] 16. Write property-based tests
  - [ ] 16.1 Install hypothesis library for property-based testing
  - [ ] 16.2 Create `tests/test_properties.py` with all 16 correctness properties
  - [ ] 16.3 Configure hypothesis for minimum 100 iterations per test
  - [ ] 16.4 Tag each test with feature and property number
  - [ ] 16.5 Run property tests and verify all pass
  **Validates: Testing Strategy - Property-Based Testing**

- [ ] 17. Integration testing
  - [ ] 17.1 Test workflow with manual trigger in test environment
  - [ ] 17.2 Test concurrent scraper instances for race conditions
  - [ ] 17.3 Test workflow cancellation at various stages
  - [ ] 17.4 Test API key validation with missing/invalid keys
  - [ ] 17.5 Test time-based scheduling at midnight and top-of-hour
  **Validates: Testing Strategy - Integration Testing**

### Phase 7: Documentation and Cleanup

- [ ] 18. Update documentation
  - [ ] 18.1 Document new DiskSpaceManager usage
  - [ ] 18.2 Document BrowserManager usage
  - [ ] 18.3 Document JAVDatabaseClient usage
  - [ ] 18.4 Update README with new features and fixes
  - [ ] 18.5 Add troubleshooting guide for common issues

- [ ] 19. Final validation
  - [ ] 19.1 Run complete test suite
  - [ ] 19.2 Verify all 15 requirements are addressed
  - [ ] 19.3 Verify all 16 correctness properties pass
  - [ ] 19.4 Run workflow end-to-end in production
  - [ ] 19.5 Monitor for 24 hours to ensure stability