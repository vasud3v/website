"""
Scrape latest movies from JAVDatabase homepage
Extract all metadata including actress images
"""

import json
import time
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from seleniumbase import Driver


@dataclass
class VideoData:
    """Video metadata from JAVDatabase"""
    code: str
    title: str
    cover_url: str
    actresses: List[str]
    actress_images: Dict[str, str]
    release_date: str
    runtime: str
    studio: str
    categories: List[str]
    javdb_url: str
    scraped_at: str


class JAVDBLatestScraper:
    """Scrape latest movies from JAVDatabase"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        
    def _init_driver(self):
        """Initialize browser"""
        if self.driver is None:
            print("Initializing browser...")
            self.driver = Driver(uc=True, headless=self.headless)
            time.sleep(2)
            print("Browser ready")
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def scrape_actress_image(self, actress_name: str) -> Optional[str]:
        """Get actress image from profile"""
        try:
            from urllib.parse import quote
            url = f"https://www.javdatabase.com/idols/?q={quote(actress_name)}"
            self.driver.get(url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find first valid idol link
            links = soup.find_all('a', href=re.compile(r'/idols/[a-z0-9-]+/$'))
            valid = [l for l in links if '/idols/?_' not in l.get('href', '')]
            
            if valid:
                profile_url = valid[0].get('href')
                if not profile_url.startswith('http'):
                    profile_url = 'https://www.javdatabase.com' + profile_url
                
                self.driver.get(profile_url)
                time.sleep(2)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Find image
                img = soup.find('img', src=re.compile(r'/idolimages/'))
                if img:
                    image_url = img.get('src', '')
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    elif image_url.startswith('/'):
                        image_url = 'https://www.javdatabase.com' + image_url
                    return image_url
            
            return None
        except:
            return None
    
    def scrape_movie_details(self, movie_url: str) -> Optional[VideoData]:
        """Scrape full movie details"""
        try:
            print(f"  Visiting: {movie_url}")
            self.driver.get(movie_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Get title
            h1 = soup.find('h1')
            title = h1.get_text(strip=True) if h1 else ""
            
            # Extract code from title or URL
            code_match = re.search(r'([A-Z]+-\d+)', title)
            if not code_match:
                code_match = re.search(r'/movies/([^/]+)/', movie_url)
            code = code_match.group(1).upper() if code_match else ""
            
            # Get cover image
            cover_url = ""
            cover_img = soup.find('img', alt=re.compile(r'JAV Movie|Cover', re.I))
            if cover_img:
                cover_url = cover_img.get('src', '')
                if cover_url.startswith('//'):
                    cover_url = 'https:' + cover_url
                elif cover_url.startswith('/'):
                    cover_url = 'https://www.javdatabase.com' + cover_url
            
            # Get actresses
            actresses = []
            actress_images = {}
            
            # Look for actress links
            actress_links = soup.find_all('a', href=re.compile(r'/idols/[a-z0-9-]+/$'))
            for link in actress_links:
                name = link.get_text(strip=True)
                if name and name not in actresses and len(name) > 2:  # Filter out short/invalid names
                    actresses.append(name)
                    print(f"    Actress: {name}")
                    
                    # Try to get image from link itself first
                    img = link.find('img')
                    if img:
                        img_url = img.get('src', '')
                        if img_url:
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            elif img_url.startswith('/'):
                                img_url = 'https://www.javdatabase.com' + img_url
                            actress_images[name] = img_url
                            print(f"      Image (inline): {img_url[:60]}...")
                            continue
                    
                    # If no inline image, scrape profile (slower)
                    img_url = self.scrape_actress_image(name)
                    if img_url:
                        actress_images[name] = img_url
                        print(f"      Image (profile): {img_url[:60]}...")
            
            # Get other metadata
            release_date = ""
            runtime = ""
            studio = ""
            categories = []
            
            # Parse info sections
            # (This depends on actual HTML structure)
            
            print(f"  >> {code}: {title[:50]}...")
            print(f"     Actresses: {len(actresses)}, Images: {len(actress_images)}")
            
            from datetime import datetime
            return VideoData(
                code=code,
                title=title,
                cover_url=cover_url,
                actresses=actresses,
                actress_images=actress_images,
                release_date=release_date,
                runtime=runtime,
                studio=studio,
                categories=categories,
                javdb_url=movie_url,
                scraped_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"  !! Error: {e}")
            return None
    
    def scrape_homepage(self, num_movies: int = 10) -> List[VideoData]:
        """Scrape latest movies from homepage"""
        self._init_driver()
        
        print("\n" + "="*60)
        print("Scraping JAVDatabase Homepage")
        print("="*60)
        
        # Go to homepage
        url = "https://www.javdatabase.com/movies/"
        print(f"\nLoading: {url}")
        self.driver.get(url)
        time.sleep(4)
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Find all movie links
        movie_links = []
        links = soup.find_all('a', href=re.compile(r'/movies/[a-z0-9-]+/$'))
        
        for link in links:
            href = link.get('href')
            if '/movies/?_' not in href and href != '/movies/':
                if not href.startswith('http'):
                    href = 'https://www.javdatabase.com' + href
                if href not in movie_links:
                    movie_links.append(href)
        
        print(f"Found {len(movie_links)} movie links")
        movie_links = movie_links[:num_movies]
        
        # Scrape each movie
        all_videos = []
        for i, movie_url in enumerate(movie_links, 1):
            print(f"\n[{i}/{len(movie_links)}]")
            
            video_data = self.scrape_movie_details(movie_url)
            if video_data:
                all_videos.append(video_data)
            
            time.sleep(2)
        
        return all_videos


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape latest movies from JAVDatabase')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--limit', type=int, default=10, help='Number of movies to scrape')
    parser.add_argument('--output', default='database/javdb_latest.json', help='Output file')
    
    args = parser.parse_args()
    
    scraper = JAVDBLatestScraper(headless=args.headless)
    
    try:
        videos = scraper.scrape_homepage(num_movies=args.limit)
        
        print(f"\n{'='*60}")
        print("SCRAPING COMPLETE")
        print("="*60)
        print(f"Total videos: {len(videos)}")
        
        if videos:
            # Save to file
            print(f"\nSaving to: {args.output}")
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump([asdict(v) for v in videos], f, indent=2, ensure_ascii=False)
            print("Done!")
            
            # Show summary
            print("\nVideos scraped:")
            for v in videos:
                print(f"  {v.code}: {v.title[:50]}... ({len(v.actresses)} actresses)")
    
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
