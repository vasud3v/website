import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from seekstreaming_uploader import SeekstreamingUploader
from streamtape_uploader import StreamtapeUploader
from turboviplay_uploader import TurboviplayUploader
from vidoza_uploader import VidozaUploader
from uploady_uploader import UploadyUploader
from upload18_uploader import Upload18Uploader

class ParallelUploadPipeline:
    def __init__(self, env_path=".env"):
        """Initialize the parallel upload pipeline with all hosting services"""
        load_dotenv(env_path)
        
        # Initialize all uploaders
        self.uploaders = {
            "seekstreaming": SeekstreamingUploader(
                api_key=os.getenv("SEEKSTREAMING_API_KEY"),
                email=os.getenv("SEEKSTREAMING_EMAIL"),
                password=os.getenv("SEEKSTREAMING_PASSWORD")
            ),
            "streamtape": StreamtapeUploader(
                username=os.getenv("STREAMTAPE_USERNAME"),
                password=os.getenv("STREAMTAPE_PASSWORD")
            ),
            "turboviplay": TurboviplayUploader(
                email=os.getenv("TURBOVIPLAY_EMAIL"),
                username=os.getenv("TURBOVIPLAY_USERNAME"),
                password=os.getenv("TURBOVIPLAY_PASSWORD"),
                api_key=os.getenv("TURBOVIPLAY_API_KEY")
            ),
            "vidoza": VidozaUploader(
                email=os.getenv("VIDOZA_EMAIL"),
                password=os.getenv("VIDOZA_PASSWORD"),
                api_key=os.getenv("VIDOZA_API_KEY")
            ),
            "uploady": UploadyUploader(
                email=os.getenv("UPLOADY_EMAIL"),
                username=os.getenv("UPLOADY_USERNAME"),
                api_key=os.getenv("UPLOADY_API_KEY")
            ),
            "upload18": Upload18Uploader(
                email=os.getenv("UPLOAD18_EMAIL"),
                username=os.getenv("UPLOAD18_USERNAME"),
                password=os.getenv("UPLOAD18_PASSWORD"),
                api_key=os.getenv("UPLOAD18_API_KEY")
            )
        }
        
        self.results_dir = Path("upload_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def upload_to_host(self, host_name, uploader, video_path, title):
        """Upload video to a single host"""
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"Starting upload to {host_name.upper()}")
        print(f"{'='*60}")
        
        result = uploader.upload(video_path, title)
        
        elapsed_time = time.time() - start_time
        result['host'] = host_name
        result['upload_time'] = elapsed_time
        result['timestamp'] = datetime.now().isoformat()
        
        if result['success']:
            print(f"✓ {host_name.upper()} completed in {elapsed_time:.2f}s")
        else:
            print(f"✗ {host_name.upper()} failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def upload_video(self, video_path, title=None, hosts=None, max_workers=6):
        """
        Upload a video to multiple hosting sites in parallel
        
        Args:
            video_path: Path to the video file
            title: Optional title for the video
            hosts: List of host names to upload to (None = all hosts)
            max_workers: Maximum number of parallel uploads
        
        Returns:
            Dictionary with upload results for each host
        """
        if not os.path.exists(video_path):
            return {"error": "Video file not found", "path": video_path}
        
        # Use all hosts if none specified
        if hosts is None:
            hosts = list(self.uploaders.keys())
        
        # Validate hosts
        invalid_hosts = [h for h in hosts if h not in self.uploaders]
        if invalid_hosts:
            return {"error": f"Invalid hosts: {invalid_hosts}"}
        
        title = title or Path(video_path).stem
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        
        print(f"\n{'#'*60}")
        print(f"PARALLEL UPLOAD PIPELINE")
        print(f"{'#'*60}")
        print(f"Video: {Path(video_path).name}")
        print(f"Size: {file_size:.2f} MB")
        print(f"Title: {title}")
        print(f"Hosts: {', '.join(hosts)}")
        print(f"Max Workers: {max_workers}")
        print(f"{'#'*60}\n")
        
        results = {}
        start_time = time.time()
        
        # Upload to all hosts in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_host = {
                executor.submit(
                    self.upload_to_host,
                    host_name,
                    self.uploaders[host_name],
                    video_path,
                    title
                ): host_name
                for host_name in hosts
            }
            
            for future in as_completed(future_to_host):
                host_name = future_to_host[future]
                try:
                    result = future.result()
                    results[host_name] = result
                except Exception as e:
                    print(f"✗ {host_name.upper()} exception: {str(e)}")
                    results[host_name] = {
                        "success": False,
                        "host": host_name,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
        
        total_time = time.time() - start_time
        
        # Summary
        successful = sum(1 for r in results.values() if r.get('success'))
        failed = len(results) - successful
        
        print(f"\n{'='*60}")
        print(f"UPLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Successful: {successful}/{len(results)}")
        print(f"Failed: {failed}/{len(results)}")
        print(f"{'='*60}\n")
        
        # Save results
        self._save_results(video_path, title, results, total_time)
        
        return {
            "video_path": video_path,
            "title": title,
            "total_time": total_time,
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    def _save_results(self, video_path, title, results, total_time):
        """Save upload results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = Path(video_path).stem
        result_file = self.results_dir / f"{video_name}_{timestamp}.json"
        
        data = {
            "video_path": video_path,
            "video_name": video_name,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "total_time": total_time,
            "results": results
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {result_file}")
    
    def get_successful_urls(self, results):
        """Extract all successful upload URLs"""
        urls = {}
        for host, result in results.get('results', {}).items():
            if result.get('success'):
                urls[host] = {
                    'url': result.get('url'),
                    'embed_url': result.get('embed_url')
                }
        return urls


def main():
    """Example usage"""
    pipeline = ParallelUploadPipeline()
    
    # Example: Upload a video to all hosts
    video_path = "path/to/your/video.mp4"
    
    if os.path.exists(video_path):
        results = pipeline.upload_video(
            video_path=video_path,
            title="My Video Title",
            hosts=None,  # Upload to all hosts
            max_workers=6  # 6 parallel uploads
        )
        
        # Get successful URLs
        urls = pipeline.get_successful_urls(results)
        print("\nSuccessful Upload URLs:")
        for host, data in urls.items():
            print(f"\n{host.upper()}:")
            print(f"  URL: {data['url']}")
            print(f"  Embed: {data['embed_url']}")
    else:
        print(f"Video file not found: {video_path}")
        print("\nUsage:")
        print("1. Place your video file in the directory")
        print("2. Update video_path in main()")
        print("3. Run: python parallel_upload_pipeline.py")


if __name__ == "__main__":
    main()
