"""
Test Internet Archive upload with a small test file
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_test_video():
    """Create a small test video file"""
    test_file = Path(__file__).parent / "test_preview.mp4"
    
    # Create a minimal MP4 file (just for testing)
    # In production, you'd use actual preview videos
    with open(test_file, 'wb') as f:
        # Write minimal MP4 header (not a real video, just for testing upload)
        f.write(b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41')
        f.write(b'\x00' * 1000)  # 1KB test file
    
    return test_file

def test_internet_archive():
    """Test Internet Archive upload"""
    print("="*60)
    print("TESTING INTERNET ARCHIVE UPLOAD")
    print("="*60)
    
    # Check credentials
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    print("✓ Credentials file found")
    
    # Test internetarchive library
    try:
        import internetarchive as ia
        session = ia.get_session()
        print(f"✓ Connected to Internet Archive")
        print(f"  User: {session.user_email}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Create test file
    print("\nCreating test file...")
    test_file = create_test_video()
    print(f"✓ Test file created: {test_file}")
    
    # Test upload
    print("\nTesting upload...")
    try:
        from upload_to_ia import upload_preview_to_internet_archive
        
        result = upload_preview_to_internet_archive(
            str(test_file),
            "TEST-001",
            "Test Preview Upload"
        )
        
        if result['success']:
            print("\n" + "="*60)
            print("✓ UPLOAD TEST SUCCESSFUL!")
            print("="*60)
            print(f"Direct URL: {result['direct_url']}")
            print(f"Details: {result['details_url']}")
            print("\nYou can test the URL in your browser:")
            print(f"  {result['direct_url']}")
            print("="*60)
            
            # Cleanup
            test_file.unlink()
            print("\n✓ Test file cleaned up")
            
            return True
        else:
            print(f"\n❌ Upload failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_internet_archive()
    
    if success:
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nYou're ready to upload real preview videos:")
        print("  python upload_to_ia.py <video_file> <video_code>")
        print("\nOr batch upload:")
        print("  python upload_to_ia.py --batch <preview_directory>")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("TEST FAILED")
        print("="*60)
        print("\nPlease check:")
        print("  1. Internet Archive credentials in .env")
        print("  2. Internet connection")
        print("  3. Account is verified (check email)")
        print("="*60)
        sys.exit(1)
