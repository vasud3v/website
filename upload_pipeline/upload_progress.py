"""
Progress tracking utilities for uploads
"""
from tqdm import tqdm
import requests

class ProgressFileWrapper:
    """Wrapper for file object to track upload progress"""
    def __init__(self, file_obj, filename, total_size):
        self.file_obj = file_obj
        self.filename = filename
        self.total_size = total_size
        self.progress_bar = tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            desc=f"📤 {filename}",
            leave=False
        )
        self.bytes_read = 0
    
    def read(self, size=-1):
        data = self.file_obj.read(size)
        self.bytes_read += len(data)
        self.progress_bar.update(len(data))
        return data
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.progress_bar.close()
        self.file_obj.close()

def upload_with_progress(url, files, data, timeout, verify=True):
    """
    Upload file with progress tracking
    
    Args:
        url: Upload URL
        files: Files dict for requests
        data: Form data
        timeout: Request timeout
        verify: SSL verification
    
    Returns:
        Response object
    """
    # Get file info
    file_tuple = list(files.values())[0]
    filename = file_tuple[0]
    file_obj = file_tuple[1]
    content_type = file_tuple[2] if len(file_tuple) > 2 else None
    
    # Get file size
    file_obj.seek(0, 2)  # Seek to end
    total_size = file_obj.tell()
    file_obj.seek(0)  # Seek back to start
    
    # Wrap file with progress tracker
    progress_file = ProgressFileWrapper(file_obj, filename, total_size)
    
    # Recreate files dict with progress wrapper
    file_key = list(files.keys())[0]
    if content_type:
        files_with_progress = {file_key: (filename, progress_file, content_type)}
    else:
        files_with_progress = {file_key: (filename, progress_file)}
    
    try:
        response = requests.post(
            url,
            files=files_with_progress,
            data=data,
            timeout=timeout,
            verify=verify
        )
        return response
    finally:
        progress_file.progress_bar.close()
