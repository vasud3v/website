# Requirements Document

## Introduction

This specification addresses critical bugs, edge cases, and race conditions in the GitHub Actions workflow (`.github/workflows/integrated_scraper.yml`) and associated Python scripts (`jable/run_continuous.py`, `database_manager.py`) that run a 24/7 video scraping pipeline. The system scrapes videos from Jable.tv, downloads them, uploads to hosting services (StreamWish, LuluStream, StreamTape), and manages metadata in JSON databases. The identified issues range from syntax errors that prevent workflow execution to race conditions that could cause data corruption or resource exhaustion.

## Glossary

- **Workflow**: The GitHub Actions YAML file that orchestrates the scraping pipeline
- **Scraper**: The Python script (`run_continuous.py`) that performs video discovery, download, and upload
- **Database_Manager**: Centralized Python module for managing JSON database files
- **Browser**: Selenium WebDriver instance used for web scraping
- **Hosting_Service**: Video hosting platforms (StreamWish, LuluStream, StreamTape)
- **Rate_Limit**: Upload quota restriction imposed by hosting services
- **Process_Lock**: File-based mechanism to prevent concurrent workflow instances
- **Temp_Directory**: Temporary storage location for downloaded video files
- **Git_Push**: Operation to commit and push database changes to GitHub repository
- **Time_Window**: The 20-minute gap between Python script timeout (330 min) and workflow timeout (350 min)

## Requirements

### Requirement 1: Fix Critical YAML Syntax Error

**User Story:** As a DevOps engineer, I want the workflow YAML to be syntactically correct, so that GitHub Actions can execute the workflow without parsing errors.

#### Acceptance Criteria

1. WHEN the workflow YAML is parsed by GitHub Actions, THE Workflow SHALL NOT contain syntax errors
2. THE Workflow SHALL use correct bash conditional syntax with `else` instead of `else:`
3. WHEN the workflow is triggered, THE Workflow SHALL execute the determine-action job successfully

### Requirement 2: Handle Time-Based Edge Cases

**User Story:** As a system operator, I want time-based logic to handle edge cases like midnight and top-of-hour, so that the workflow scheduling works correctly at all times.

#### Acceptance Criteria

1. WHEN the current minute is "00", THE Workflow SHALL handle the empty string case after `sed 's/^0//'` gracefully
2. WHEN the current hour is "00" (midnight), THE Workflow SHALL handle the empty string case after `sed 's/^0//'` gracefully
3. WHEN extracting time values, THE Workflow SHALL use a method that preserves "00" as "0" instead of producing empty strings
4. WHEN comparing time values in conditionals, THE Workflow SHALL handle both numeric zero and empty string cases

### Requirement 3: Implement Atomic Disk Space Reservation

**User Story:** As a system administrator, I want disk space to be reserved atomically before downloads, so that multiple processes don't race for the same free space.

#### Acceptance Criteria

1. WHEN checking disk space before download, THE Scraper SHALL reserve the required space atomically
2. WHEN a download begins, THE Scraper SHALL ensure no other process can claim the reserved space
3. WHEN a download completes or fails, THE Scraper SHALL release the reserved space
4. IF insufficient space is available after reservation attempt, THEN THE Scraper SHALL skip the video and log the reason

### Requirement 4: Implement Database File Locking

**User Story:** As a developer, I want database writes to be protected by file locks, so that concurrent processes don't corrupt JSON files.

#### Acceptance Criteria

1. WHEN writing to any JSON database file, THE Database_Manager SHALL acquire an exclusive file lock
2. WHEN reading from any JSON database file, THE Database_Manager SHALL acquire a shared file lock
3. WHEN a lock cannot be acquired within a timeout period, THE Database_Manager SHALL retry with exponential backoff
4. WHEN a process terminates unexpectedly, THE Database_Manager SHALL release all held locks automatically

### Requirement 5: Align Timeout Values

**User Story:** As a system architect, I want timeout values to be properly aligned, so that the workflow doesn't kill the script mid-operation.

#### Acceptance Criteria

1. THE Workflow SHALL set a timeout that is at least 30 minutes longer than the Python script timeout
2. THE Scraper SHALL check remaining time before starting each new video
3. WHEN less than 30 minutes remain before workflow timeout, THE Scraper SHALL stop accepting new videos
4. WHEN the script timeout is reached, THE Scraper SHALL complete the current video before exiting

### Requirement 6: Implement Robust Git Push with Retry

**User Story:** As a DevOps engineer, I want git push operations to retry on failure, so that temporary network issues don't cause data loss.

#### Acceptance Criteria

1. WHEN a git push fails, THE Scraper SHALL retry up to 3 times with exponential backoff
2. WHEN a push fails due to conflicts, THE Scraper SHALL pull with rebase and retry
3. WHEN a push fails due to network timeout, THE Scraper SHALL wait and retry
4. IF all retry attempts fail, THEN THE Scraper SHALL log the failure and save data locally for manual recovery

### Requirement 7: Implement Cleanup on Crash

**User Story:** As a system administrator, I want temporary files to be cleaned up even when the script crashes, so that disk space isn't wasted.

#### Acceptance Criteria

1. WHEN the script starts, THE Scraper SHALL scan for and remove orphaned temporary files from previous runs
2. WHEN the script exits normally, THE Scraper SHALL remove all temporary files for processed videos
3. WHEN the script crashes, THE Scraper SHALL use signal handlers to clean up temporary files before exit
4. WHEN the workflow is cancelled, THE Workflow SHALL execute cleanup steps in a finally block

### Requirement 8: Implement Video Deduplication

**User Story:** As a data engineer, I want videos to be deduplicated by URL before processing, so that the same video isn't processed multiple times in one run.

#### Acceptance Criteria

1. WHEN discovering videos from a page, THE Scraper SHALL normalize URLs before checking if processed
2. WHEN checking if a video is processed, THE Database_Manager SHALL compare normalized URLs
3. THE Database_Manager SHALL normalize URLs by removing query parameters, fragments, and trailing slashes
4. WHEN a duplicate URL is detected, THE Scraper SHALL skip it and log the duplicate

### Requirement 9: Validate API Keys Before Pipeline Start

**User Story:** As a system operator, I want API keys to be validated before starting the pipeline, so that the workflow fails fast if credentials are invalid.

#### Acceptance Criteria

1. WHEN the workflow starts, THE Workflow SHALL validate that all required API keys are set
2. WHEN the workflow starts, THE Workflow SHALL make test API calls to verify credentials are valid
3. IF any API key is missing or invalid, THEN THE Workflow SHALL fail immediately with a clear error message
4. THE Workflow SHALL log which API keys are valid and which are missing

### Requirement 10: Implement Browser Memory Leak Prevention

**User Story:** As a developer, I want the browser to be properly closed on exceptions, so that memory leaks don't cause the workflow to run out of memory.

#### Acceptance Criteria

1. WHEN an exception occurs during scraping, THE Scraper SHALL close the browser in a finally block
2. WHEN the browser is closed, THE Scraper SHALL verify the process is terminated
3. WHEN creating a new browser instance, THE Scraper SHALL check for and kill any orphaned browser processes
4. THE Scraper SHALL restart the browser after every successful video to prevent memory accumulation

### Requirement 11: Implement Discovery Failure Backoff

**User Story:** As a system operator, I want the script to back off when discovery fails repeatedly, so that it doesn't enter an infinite loop.

#### Acceptance Criteria

1. WHEN video discovery fails, THE Scraper SHALL increment a failure counter
2. WHEN the failure counter reaches 3, THE Scraper SHALL wait 60 seconds before retrying
3. WHEN the failure counter reaches 5, THE Scraper SHALL wait 300 seconds before retrying
4. WHEN the failure counter reaches 10, THE Scraper SHALL exit and log the repeated failures

### Requirement 12: Sanitize Git Remote URLs in Logs

**User Story:** As a security engineer, I want GitHub tokens to be masked in logs, so that credentials aren't exposed in workflow output.

#### Acceptance Criteria

1. WHEN logging git remote URLs, THE Scraper SHALL replace the GitHub token with "***TOKEN***"
2. WHEN logging git commands, THE Scraper SHALL mask any authentication credentials
3. WHEN logging API responses, THE Scraper SHALL mask any sensitive fields
4. THE Workflow SHALL use GitHub's built-in secret masking for environment variables

### Requirement 13: Handle Concurrent Workflow Cancellation

**User Story:** As a DevOps engineer, I want the workflow to handle cancellation gracefully, so that the repository isn't left in an inconsistent state.

#### Acceptance Criteria

1. WHEN a workflow is cancelled mid-commit, THE Workflow SHALL complete the current commit operation
2. WHEN a workflow is cancelled, THE Workflow SHALL push any staged changes before exiting
3. WHEN a workflow is cancelled during upload, THE Workflow SHALL save partial progress to the database
4. THE Workflow SHALL use git stash to preserve uncommitted changes on cancellation

### Requirement 14: Implement JAVDatabase Integration Fallback

**User Story:** As a data engineer, I want the pipeline to continue when JAVDatabase integration fails, so that Jable scraping isn't blocked by external dependencies.

#### Acceptance Criteria

1. WHEN JAVDatabase integration is unavailable, THE Scraper SHALL log a warning and continue with Jable data only
2. WHEN JAVDatabase API calls fail, THE Scraper SHALL retry up to 2 times with backoff
3. IF JAVDatabase enrichment fails after retries, THEN THE Scraper SHALL save the video with Jable data only
4. THE Scraper SHALL track JAVDatabase availability and skip enrichment if it's consistently failing

### Requirement 15: Implement Segment Folder Cleanup

**User Story:** As a system administrator, I want HLS segment folders to be cleaned up after downloads, so that temporary files don't consume disk space.

#### Acceptance Criteria

1. WHEN an HLS download completes, THE Scraper SHALL delete the segment folder
2. WHEN an HLS download fails, THE Scraper SHALL delete the segment folder
3. WHEN the script starts, THE Scraper SHALL scan for and remove orphaned segment folders
4. THE Scraper SHALL use glob patterns to find segment folders matching the pattern `.*_segments`
