"""
Upload to working hosts only (Turboviplay, SeekStreaming)
Skips blocked hosts (Streamtape, Vidoza)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_manager import db_manager

from turboviplay_uploader import TurboviplayUploader
from seekstreaming_uploader import SeekstreamingUploader
from parallel_upload_pipeline import ParallelUploadPipeline


class WorkingHostsUploader:
    """Upload only to working hosts"""
    
    def __init__(self, env_path=".env"):
        load_dotenv(env_path)
        
        self.working_hosts = ['turboviplay', 'seekstreaming']
        self.pipeline = ParallelUploadPipeline(env_path)
    
    def upload_video(self, video_path, title=None, max_workers=2):
        """Upload video to working hosts only"""
        print(f"\n{'='*80}")
        print(f"UPLOADING TO WORKING HOSTS ONLY")
        print(f"Hosts: {', '.join(self.working_hosts)}")
        print(f"{'='*80}\n")
        
        return self.pipeline.upload_video(
            video_path=video_path,
            title=title,
            hosts=self.working_hosts,
            max_workers=max_workers
        )


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python upload_working_hosts.py <video_file> [title]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(video_path):
        print(f"✗ Video file not found: {video_path}")
        sys.exit(1)
    
    uploader = WorkingHostsUploader()
    results = uploader.upload_video(video_path, title)
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Successful: {results['successful']}/{len(results['results'])}")
    print(f"Total time: {results['total_time']:.1f}s")
    
    for host, result in results['results'].items():
        if result.get('success'):
            print(f"\n✓ {host.upper()}")
            print(f"  Embed: {result.get('embed_url', 'N/A')}")
        else:
            print(f"\n✗ {host.upper()}: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
