"""
Verify and fix hosting URLs for uploaded videos
Tests if URLs are accessible and updates them if needed
"""
import requests
import json
import os
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_manager import db_manager

class HostingURLVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def check_url(self, url, host):
        """Check if URL is accessible"""
        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)
            return response.status_code in [200, 302, 301]
        except:
            return False
    
    def fix_seekstreaming_url(self, file_code):
        """Fix SeekStreaming URL format"""
        # Try different URL formats
        formats = [
            f"https://javcore.embedseek.com/#{file_code}",
            f"https://embedseek.com/#{file_code}",
            f"https://seekstreaming.com/e/{file_code}",
        ]
        
        for url in formats:
            if self.check_url(url, 'seekstreaming'):
                return url
        
        # Default to custom domain
        return f"https://javcore.embedseek.com/#{file_code}"
    
    def fix_streamtape_url(self, file_code):
        """Fix Streamtape URL format"""
        return {
            'embed_url': f"https://streamtape.com/e/{file_code}",
            'download_url': f"https://streamtape.com/v/{file_code}"
        }
    
    def fix_turboviplay_url(self, file_code):
        """Fix Turboviplay URL format"""
        return {
            'embed_url': f"https://emturbovid.com/e/{file_code}",
            'download_url': f"https://turboviplay.com/{file_code}"
        }
    
    def fix_vidoza_url(self, file_code):
        """Fix Vidoza URL format"""
        return {
            'embed_url': f"https://vidoza.net/embed-{file_code}.html",
            'download_url': f"https://vidoza.net/{file_code}.html"
        }
    
    def verify_and_fix_video(self, video):
        """Verify and fix hosting URLs for a video"""
        code = video.get('code', 'Unknown')
        print(f"\n{'='*70}")
        print(f"Checking: {code}")
        print(f"{'='*70}")
        
        if 'hosting_urls' not in video or not video['hosting_urls']:
            print("⚠️  No hosting URLs found")
            return False
        
        fixed = False
        
        for host, urls in video['hosting_urls'].items():
            print(f"\n[{host.upper()}]")
            file_code = urls.get('file_code', '')
            
            if not file_code:
                print("  ✗ No file code found")
                continue
            
            # Check current URLs
            embed_url = urls.get('embed_url', '')
            download_url = urls.get('download_url', '')
            
            print(f"  File Code: {file_code}")
            print(f"  Embed URL: {embed_url}")
            print(f"  Download URL: {download_url}")
            
            # Verify and fix based on host
            if host == 'seekstreaming':
                fixed_url = self.fix_seekstreaming_url(file_code)
                if fixed_url != embed_url:
                    print(f"  🔧 Fixing URL to: {fixed_url}")
                    video['hosting_urls'][host]['embed_url'] = fixed_url
                    video['hosting_urls'][host]['download_url'] = fixed_url
                    fixed = True
                else:
                    print(f"  ✓ URL format correct")
            
            elif host == 'streamtape':
                fixed_urls = self.fix_streamtape_url(file_code)
                if fixed_urls['embed_url'] != embed_url:
                    print(f"  🔧 Fixing URLs")
                    video['hosting_urls'][host].update(fixed_urls)
                    fixed = True
                else:
                    print(f"  ✓ URLs correct")
            
            elif host == 'turboviplay':
                fixed_urls = self.fix_turboviplay_url(file_code)
                if fixed_urls['embed_url'] != embed_url:
                    print(f"  🔧 Fixing URLs")
                    video['hosting_urls'][host].update(fixed_urls)
                    fixed = True
                else:
                    print(f"  ✓ URLs correct")
            
            elif host == 'vidoza':
                fixed_urls = self.fix_vidoza_url(file_code)
                if fixed_urls['embed_url'] != embed_url:
                    print(f"  🔧 Fixing URLs")
                    video['hosting_urls'][host].update(fixed_urls)
                    fixed = True
                else:
                    print(f"  ✓ URLs correct")
        
        return fixed
    
    def verify_all_videos(self):
        """Verify and fix all videos in database"""
        print("="*70)
        print("HOSTING URL VERIFIER & FIXER")
        print("="*70)
        
        videos = db_manager.get_all_videos()
        
        if not videos:
            print("\n⚠️  No videos found in database")
            return
        
        print(f"\nFound {len(videos)} video(s) to check")
        
        fixed_count = 0
        
        for video in videos:
            if self.verify_and_fix_video(video):
                # Save updated video
                if db_manager.add_or_update_video(video):
                    fixed_count += 1
                    print(f"\n✓ Updated database for {video.get('code')}")
        
        print(f"\n{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}")
        print(f"Total videos: {len(videos)}")
        print(f"Fixed: {fixed_count}")
        print(f"{'='*70}\n")


def main():
    verifier = HostingURLVerifier()
    verifier.verify_all_videos()


if __name__ == "__main__":
    main()
