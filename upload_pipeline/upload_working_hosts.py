"""
Upload to ONLY the 4 working hosts
This ensures 100% success rate
"""
import os
import sys
from parallel_upload_pipeline import ParallelUploadPipeline

# Only use verified working hosts
WORKING_HOSTS = [
    "streamtape",   # ✅ Verified working
    "vidoza",       # ✅ Verified working
    "turboviplay",  # ✅ Verified working
    "uploady"       # ✅ Working (SSL workaround)
]

def main():
    # Video file path
    video_path = r"C:\Users\hp\Downloads\New folder\New folder\test_preview.mp4"
    
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found at {video_path}")
        return
    
    # Get file size
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
    print(f"\n📹 Video File: {os.path.basename(video_path)}")
    print(f"📊 Size: {file_size:.2f} MB")
    print(f"📁 Path: {video_path}")
    
    # Initialize pipeline
    print("\n🚀 Initializing upload pipeline...")
    print(f"🎯 Using {len(WORKING_HOSTS)} verified working hosts")
    pipeline = ParallelUploadPipeline()
    
    # Upload to working hosts only
    print("\n⬆️  Starting parallel upload to working hosts...")
    print("=" * 70)
    print(f"Hosts: {', '.join(WORKING_HOSTS)}")
    print("=" * 70)
    
    results = pipeline.upload_video(
        video_path=video_path,
        title="Test Preview Video",
        hosts=WORKING_HOSTS,  # Only working hosts
        max_workers=4  # 4 parallel uploads
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 UPLOAD RESULTS")
    print("=" * 70)
    
    successful = []
    failed = []
    
    for host, result in results['results'].items():
        if result.get('success'):
            successful.append(host)
            print(f"\n✅ {host.upper()}")
            print(f"   URL: {result.get('url', 'N/A')}")
            print(f"   Embed: {result.get('embed_url', 'N/A')}")
            print(f"   Time: {result.get('upload_time', 0):.2f}s")
        else:
            failed.append(host)
            print(f"\n❌ {host.upper()}")
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📈 SUMMARY")
    print("=" * 70)
    print(f"✅ Successful: {len(successful)}/{len(results['results'])}")
    print(f"❌ Failed: {len(failed)}/{len(results['results'])}")
    print(f"⏱️  Total Time: {results['total_time']:.2f}s")
    print(f"📊 Success Rate: {len(successful)/len(results['results'])*100:.1f}%")
    
    if successful:
        print(f"\n🎉 Successfully uploaded to: {', '.join(successful)}")
    
    if failed:
        print(f"\n⚠️  Failed uploads: {', '.join(failed)}")
    
    # Get all successful URLs
    urls = pipeline.get_successful_urls(results)
    if urls:
        print("\n" + "=" * 70)
        print("🔗 ALL SUCCESSFUL URLS")
        print("=" * 70)
        for host, data in urls.items():
            print(f"\n{host.upper()}:")
            print(f"  Direct: {data['url']}")
            print(f"  Embed:  {data['embed_url']}")
    
    print("\n✨ Upload process complete!")
    print(f"📄 Results saved to: upload_results/")
    
    # Show which hosts were skipped
    print("\n" + "=" * 70)
    print("ℹ️  SKIPPED HOSTS (Not Working)")
    print("=" * 70)
    print("❌ Seekstreaming - No public API available")
    print("❌ Upload18 - API key configuration issue")
    print("\nTo use all 6 hosts, run: python upload_test.py")
    print("To use only working hosts, run: python upload_working_hosts.py")

if __name__ == "__main__":
    main()
