#!/usr/bin/env python3
"""Get fresh M3U8 URL by re-scraping"""

from javgg_scraper import JavaGGScraper

video_url = "https://javgg.net/jav/fnew-021/"

print("="*70)
print("GETTING FRESH M3U8 URL")
print("="*70)
print(f"\nVideo: {video_url}")
print(f"\nReason: Previous M3U8 URLs have expired")
print(f"Solution: Re-scrape to get fresh URLs with new tokens\n")

scraper = JavaGGScraper(headless=True)

try:
    print("Scraping video page...")
    video_data = scraper.scrape_video(video_url)
    
    if video_data:
        print(f"\n✅ Successfully scraped!")
        print(f"\n{'='*70}")
        print("VIDEO INFORMATION")
        print(f"{'='*70}")
        print(f"  Code: {video_data.code}")
        print(f"  Title: {video_data.title[:60]}...")
        print(f"  Duration: {video_data.duration}")
        print(f"\n{'='*70}")
        print("DOWNLOAD URLS")
        print(f"{'='*70}")
        
        if video_data.embed_url:
            print(f"\n📍 Embed URL:")
            print(f"  {video_data.embed_url}")
        
        if video_data.m3u8_url:
            print(f"\n🎬 M3U8 URL (FRESH):")
            print(f"  {video_data.m3u8_url}")
            
            # Save to file for easy copy
            with open('fresh_m3u8_url.txt', 'w') as f:
                f.write(video_data.m3u8_url)
            print(f"\n💾 Saved to: fresh_m3u8_url.txt")
            
            # Test if it works
            print(f"\n{'='*70}")
            print("TESTING FRESH URL")
            print(f"{'='*70}")
            
            import requests
            try:
                print(f"  Checking availability...")
                response = requests.get(video_data.m3u8_url, timeout=10)
                
                if response.status_code == 200:
                    print(f"  ✅ Status: 200 OK")
                    print(f"  ✅ URL is valid and working!")
                    
                    if '#EXTM3U' in response.text:
                        variants = response.text.count('#EXT-X-STREAM-INF')
                        print(f"  ✅ Valid M3U8 playlist with {variants} quality variants")
                        
                        print(f"\n{'='*70}")
                        print("READY TO DOWNLOAD")
                        print(f"{'='*70}")
                        print(f"\nYou can now download with:")
                        print(f"  python test_16workers.py")
                        print(f"\nOr use the URL directly:")
                        print(f"  {video_data.m3u8_url[:80]}...")
                    else:
                        print(f"  ⚠️ Response is not a valid M3U8")
                else:
                    print(f"  ❌ Status: {response.status_code}")
                    print(f"  ⚠️ URL may not be working")
            except Exception as e:
                print(f"  ⚠️ Could not test URL: {e}")
        else:
            print(f"\n⚠️ No M3U8 URL extracted")
            print(f"  Only embed URL available: {video_data.embed_url}")
    else:
        print(f"\n❌ Failed to scrape video")
        
finally:
    scraper.close()

print(f"\n{'='*70}")
