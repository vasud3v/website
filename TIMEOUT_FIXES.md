# StreamWish API Timeout Fixes

## Problem
StreamWish API calls were timing out during GitHub Actions workflow execution, causing:
- API key validation failures
- Folder creation failures  
- Upload verification failures
- Direct access test failures

Error messages:
```
[StreamWish] ⚠️ API key validation error: HTTPSConnectionPool(host='api.streamwish.com', port=443): Read timed out. (read timeout=10)
[StreamWish] ⚠️ Access test error: HTTPSConnectionPool(host='streamwish.com', port=443): Read timed out. (read timeout=10)
[Folder] ❌ Failed to create parent folder
```

## Root Cause
- Network latency in GitHub Actions runners
- StreamWish API can be slow to respond
- Single-attempt API calls with no retry logic
- Folder creation had no retry logic

## Solutions Implemented

### 1. API Key Validation Retry Logic (`upload_all_hosts.py`)
```python
# Added 3-attempt retry with exponential backoff
validation_attempts = 3
for val_attempt in range(validation_attempts):
    try:
        test_response = requests.get(..., timeout=30)
        # ... validation logic ...
    except requests.exceptions.Timeout:
        wait_time = 5 * (val_attempt + 1)  # 5s, 10s, 15s
        time.sleep(wait_time)
```

**Benefits:**
- Handles temporary network issues
- Exponential backoff prevents overwhelming the API
- Non-blocking - continues even if validation fails

### 2. Upload Verification Retry Logic (`upload_all_hosts.py`)
```python
# Added 3-attempt retry for file verification
verify_attempts = 3
for verify_attempt in range(verify_attempts):
    try:
        verify_response = requests.get(..., timeout=30)
        # ... verification logic ...
    except requests.exceptions.Timeout:
        wait_time = 5 * (verify_attempt + 1)  # 5s, 10s, 15s
        time.sleep(wait_time)
```

**Benefits:**
- Ensures uploaded files are properly verified
- Handles API lag after large uploads
- Prevents false negatives

### 3. Direct Access Test Retry Logic (`upload_all_hosts.py`)
```python
# Added 3-attempt retry for direct access testing
access_attempts = 3
for access_attempt in range(access_attempts):
    try:
        test_response = requests.head(..., timeout=30)
        # ... access test logic ...
    except requests.exceptions.Timeout:
        wait_time = 5 * (access_attempt + 1)  # 5s, 10s, 15s
        time.sleep(wait_time)
```

**Benefits:**
- Verifies file accessibility
- Handles processing delays
- Provides fallback verification method

### 4. Folder Creation Retry Logic (`streamwish_folders.py`)
```python
# Already implemented in previous fix
max_retries = 3
for attempt in range(max_retries):
    try:
        r = requests.get(..., timeout=30)
        # ... folder creation logic ...
    except requests.exceptions.Timeout:
        wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
        time.sleep(wait_time)
```

**Benefits:**
- Ensures folders are created reliably
- Handles nested folder structure (JAV_VIDEOS/CODE)
- Caches folder IDs to avoid duplicate creation

### 5. GitHub Actions Workflow (`integrated_scraper.yml`)
```yaml
- name: Validate API keys
  continue-on-error: true  # Non-blocking validation
  env:
    STREAMWISH_API_KEY: ${{ secrets.STREAMWISH_API_KEY }}
  run: |
    echo "Note: API validation timeouts are non-critical and will be retried during upload"
```

**Benefits:**
- Workflow doesn't fail on validation timeouts
- Validation is retried during actual upload
- Provides clear messaging about timeout handling

## Timeout Configuration

All API calls now use consistent timeout settings:

| Operation | Timeout | Retries | Backoff |
|-----------|---------|---------|---------|
| API Key Validation | 30s | 3 | 5s, 10s, 15s |
| Folder Creation | 30s | 3 | 5s, 10s, 15s |
| Upload Server Request | 30s | 3 | 5s |
| File Upload | 7200s (2h) | 3 | 10s |
| Upload Verification | 30s | 3 | 5s, 10s, 15s |
| Direct Access Test | 30s | 3 | 5s, 10s, 15s |

## Expected Behavior

### Before Fix
```
[StreamWish] ⚠️ API key validation error: Read timed out
[Folder] ❌ Failed to create parent folder
❌ Workflow fails
```

### After Fix
```
[StreamWish] ⚠️ API key validation timeout (attempt 1/3)
[StreamWish] Retrying in 5s...
[StreamWish] ✓ API key valid
[Folder] ⚠️ Timeout on attempt 1/3
[Folder] Retrying in 5s...
[Folder] ✓ Created parent folder with ID: 218511
✅ Workflow continues successfully
```

## Testing

To verify the fixes work:

1. **Manual Test**: Run workflow with `workflow_dispatch`
2. **Monitor Logs**: Check for retry messages in GitHub Actions logs
3. **Verify Uploads**: Confirm files are uploaded to correct folders
4. **Check Database**: Ensure metadata is saved correctly

## Files Modified

1. `jable/upload_all_hosts.py` - Added retry logic for all StreamWish API calls
2. `jable/streamwish_folders.py` - Already had retry logic from previous fix
3. `.github/workflows/integrated_scraper.yml` - Made validation non-blocking

## Commit

```
commit ad8e23c
Author: github-actions[bot]
Date: 2026-01-22

Fix: Add comprehensive retry logic for StreamWish API timeouts

- Added 3-attempt retry logic with exponential backoff (5s, 10s, 15s)
- All API calls now have proper timeout handling
- Prevents workflow failures due to temporary network issues
- Non-blocking validation in GitHub Actions workflow
```

## Future Improvements

1. **Adaptive Timeouts**: Adjust timeout based on file size
2. **Circuit Breaker**: Skip StreamWish temporarily if multiple failures
3. **Metrics**: Track retry success rates
4. **Alerting**: Notify if retries consistently fail

## Related Issues

- Task 7: Increase StreamWish API Timeouts ✅ FIXED
- Task 15-16: StreamWish API timeout errors ✅ FIXED
- Task 27-28: Read timeout errors ✅ FIXED
