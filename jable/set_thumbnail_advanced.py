#!/usr/bin/env python3
"""
Advanced thumbnail setting for StreamWish
Downloads thumbnail from Jable and uploads to StreamWish, then sets it
"""
import os
import requests
import tempfile
import time

def download_image(url, output_path):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://jable.tv/'
        })
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"   [Download] Failed: {e}")
        return False

def upload_image_to_streamwish(image_path, api_key, folder_id=None):
    """Upload image to StreamWish and get hosted URL"""
    try:
        print(f"   [Upload] Uploading image to StreamWish...")
        
        # Get upload server
        params = {'key': api_key}
        if folder_id:
            params['fld_id'] = folder_id
        
        response = requests.get(
            'https://api.streamwish.com/api/upload/server',
            params=params,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"   [Upload] Failed to get upload server: {response.status_code}")
            return None
        
        result = response.json()
        if result.get('status') != 200:
            print(f"   [Upload] Server response: {result}")
            return None
        
        upload_url = result.get('result')
        if not upload_url:
            print(f"   [Upload] No upload URL in response")
            return None
        
        print(f"   [Upload] Got upload server: {upload_url[:50]}...")
        
        # Upload file
        with open(image_path, 'rb') as f:
            files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
            data = {'key': api_key}
            if folder_id:
                data['fld_id'] = folder_id
            
            response = requests.post(
                upload_url,
                files=files,
                data=data,
                timeout=120
            )
        
        if response.status_code != 200:
            print(f"   [Upload] Upload failed: {response.status_code}")
            return None
        
        result = response.json()
        print(f"   [Upload] Upload response: {result}")
        
        if result.get('status') == 200:
            file_info = result.get('result', {})
            if isinstance(file_info, dict):
                # Get the direct link or file URL
                file_url = file_info.get('url') or file_info.get('direct_link')
                if file_url:
                    print(f"   [Upload] ✅ Image uploaded: {file_url[:60]}...")
                    return file_url
        
        return None
        
    except Exception as e:
        print(f"   [Upload] Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

def set_streamwish_thumbnail_advanced(filecode, thumbnail_url, api_key, folder_id=None):
    """
    Advanced method: Download thumbnail, upload to StreamWish, then set it
    
    Args:
        filecode: StreamWish file code
        thumbnail_url: Original thumbnail URL (e.g., from Jable)
        api_key: StreamWish API key
        folder_id: Optional folder ID
        
    Returns:
        True if successful, False otherwise
    """
    temp_file = None
    temp_path = None
    
    try:
        print(f"   [Thumbnail] Advanced method: Download + Upload + Set")
        print(f"   [Thumbnail] Source: {thumbnail_url[:80]}...")
        
        # Step 1: Download thumbnail
        print(f"   [Thumbnail] Step 1: Downloading thumbnail...")
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        if not download_image(thumbnail_url, temp_path):
            print(f"   [Thumbnail] ❌ Download failed")
            return False
        
        file_size = os.path.getsize(temp_path)
        print(f"   [Thumbnail] ✅ Downloaded ({file_size} bytes)")
        
        # Step 2: Try to set thumbnail directly using file upload
        print(f"   [Thumbnail] Step 2: Setting thumbnail via file upload...")
        
        # StreamWish API endpoint for setting splash image
        try:
            with open(temp_path, 'rb') as img_file:
                files = {'splash_img': (os.path.basename(temp_path), img_file, 'image/jpeg')}
                data = {
                    'key': api_key,
                    'file_code': filecode
                }
                
                response = requests.post(
                    'https://api.streamwish.com/api/file/splash',
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   [Thumbnail] Response: {result}")
                    
                    if result.get('status') == 200 or result.get('msg') == 'OK':
                        print(f"   [Thumbnail] ✅ Thumbnail set successfully!")
                        return True
                    else:
                        print(f"   [Thumbnail] ⚠️ API response: {result.get('msg', 'Unknown')}")
                else:
                    print(f"   [Thumbnail] ⚠️ HTTP {response.status_code}")
        except Exception as e:
            print(f"   [Thumbnail] ⚠️ Direct upload failed: {e}")
        
        # Step 3: Try alternative method - upload as file then reference it
        print(f"   [Thumbnail] Step 3: Trying alternative upload method...")
        hosted_url = upload_image_to_streamwish(temp_path, api_key, folder_id)
        
        if not hosted_url:
            print(f"   [Thumbnail] ❌ Image upload failed")
            return False
        
        print(f"   [Thumbnail] ✅ Image uploaded to: {hosted_url[:60]}...")
        
        # Step 4: Set the uploaded image as thumbnail
        print(f"   [Thumbnail] Step 4: Setting uploaded image as thumbnail...")
        
        endpoints = [
            {
                'url': 'https://api.streamwish.com/api/file/edit',
                'params': {
                    'key': api_key,
                    'file_code': filecode,
                    'splash_img': hosted_url
                }
            },
            {
                'url': 'https://api.streamwish.com/api/file/edit',
                'params': {
                    'key': api_key,
                    'file_code': filecode,
                    'player_img': hosted_url
                }
            }
        ]
        
        for i, endpoint in enumerate(endpoints, 1):
            try:
                response = requests.get(
                    endpoint['url'],
                    params=endpoint['params'],
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   [Thumbnail] Method {i} response: {result}")
                    
                    if result.get('status') == 200 or result.get('msg') == 'OK':
                        print(f"   [Thumbnail] ✅ Thumbnail set successfully!")
                        return True
                    
            except Exception as e:
                print(f"   [Thumbnail] Method {i} failed: {e}")
                continue
        
        print(f"   [Thumbnail] ⚠️ Could not set thumbnail via API")
        print(f"   [Thumbnail] Note: Image is uploaded at: {hosted_url}")
        return False
        
    except Exception as e:
        print(f"   [Thumbnail] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python set_thumbnail_advanced.py <filecode> <thumbnail_url>")
        sys.exit(1)
    
    if os.path.exists('.env'):
        from load_env import load_env
        load_env()
    
    api_key = os.getenv('STREAMWISH_API_KEY')
    filecode = sys.argv[1]
    thumbnail_url = sys.argv[2]
    
    result = set_streamwish_thumbnail_advanced(filecode, thumbnail_url, api_key)
    print(f"\nResult: {'Success' if result else 'Failed'}")
