"""
Test upload to all hosts with progress bars
No validation, no status checks - just upload
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Import all uploaders
from upload18_uploader import Upload18Uploader
from uploady_uploader import UploadyUploader
from turboviplay_uploader import TurboviplayUploader
from mixdrop_uploader import MixDropUploader
from seekstreaming_uploader import SeekstreamingUploader
from streamtape_uploader import StreamtapeUploader

def test_upload(video_path):
    """Test upload to all configured hosts"""
    
    if not os.path.exists(video_path):
        print(f"✗ Video file not found: {video_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"TESTING UPLOAD TO ALL HOSTS")
    print(f"{'='*80}")
    print(f"Video: {video_path}")
    print(f"Size: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
    print(f"{'='*80}\n")
    
    results = {}
    
    # Test Upload18
    if os.getenv("UPLOAD18_API_KEY"):
        print(f"\n{'='*80}")
        print("UPLOAD18")
        print(f"{'='*80}")
        uploader = Upload18Uploader(
            email=os.getenv("UPLOAD18_EMAIL"),
            username=os.getenv("UPLOAD18_USERNAME"),
            password=os.getenv("UPLOAD18_PASSWORD"),
            api_key=os.getenv("UPLOAD18_API_KEY")
        )
        results['upload18'] = uploader.upload(video_path)
    
    # Test Uploady
    if os.getenv("UPLOADY_API_KEY"):
        print(f"\n{'='*80}")
        print("UPLOADY")
        print(f"{'='*80}")
        uploader = UploadyUploader(
            email=os.getenv("UPLOADY_EMAIL"),
            username=os.getenv("UPLOADY_USERNAME"),
            api_key=os.getenv("UPLOADY_API_KEY")
        )
        results['uploady'] = uploader.upload(video_path)
    
    # Test Turboviplay
    if os.getenv("TURBOVIPLAY_API_KEY"):
        print(f"\n{'='*80}")
        print("TURBOVIPLAY")
        print(f"{'='*80}")
        uploader = TurboviplayUploader(
            email=os.getenv("TURBOVIPLAY_EMAIL"),
            username=os.getenv("TURBOVIPLAY_USERNAME"),
            password=os.getenv("TURBOVIPLAY_PASSWORD"),
            api_key=os.getenv("TURBOVIPLAY_API_KEY")
        )
        results['turboviplay'] = uploader.upload(video_path)
    
    # Test MixDrop
    if os.getenv("MIXDROP_API_KEY"):
        print(f"\n{'='*80}")
        print("MIXDROP")
        print(f"{'='*80}")
        uploader = MixDropUploader(
            email=os.getenv("MIXDROP_EMAIL"),
            api_key=os.getenv("MIXDROP_API_KEY")
        )
        results['mixdrop'] = uploader.upload(video_path)
    
    # Test SeekStreaming
    if os.getenv("SEEKSTREAMING_API_KEY"):
        print(f"\n{'='*80}")
        print("SEEKSTREAMING")
        print(f"{'='*80}")
        uploader = SeekstreamingUploader(
            api_key=os.getenv("SEEKSTREAMING_API_KEY"),
            email=os.getenv("SEEKSTREAMING_EMAIL"),
            password=os.getenv("SEEKSTREAMING_PASSWORD")
        )
        results['seekstreaming'] = uploader.upload(video_path)
    
    # Test Streamtape
    if os.getenv("STREAMTAPE_LOGIN") and os.getenv("STREAMTAPE_API_KEY"):
        print(f"\n{'='*80}")
        print("STREAMTAPE")
        print(f"{'='*80}")
        uploader = StreamtapeUploader(
            login=os.getenv("STREAMTAPE_LOGIN"),
            api_key=os.getenv("STREAMTAPE_API_KEY")
        )
        results['streamtape'] = uploader.upload(video_path)
    
    # Summary
    print(f"\n{'='*80}")
    print("UPLOAD SUMMARY")
    print(f"{'='*80}")
    
    successful = []
    failed = []
    
    for host, result in results.items():
        if result.get('success'):
            successful.append(host)
            print(f"✓ {host.upper()}: {result.get('embed_url', result.get('url', 'N/A'))}")
        else:
            failed.append(host)
            error = result.get('error', 'Unknown')[:60]
            print(f"✗ {host.upper()}: {error}")
    
    print(f"\n{'='*80}")
    print(f"Total: {len(results)} | Success: {len(successful)} | Failed: {len(failed)}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_all_uploads.py <video_path>")
        print("\nExample:")
        print("  python test_all_uploads.py ../test_preview.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    test_upload(video_path)
