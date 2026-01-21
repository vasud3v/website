#!/usr/bin/env python3
"""
Upload thumbnail to StreamWish
"""
import os
import requests
import time

def upload_thumbnail_to_streamwish(thumbnail_path, api_key, folder_name=None):
    """
    Upload thumbnail image to StreamWish
    
    Args:
        thumbnail_path: Local path to thumbnail file
        api_key: StreamWish API key
        folder_name: Optional folder name to upload to
        
    Returns:
        Hosted file URL if successful, None if failed
    """
    if not thumbnail_path or not os.path.exists(thumbnail_path):
        print(f"   [File Upload] ⚠️ File not found: {thumbnail_path}")
        return None
    
    if not api_key:
        print(f"   [File Upload] ⚠️ No API key provided")
        return None
    
    try:
        file_size = os.path.getsize(thumbnail_path)
        file_name = os.path.basename(thumbnail_path)
        print(f"   [File Upload] Uploading {file_name} ({file_size} bytes) to StreamWish...")
        
        # Get folder ID if folder name provided
        folder_id = None
        if folder_name:
            from streamwish_folders import get_or_create_folder
            folder_id = get_or_create_folder(folder_name, api_key)
            if folder_id:
                print(f"   [File Upload] Target folder: {folder_name} (ID: {folder_id})")
            else:
                print(f"   [File Upload] ⚠️ Could not get folder ID, uploading to root")
        
        # Get upload server
        r = requests.get("https://api.streamwish.com/api/upload/server",
                        params={'key': api_key}, timeout=30)
        
        if r.status_code != 200:
            print(f"   [File Upload] ❌ Failed to get server: HTTP {r.status_code}")
            return None
        
        result = r.json()
        if result.get('status') != 200:
            print(f"   [File Upload] ❌ API error: {result.get('msg', 'Unknown')}")
            return None
        
        server = result.get('result', 'https://s1.streamwish.com/upload/01')
        print(f"   [File Upload] Server: {server}")
        
        # Upload file
        # Detect MIME type based on file extension
        file_ext = os.path.splitext(thumbnail_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        mime_type = mime_types.get(file_ext, 'application/octet-stream')
        
        with open(thumbnail_path, 'rb') as f:
            files = {'file': (file_name, f, mime_type)}
            data = {
                'key': api_key,
                'file_title': file_name
            }
            
            # Add folder ID if available
            if folder_id:
                data['fld_id'] = folder_id
            
            response = requests.post(
                server,
                files=files,
                data=data,
                timeout=60
            )
        
        print(f"   [File Upload] Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   [File Upload] Response: {result}")
            
            # Check for file URL in response
            if 'files' in result and len(result['files']) > 0:
                file_info = result['files'][0]
                
                # Try to construct direct URL from filecode
                filecode = file_info.get('filecode')
                if filecode:
                    # StreamWish direct file URL format
                    if file_ext == '.mp4':
                        file_url = f"https://streamwish.com/e/{filecode}"  # Embed URL for videos
                    else:
                        file_url = f"https://streamwish.com/i/{filecode}"  # Image URL
                    print(f"   [File Upload] ✅ Uploaded: {file_url}")
                    return file_url
                
                # Fallback: try other URL fields
                file_url = (
                    file_info.get('url') or 
                    file_info.get('direct_url') or
                    file_info.get('image_url')
                )
                
                if file_url:
                    print(f"   [File Upload] ✅ Uploaded: {file_url}")
                    return file_url
            
            print(f"   [File Upload] ⚠️ No URL found in response")
        else:
            print(f"   [File Upload] ❌ Upload failed: HTTP {response.status_code}")
            print(f"   [File Upload]   Response: {response.text[:300]}")
        
    except Exception as e:
        print(f"   [File Upload] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return None

if __name__ == "__main__":
    # Test
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python upload_thumbnail.py <thumbnail_path>")
        sys.exit(1)
    
    if os.path.exists('.env'):
        from load_env import load_env
        load_env()
    
    api_key = os.getenv('STREAMWISH_API_KEY')
    thumbnail_path = sys.argv[1]
    
    result = upload_thumbnail_to_streamwish(thumbnail_path, api_key)
    print(f"\nResult: {result}")
