"""
Parallel Upload to All Hosts
Uploads to multiple hosts simultaneously for maximum speed
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# Import uploaders (excluding Upload18)
from uploady_uploader import UploadyUploader
from turboviplay_uploader import TurboviplayUploader
from mixdrop_uploader import MixDropUploader
from seekstreaming_uploader import SeekstreamingUploader
from streamtape_uploader import StreamtapeUploader


def upload_to_host(host_name, uploader, video_path):
    """Upload to a single host"""
    print(f"\n[{host_name}] Starting upload...")
    start_time = time.time()
    
    try:
        result = uploader.upload(video_path)
        elapsed = time.time() - start_time
        
        if result.get('success'):
            print(f"[{host_name}] ✓ Completed in {elapsed:.1f}s")
        else:
            print(f"[{host_name}] ✗ Failed: {result.get('error', 'Unknown')[:50]}")
        
        return host_name, result
    except Exception as e:
        print(f"[{host_name}] ✗ Exception: {str(e)[:50]}")
        return host_name, {"success": False, "error": str(e)}


def parallel_upload(video_path, max_workers=6):
    """Upload to all hosts in parallel"""
    
    if not os.path.exists(video_path):
        print(f"✗ Video not found: {video_path}")
        return
    
    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    
    print(f"\n{'='*80}")
    print(f"PARALLEL UPLOAD TO ALL HOSTS")
    print(f"{'='*80}")
    print(f"Video: {video_path}")
    print(f"Size: {size_mb:.1f} MB")
    print(f"Workers: {max_workers}")
    print(f"{'='*80}\n")
    
    # Initialize uploaders (excluding Upload18)
    uploaders = {}
    
    if os.getenv("UPLOADY_API_KEY"):
        uploaders['Uploady'] = UploadyUploader(
            email=os.getenv("UPLOADY_EMAIL"),
            username=os.getenv("UPLOADY_USERNAME"),
            api_key=os.getenv("UPLOADY_API_KEY")
        )
    
    if os.getenv("TURBOVIPLAY_API_KEY"):
        uploaders['Turboviplay'] = TurboviplayUploader(
            email=os.getenv("TURBOVIPLAY_EMAIL"),
            username=os.getenv("TURBOVIPLAY_USERNAME"),
            password=os.getenv("TURBOVIPLAY_PASSWORD"),
            api_key=os.getenv("TURBOVIPLAY_API_KEY")
        )
    
    if os.getenv("MIXDROP_API_KEY"):
        uploaders['MixDrop'] = MixDropUploader(
            email=os.getenv("MIXDROP_EMAIL"),
            api_key=os.getenv("MIXDROP_API_KEY")
        )
    
    if os.getenv("SEEKSTREAMING_API_KEY"):
        uploaders['SeekStreaming'] = SeekstreamingUploader(
            api_key=os.getenv("SEEKSTREAMING_API_KEY"),
            email=os.getenv("SEEKSTREAMING_EMAIL"),
            password=os.getenv("SEEKSTREAMING_PASSWORD")
        )
    
    # Streamtape (optional - may be blocked by ISP)
    if os.getenv("STREAMTAPE_LOGIN") and os.getenv("STREAMTAPE_API_KEY"):
        try:
            uploaders['Streamtape'] = StreamtapeUploader(
                login=os.getenv("STREAMTAPE_LOGIN"),
                api_key=os.getenv("STREAMTAPE_API_KEY")
            )
        except:
            print("⚠️  Streamtape initialization failed")
    
    if not uploaders:
        print("✗ No uploaders configured! Check .env file")
        return
    
    print(f"Uploading to {len(uploaders)} hosts in parallel...\n")
    
    # Upload in parallel
    results = {}
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(upload_to_host, host_name, uploader, video_path): host_name
            for host_name, uploader in uploaders.items()
        }
        
        for future in as_completed(futures):
            host_name = futures[future]
            try:
                host_name, result = future.result()
                results[host_name] = result
            except Exception as e:
                print(f"[{host_name}] ✗ Worker exception: {str(e)}")
                results[host_name] = {"success": False, "error": str(e)}
    
    total_time = time.time() - start_time
    
    # Summary
    successful = [h for h, r in results.items() if r.get('success')]
    failed = [h for h, r in results.items() if not r.get('success')]
    
    print(f"\n{'='*80}")
    print(f"UPLOAD SUMMARY")
    print(f"{'='*80}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Total hosts: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print(f"\n✓ Successful uploads:")
        for host in successful:
            result = results[host]
            url = result.get('embed_url', result.get('url', 'N/A'))
            print(f"  • {host}: {url}")
    
    if failed:
        print(f"\n✗ Failed uploads:")
        for host in failed:
            result = results[host]
            error = result.get('error', 'Unknown')[:60]
            print(f"  • {host}: {error}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parallel_upload.py <video_path> [max_workers]")
        print("\nExample:")
        print("  python parallel_upload.py test_preview.mp4")
        print("  python parallel_upload.py test_preview.mp4 6")
        sys.exit(1)
    
    video_path = sys.argv[1]
    max_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    
    parallel_upload(video_path, max_workers)
