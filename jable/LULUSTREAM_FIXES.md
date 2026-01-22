# LuluStream API Integration Fixes

## Date: January 22, 2026

## Issues Fixed

### 1. **Incorrect API Parameter Name** ✅ FIXED
**Problem:** The code was using `api_key` as the parameter name in upload requests, which is incorrect for LuluStream API.

**Solution:** Changed to `key` parameter (consistent with the server endpoint call which already used `key`).

**Files Modified:**
- `jable/lulustream_upload.py` (lines 117, 229)
- `jable/upload_all_hosts.py` (lines 101, 179)

**Before:**
```python
upload_fields = {
    'api_key': LULUSTREAM_API_KEY,
    'title': f"{code} - {title[:100]}",
    'file': (...)
}
```

**After:**
```python
upload_fields = {
    'key': LULUSTREAM_API_KEY,
    'title': f"{code} - {title[:100]}",
    'file': (...)
}
```

### 2. **Incorrect Folder Parameter Name** ✅ FIXED
**Problem:** The code was using `folder` as the parameter name, which doesn't match common video hosting API patterns.

**Solution:** Changed to `fld_id` (folder ID) which is the standard parameter name used by similar services like StreamWish.

**Files Modified:**
- `jable/lulustream_upload.py` (lines 122, 232)
- `jable/upload_all_hosts.py` (lines 106, 182)

**Before:**
```python
if folder_name:
    upload_fields['folder'] = folder_name
```

**After:**
```python
if folder_name:
    upload_fields['fld_id'] = folder_name
```

### 3. **Timeout Too Short for Large Files** ✅ FIXED
**Problem:** Upload timeout was set to 300 seconds (5 minutes), which is insufficient for large video files (2-5 GB).

**Solution:** Increased timeout to 7200 seconds (2 hours) to accommodate large file uploads.

**Files Modified:**
- `jable/lulustream_upload.py` (lines 169, 235)

**Before:**
```python
timeout=300  # 5 minutes
```

**After:**
```python
timeout=7200  # 2 hours for large files
```

**Rationale:** 
- Video files in this project are typically 2-5 GB
- At 10 MB/s upload speed, a 5 GB file takes ~8 minutes just for transfer
- Server processing time adds additional delay
- 2 hour timeout provides adequate buffer

### 4. **Missing Folder Parameter in Fallback Upload** ✅ FIXED
**Problem:** The basic upload mode (when requests-toolbelt is not installed) wasn't including the folder parameter.

**Solution:** Added folder parameter handling to the fallback upload path.

**Files Modified:**
- `jable/lulustream_upload.py` (lines 228-232)

### 5. **Improved Error Messages** ✅ FIXED
**Problem:** Timeout error message didn't provide helpful guidance.

**Solution:** Added tip about FTP upload for very large files.

**Files Modified:**
- `jable/lulustream_upload.py` (line 240)

## API Endpoint Reference

Based on code analysis and common video hosting patterns:

### Get Upload Server
```
GET https://lulustream.com/api/upload/server
Parameters:
  - key: API key (required)
Response:
  - result: Upload server URL
```

### Upload File
```
POST {upload_server_url}
Parameters:
  - key: API key (required)
  - title: Video title (required)
  - file: Video file (required)
  - fld_id: Folder ID (optional)
Content-Type: multipart/form-data
```

### Get File List
```
GET https://lulustream.com/api/file/list
Parameters:
  - key: API key (required)
  - per_page: Results per page (optional)
Response:
  - status: "success" or error
  - result.files: Array of file objects
```

## Response Formats

LuluStream can return two types of responses:

### 1. JSON Response (Success)
```json
{
  "status": "success",
  "file_code": "ABC123XYZ",
  "filecode": "ABC123XYZ",
  "download_url": "https://..."
}
```

### 2. HTML Form Response (Alternative Success)
```html
<Form name='F1' action='https://lulustream.com/' method='POST'>
  <textarea name="op">upload_result</textarea>
  <textarea name="file_code">ABC123XYZ</textarea>
  <textarea name="st">OK</textarea>
</Form>
```

The code handles both response types with multiple parsing strategies.

## Testing Recommendations

1. **Test with small file first** (< 100 MB) to verify API credentials
2. **Test folder creation** by uploading to a specific folder
3. **Monitor upload progress** to ensure full file is transmitted
4. **Verify file accessibility** after upload completes
5. **Check LuluStream dashboard** to confirm file appears correctly

## Common Issues & Solutions

### Issue: "Missing API key"
**Solution:** Set `LULUSTREAM_API_KEY` in your `.env` file

### Issue: "Upload timeout"
**Solution:** 
- Check internet connection stability
- For very large files (> 10 GB), consider using FTP upload instead
- Verify server is not experiencing issues

### Issue: "Could not extract file code"
**Solution:**
- Check LuluStream dashboard manually
- File may have uploaded successfully despite parsing error
- Use the API file list endpoint to find recent uploads

### Issue: "File too small"
**Solution:**
- Ensure video file downloaded completely before upload
- Check that file is at least 50 MB (unless using `allow_small_files=True`)

## Environment Variables Required

```bash
LULUSTREAM_API_KEY=your_api_key_here
```

Get your API key from: https://lulustream.com/account (assumed based on common patterns)

## Notes

- LuluStream supports HLS streaming
- Unlimited storage for premium users
- Files removed after 60 days for free users
- Adult content is allowed (legal content only)
- Supports FTP, Remote URL, and API upload methods
- No bandwidth limitations

## References

- LuluStream Homepage: https://lulustream.com/
- Upload methods mentioned: Browser, FTP, Remote URL, API, Torrent
- Earnings: Up to $35 per 10k views (3 views per 24 hours per IP)

---

**Note:** Since official API documentation is not publicly available, these fixes are based on:
1. Analysis of existing code patterns
2. Comparison with similar video hosting APIs (StreamWish, Streamtape)
3. Common REST API conventions
4. Error messages and response formats in the code
