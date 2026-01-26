#!/usr/bin/env python3
"""
Test Internet Archive Upload
Quick test to verify IA credentials and upload functionality
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_ia_credentials():
    """Test if IA credentials are set"""
    print("="*70)
    print("🔍 TESTING INTERNET ARCHIVE CREDENTIALS")
    print("="*70)
    
    access_key = os.getenv('IA_ACCESS_KEY')
    secret_key = os.getenv('IA_SECRET_KEY')
    
    if not access_key:
        print("❌ IA_ACCESS_KEY not set")
        return False
    
    if not secret_key:
        print("❌ IA_SECRET_KEY not set")
        return False
    
    print(f"✅ IA_ACCESS_KEY: {access_key[:20]}...")
    print(f"✅ IA_SECRET_KEY: {'*' * len(secret_key)}")
    
    return True


def test_ia_package():
    """Test if internetarchive package is installed"""
    print("\n🔍 TESTING INTERNETARCHIVE PACKAGE")
    print("="*70)
    
    try:
        import internetarchive as ia
        print(f"✅ internetarchive package installed (version: {ia.__version__})")
        return True
    except ImportError:
        print("❌ internetarchive package not installed")
        print("   Install with: pip install internetarchive")
        return False


def test_ia_session():
    """Test if we can create an IA session"""
    print("\n🔍 TESTING INTERNET ARCHIVE SESSION")
    print("="*70)
    
    try:
        from internet_archive_uploader import InternetArchiveUploader
        
        uploader = InternetArchiveUploader()
        print("✅ Internet Archive session created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create IA session: {e}")
        return False


def test_upload_preview():
    """Test uploading a preview video"""
    print("\n🔍 TESTING PREVIEW UPLOAD")
    print("="*70)
    
    # Check if test video exists
    test_video = Path("../test.mp4")
    if not test_video.exists():
        print(f"⚠️ Test video not found: {test_video}")
        print("   Skipping upload test")
        return True
    
    try:
        from internet_archive_uploader import InternetArchiveUploader
        
        uploader = InternetArchiveUploader()
        
        # Test metadata
        metadata = {
            'title': 'Test Preview Video',
            'actors': ['Test Actor'],
            'studio': 'Test Studio',
            'release_date': '2026-01-27'
        }
        
        print(f"📤 Uploading test video: {test_video}")
        print("   This may take a few minutes...")
        
        result = uploader.upload_preview(
            str(test_video),
            'TEST-001',
            metadata=metadata
        )
        
        if result.get('success'):
            print("\n✅ UPLOAD SUCCESSFUL!")
            print(f"   Direct MP4 Link: {result['direct_mp4_link']}")
            print(f"   Player Link: {result['player_link']}")
            return True
        else:
            print(f"\n❌ Upload failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*70)
    print("🧪 INTERNET ARCHIVE INTEGRATION TEST")
    print("="*70)
    
    all_passed = True
    
    # Test 1: Credentials
    if not test_ia_credentials():
        all_passed = False
        print("\n⚠️ Please set IA_ACCESS_KEY and IA_SECRET_KEY in .env file")
        print("   Get your keys from: https://archive.org/account/s3.php")
        return
    
    # Test 2: Package
    if not test_ia_package():
        all_passed = False
        return
    
    # Test 3: Session
    if not test_ia_session():
        all_passed = False
        return
    
    # Test 4: Upload (optional)
    print("\n" + "="*70)
    response = input("Do you want to test uploading a video? (y/n): ").lower()
    if response == 'y':
        if not test_upload_preview():
            all_passed = False
    
    # Summary
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\n🎉 Internet Archive integration is ready!")
        print("\nYou can now:")
        print("  1. Upload preview videos to Internet Archive")
        print("  2. Get direct MP4 links for your website")
        print("  3. Use the workflow in GitHub Actions")
    else:
        print("❌ SOME TESTS FAILED")
        print("="*70)
        print("\nPlease fix the issues above before proceeding")


if __name__ == "__main__":
    main()
