"""
Fix and update hosting URLs with proper formats
Checks video status and updates database with working URLs
"""
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_manager import db_manager

class HostingURLFixer:
    def __init__(self):
        pass
    
    def fix_turboviplay_urls(self, file_code):
        """Generate correct Turboviplay URLs"""
        return {
            'embed_url': f"https://emturbovid.com/t/{file_code}",
            'download_url': f"https://turboviplay.com/v/{file_code}",
            'file_code': file_code
        }
    
    def fix_seekstreaming_urls(self, file_code):
        """Generate correct SeekStreaming URLs"""
        return {
            'embed_url': f"https://javcore.embedseek.com/#{file_code}",
            'download_url': f"https://javcore.embedseek.com/#{file_code}",
            'file_code': file_code
        }
    
    def fix_streamtape_urls(self, file_code):
        """Generate correct Streamtape URLs"""
        return {
            'embed_url': f"https://streamtape.com/e/{file_code}",
            'download_url': f"https://streamtape.com/v/{file_code}",
            'file_code': file_code
        }
    
    def fix_vidoza_urls(self, file_code):
        """Generate correct Vidoza URLs"""
        return {
            'embed_url': f"https://vidoza.net/embed-{file_code}.html",
            'download_url': f"https://vidoza.net/{file_code}.html",
            'file_code': file_code
        }
    
    def fix_video_urls(self, video):
        """Fix all hosting URLs for a video"""
        code = video.get('code', 'Unknown')
        print(f"\n{'='*70}")
        print(f"Fixing: {code}")
        print(f"{'='*70}")
        
        if 'hosting_urls' not in video or not video['hosting_urls']:
            print("⚠️  No hosting URLs found")
            return False
        
        fixed = False
        
        for host, urls in video['hosting_urls'].items():
            file_code = urls.get('file_code', '')
            
            if not file_code:
                print(f"\n[{host.upper()}] ✗ No file code found, skipping")
                continue
            
            print(f"\n[{host.upper()}]")
            print(f"  File Code: {file_code}")
            print(f"  Current Embed: {urls.get('embed_url', 'N/A')}")
            
            # Fix URLs based on host
            new_urls = None
            
            if host == 'turboviplay':
                new_urls = self.fix_turboviplay_urls(file_code)
            elif host == 'seekstreaming':
                new_urls = self.fix_seekstreaming_urls(file_code)
            elif host == 'streamtape':
                new_urls = self.fix_streamtape_urls(file_code)
            elif host == 'vidoza':
                new_urls = self.fix_vidoza_urls(file_code)
            
            if new_urls:
                # Check if URLs changed
                if (new_urls['embed_url'] != urls.get('embed_url') or 
                    new_urls['download_url'] != urls.get('download_url')):
                    
                    print(f"  🔧 Updating URLs:")
                    print(f"     New Embed: {new_urls['embed_url']}")
                    print(f"     New Download: {new_urls['download_url']}")
                    
                    video['hosting_urls'][host] = new_urls
                    fixed = True
                else:
                    print(f"  ✓ URLs already correct")
        
        return fixed
    
    def fix_all_videos(self):
        """Fix all videos in database"""
        print("="*70)
        print("HOSTING URL FIXER")
        print("="*70)
        
        videos = db_manager.get_all_videos()
        
        if not videos:
            print("\n⚠️  No videos found in database")
            return
        
        print(f"\nFound {len(videos)} video(s) to fix")
        
        fixed_count = 0
        
        for video in videos:
            if self.fix_video_urls(video):
                # Save updated video
                if db_manager.add_or_update_video(video):
                    fixed_count += 1
                    print(f"\n✓ Updated database for {video.get('code')}")
                else:
                    print(f"\n✗ Failed to update database for {video.get('code')}")
        
        print(f"\n{'='*70}")
        print(f"SUMMARY")
        print(f"{'='*70}")
        print(f"Total videos: {len(videos)}")
        print(f"Fixed: {fixed_count}")
        print(f"{'='*70}\n")
        
        if fixed_count > 0:
            print("✓ Database updated with corrected URLs")
            print("\nYou can now test the URLs again with:")
            print("  python test_hosting_urls.py")


def main():
    fixer = HostingURLFixer()
    fixer.fix_all_videos()


if __name__ == "__main__":
    main()
