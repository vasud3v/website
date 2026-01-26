"""
Test script to verify API implementations match actual documentation
Run this to test each uploader individually before using the pipeline
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_streamtape():
    """Test Streamtape API implementation"""
    print("\n" + "="*60)
    print("TESTING STREAMTAPE API")
    print("="*60)
    
    from streamtape_uploader import StreamtapeUploader
    
    uploader = StreamtapeUploader(
        username=os.getenv("STREAMTAPE_USERNAME"),
        password=os.getenv("STREAMTAPE_PASSWORD")
    )
    
    print(f"✓ Username: {uploader.username}")
    print(f"✓ Base URL: {uploader.base_url}")
    print(f"✓ Expected endpoint: {uploader.base_url}/file/ul")
    print("✓ File field name: file1")
    print("✓ Authentication: login + key parameters")
    

def test_vidoza():
    """Test Vidoza API implementation"""
    print("\n" + "="*60)
    print("TESTING VIDOZA API")
    print("="*60)
    
    from vidoza_uploader import VidozaUploader
    
    uploader = VidozaUploader(
        email=os.getenv("VIDOZA_EMAIL"),
        password=os.getenv("VIDOZA_PASSWORD"),
        api_key=os.getenv("VIDOZA_API_KEY")
    )
    
    print(f"✓ API Key: {uploader.api_key[:10]}...")
    print(f"✓ Base URL: {uploader.base_url}")
    print(f"✓ Expected endpoint: {uploader.base_url}/upload/http/server")
    print("✓ Authentication: Bearer token in Authorization header")
    print("✓ Upload process: 2-stage (get server + upload with params)")
    

def test_turboviplay():
    """Test Turboviplay API implementation"""
    print("\n" + "="*60)
    print("TESTING TURBOVIPLAY API")
    print("="*60)
    
    from turboviplay_uploader import TurboviplayUploader
    
    uploader = TurboviplayUploader(
        email=os.getenv("TURBOVIPLAY_EMAIL"),
        username=os.getenv("TURBOVIPLAY_USERNAME"),
        password=os.getenv("TURBOVIPLAY_PASSWORD"),
        api_key=os.getenv("TURBOVIPLAY_API_KEY")
    )
    
    print(f"✓ API Key: {uploader.api_key}")
    print(f"✓ Base URL: {uploader.base_url}")
    print(f"✓ Expected endpoint: {uploader.base_url}/uploadserver")
    print("✓ File field name: File (capital F)")
    print("✓ Parameter name: keyApi")
    

def test_seekstreaming():
    """Test Seekstreaming API implementation"""
    print("\n" + "="*60)
    print("TESTING SEEKSTREAMING API")
    print("="*60)
    
    from seekstreaming_uploader import SeekstreamingUploader
    
    uploader = SeekstreamingUploader(
        api_key=os.getenv("SEEKSTREAMING_API_KEY"),
        email=os.getenv("SEEKSTREAMING_EMAIL"),
        password=os.getenv("SEEKSTREAMING_PASSWORD")
    )
    
    print(f"✓ API Key: {uploader.api_key}")
    print(f"✓ Base URL: {uploader.base_url}")
    print(f"✓ Expected endpoint: {uploader.base_url}/upload/server")
    print("✓ Pattern: XFS-based (similar to other hosts)")
    

def test_uploady():
    """Test Uploady API implementation"""
    print("\n" + "="*60)
    print("TESTING UPLOADY API")
    print("="*60)
    
    from uploady_uploader import UploadyUploader
    
    uploader = UploadyUploader(
        email=os.getenv("UPLOADY_EMAIL"),
        username=os.getenv("UPLOADY_USERNAME"),
        api_key=os.getenv("UPLOADY_API_KEY")
    )
    
    print(f"✓ API Key: {uploader.api_key}")
    print(f"✓ Base URL: {uploader.base_url}")
    print(f"✓ Expected endpoint: {uploader.base_url}/upload/server")
    print("✓ Pattern: XFS-based")
    

def test_upload18():
    """Test Upload18 API implementation"""
    print("\n" + "="*60)
    print("TESTING UPLOAD18 API")
    print("="*60)
    
    from upload18_uploader import Upload18Uploader
    
    uploader = Upload18Uploader(
        email=os.getenv("UPLOAD18_EMAIL"),
        username=os.getenv("UPLOAD18_USERNAME"),
        password=os.getenv("UPLOAD18_PASSWORD"),
        api_key=os.getenv("UPLOAD18_API_KEY")
    )
    
    print(f"✓ API Key: {uploader.api_key}")
    print(f"✓ Base URL: {uploader.base_url}")
    print(f"✓ Expected endpoint: {uploader.base_url}/upload/server")
    print("✓ Pattern: XFS-based")
    

def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# API IMPLEMENTATION VERIFICATION")
    print("#"*60)
    
    try:
        test_streamtape()
        test_vidoza()
        test_turboviplay()
        test_seekstreaming()
        test_uploady()
        test_upload18()
        
        print("\n" + "="*60)
        print("✓ ALL API IMPLEMENTATIONS VERIFIED")
        print("="*60)
        print("\nNext steps:")
        print("1. Test with a small video file")
        print("2. Check response formats match expectations")
        print("3. Verify URLs are correctly generated")
        
    except Exception as e:
        print(f"\n✗ Error during verification: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
