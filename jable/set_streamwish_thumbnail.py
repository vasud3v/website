#!/usr/bin/env python3
"""
Set custom thumbnail for StreamWish video using external URL
"""
import os
import requests

def set_streamwish_thumbnail(filecode, thumbnail_url, api_key):
    """
    Set custom thumbnail for a StreamWish video using an external image URL
    
    Args:
        filecode: StreamWish file code (e.g., 'fv5mkww3k574')
        thumbnail_url: URL of the thumbnail image (e.g., Jable thumbnail URL)
        api_key: StreamWish API key
        
    Returns:
        True if successful, False otherwise
    """
    if not filecode or not thumbnail_url or not api_key:
        print(f"   [Thumbnail] ⚠️ Missing required parameters")
        return False
    
    try:
        print(f"   [Thumbnail] Setting custom thumbnail for {filecode}...")
        print(f"   [Thumbnail] Thumbnail URL: {thumbnail_url[:60]}...")
        
        # Try different possible API endpoints
        endpoints = [
            {
                'url': 'https://api.streamwish.com/api/file/edit',
                'params': {
                    'key': api_key,
                    'file_code': filecode,
                    'splash_img': thumbnail_url  # External image URL
                }
            },
            {
                'url': 'https://api.streamwish.com/api/file/splash',
                'params': {
                    'key': api_key,
                    'file_code': filecode,
                    'splash': thumbnail_url
                }
            },
            {
                'url': 'https://api.streamwish.com/api/file/edit',
                'params': {
                    'key': api_key,
                    'filecode': filecode,
                    'splash_img': thumbnail_url
                }
            }
        ]
        
        for i, endpoint in enumerate(endpoints, 1):
            try:
                print(f"   [Thumbnail] Trying endpoint {i}/{len(endpoints)}...")
                response = requests.get(
                    endpoint['url'],
                    params=endpoint['params'],
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   [Thumbnail] Response: {result}")
                    
                    # Check for success
                    if result.get('status') == 200 or result.get('msg') == 'OK':
                        print(f"   [Thumbnail] ✅ Thumbnail set successfully!")
                        return True
                    elif result.get('status') == 404:
                        print(f"   [Thumbnail] ⚠️ Endpoint not found, trying next...")
                        continue
                    else:
                        print(f"   [Thumbnail] ⚠️ API response: {result.get('msg', 'Unknown')}")
                        continue
                else:
                    print(f"   [Thumbnail] ⚠️ HTTP {response.status_code}, trying next...")
                    continue
                    
            except Exception as e:
                print(f"   [Thumbnail] ⚠️ Endpoint {i} failed: {e}")
                continue
        
        print(f"   [Thumbnail] ❌ All endpoints failed")
        return False
        
    except Exception as e:
        print(f"   [Thumbnail] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python set_streamwish_thumbnail.py <filecode> <thumbnail_url>")
        sys.exit(1)
    
    if os.path.exists('.env'):
        from load_env import load_env
        load_env()
    
    api_key = os.getenv('STREAMWISH_API_KEY')
    filecode = sys.argv[1]
    thumbnail_url = sys.argv[2]
    
    result = set_streamwish_thumbnail(filecode, thumbnail_url, api_key)
    print(f"\nResult: {'Success' if result else 'Failed'}")
