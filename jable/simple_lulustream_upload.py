"""
Simple, reliable LuluStream upload without progress bars
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

def simple_upload(file_path, code, title, folder_name=None):
    """Simple upload without fancy progress tracking"""
    
    api_key = os.getenv('LULUSTREAM_API_KEY')
    if not api_key:
        print("ERROR: LULUSTREAM_API_KEY not set")
        return None
    
    print(f"\n{'='*60}")
    print(f"LULUSTREAM UPLOAD")
    print(f"{'='*60}")
    print(f"File: {os.path.basename(file_path)}")
    print(f"Size: {os.path.getsize(file_path):,} bytes")
    print(f"Code: {code}")
    print(f"Title: {title}")
    if folder_name:
        print(f"Folder: {folder_name}")
    
    # Step 1: Get upload server
    print(f"\nStep 1: Getting upload server...")
    try:
        r = requests.get(
            "https://lulustream.com/api/upload/server",
            params={'key': api_key},
            timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            server = data.get('result', 'https://lulustream.com/upload')
            print(f"  Server: {server}")
        else:
            server = 'https://lulustream.com/upload'
            print(f"  Using default server")
    except Exception as e:
        server = 'https://lulustream.com/upload'
        print(f"  Using default server (error: {e})")
    
    # Step 2: Upload file
    print(f"\nStep 2: Uploading file...")
    print(f"  This may take a few minutes...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
            data = {
                'key': api_key,
                'title': f"{code} - {title}"
            }
            if folder_name:
                data['fld_id'] = folder_name
            
            # Upload with reasonable timeout
            response = requests.post(
                server,
                files=files,
                data=data,
                timeout=600  # 10 minutes
            )
        
        print(f"  Upload completed!")
        print(f"  Status: {response.status_code}")
        
        # Step 3: Parse response
        print(f"\nStep 3: Processing response...")
        
        if response.status_code == 200:
            # Try JSON first
            try:
                result = response.json()
                print(f"  Response type: JSON")
                print(f"  Response: {result}")
                
                # Check for success
                if result.get('status') == 200 or result.get('msg') == 'OK':
                    # Look for file code in various places
                    file_code = None
                    
                    # Direct fields
                    file_code = result.get('file_code') or result.get('filecode')
                    
                    # In result field
                    if not file_code and 'result' in result:
                        if isinstance(result['result'], dict):
                            file_code = result['result'].get('file_code') or result['result'].get('filecode')
                        elif isinstance(result['result'], str):
                            file_code = result['result']
                    
                    if file_code:
                        print(f"\n{'='*60}")
                        print(f"SUCCESS!")
                        print(f"{'='*60}")
                        print(f"File Code: {file_code}")
                        print(f"Embed URL: https://lulustream.com/e/{file_code}")
                        print(f"Watch URL: https://lulustream.com/{file_code}")
                        print(f"{'='*60}")
                        return {
                            'success': True,
                            'filecode': file_code,
                            'embed_url': f"https://lulustream.com/e/{file_code}",
                            'watch_url': f"https://lulustream.com/{file_code}"
                        }
                    else:
                        print(f"  ERROR: No file code in response")
                        print(f"  Full response: {result}")
                else:
                    print(f"  ERROR: Upload failed")
                    print(f"  Message: {result.get('msg', 'Unknown')}")
                    
            except Exception as e:
                # Not JSON, try HTML parsing
                print(f"  Response type: HTML/Text")
                print(f"  Parsing HTML...")
                
                import re
                text = response.text
                
                # Look for file code patterns
                patterns = [
                    r'file_code["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]{10,})',
                    r'filecode["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]{10,})',
                    r'https://lulustream\.com/(?:e/|v/)?([a-zA-Z0-9]{10,})',
                ]
                
                file_code = None
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        file_code = match.group(1)
                        print(f"  Found code: {file_code}")
                        break
                
                if file_code:
                    print(f"\n{'='*60}")
                    print(f"SUCCESS!")
                    print(f"{'='*60}")
                    print(f"File Code: {file_code}")
                    print(f"Embed URL: https://lulustream.com/e/{file_code}")
                    print(f"Watch URL: https://lulustream.com/{file_code}")
                    print(f"{'='*60}")
                    return {
                        'success': True,
                        'filecode': file_code,
                        'embed_url': f"https://lulustream.com/e/{file_code}",
                        'watch_url': f"https://lulustream.com/{file_code}"
                    }
                else:
                    print(f"  ERROR: Could not find file code")
                    print(f"  Response preview: {text[:500]}")
        else:
            print(f"  ERROR: HTTP {response.status_code}")
            print(f"  Response: {response.text[:500]}")
        
    except requests.exceptions.Timeout:
        print(f"  ERROR: Upload timeout")
        print(f"  The file may have uploaded but server didn't respond")
        print(f"  Check your LuluStream dashboard")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    return {'success': False}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_lulustream_upload.py <video_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)
    
    code = os.path.basename(file_path).split('.')[0]
    title = code
    
    result = simple_upload(file_path, code, title, 'TEST_UPLOADS')
    
    sys.exit(0 if result.get('success') else 1)
