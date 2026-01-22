"""
Simple test script to upload video_preview.mp4 to LuluStream
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')

# Import upload function
from lulustream_upload import upload_to_lulustream

def main():
    file_path = '../video_preview.mp4'
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print("Starting upload test...")
    print(f"File: {file_path}")
    print(f"Size: {os.path.getsize(file_path):,} bytes")
    
    # Upload with test parameters
    result = upload_to_lulustream(
        file_path=file_path,
        code='TEST-PREVIEW',
        title='Test Video Preview Upload',
        folder_name='TEST_UPLOADS'
    )
    
    print("\n" + "="*60)
    print("UPLOAD RESULT")
    print("="*60)
    
    if result.get('success'):
        print("✅ SUCCESS!")
        print(f"Service: {result['service']}")
        print(f"File Code: {result['filecode']}")
        print(f"Embed URL: {result['embed_url']}")
        print(f"Watch URL: {result['watch_url']}")
        print(f"Upload Time: {result['time']:.1f}s")
    else:
        print("❌ FAILED!")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result.get('success') else 1)
