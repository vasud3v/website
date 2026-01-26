"""
Wait for upload to complete and show final results
"""
import time
import json
from pathlib import Path

def wait_and_show_results():
    print("\n⏳ Waiting for uploads to complete...")
    print("This may take a few minutes depending on your internet speed.")
    print("=" * 70)
    
    results_dir = Path("upload_results")
    results_dir.mkdir(exist_ok=True)
    
    # Wait for result file to be created/updated
    last_check = 0
    while True:
        result_files = sorted(results_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if result_files:
            latest = result_files[0]
            current_mtime = latest.stat().st_mtime
            
            if current_mtime > last_check:
                last_check = current_mtime
                
                with open(latest, 'r') as f:
                    data = json.load(f)
                
                print(f"\n📊 Upload Progress Update:")
                print(f"Video: {data['video_name']}")
                
                successful = []
                failed = []
                
                for host, result in data['results'].items():
                    if result.get('success'):
                        successful.append(host)
                        print(f"  ✅ {host.upper()}: {result.get('url', 'N/A')}")
                    else:
                        failed.append(host)
                        error = result.get('error', 'Unknown')[:60]
                        print(f"  ❌ {host.upper()}: {error}")
                
                print(f"\n📈 Summary: {len(successful)} successful, {len(failed)} failed")
                
                if len(successful) + len(failed) == 6:
                    print("\n✨ All uploads completed!")
                    print("\n🔗 Successful URLs:")
                    for host in successful:
                        result = data['results'][host]
                        print(f"\n{host.upper()}:")
                        print(f"  Direct: {result.get('url')}")
                        print(f"  Embed:  {result.get('embed_url')}")
                    break
        
        time.sleep(3)

if __name__ == "__main__":
    try:
        wait_and_show_results()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
