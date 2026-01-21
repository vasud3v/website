"""
JAVDatabase Complete Scraper
Scrapes complete metadata including actress images from JAVDatabase.com
Videos are downloaded from Jable.tv
"""

import re
import time
import json
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

from bs4 import BeautifulSoup
from seleniumbase import Driver


@dataclass
class ActressData:
    """Actress profile data"""
    name: str
    name_jp: str
    image_url: str
    profile_url: str
    age: Optional[str] = None
    birthdate: Optional[str] = None
    measurements: Optional[str] = None
    height: Optional[str] = None


@dataclass
class VideoMetadata:
    """Complete video metadata from JAVDatabase"""
    code: str
    title: str
    title_jp: str
    release_date: str
    runtime: str
    director: str
    studio: str
    label: str
    series: str
    cover_url: str
    thumbnail_url: str
    screenshots: List[str]
    actresses: List[str]  # Actress names
    actress_images: Dict[str, str]  # name -> image_url
    categories: List[str]
    description: str
    rating: float
    scraped_at: str
    javdb_url: str


class JAVDatabaseScraper:
    """Complete scraper for JAVDatabase.com"""
    
    BASE_URL = "https://www.javdatabase.com"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.actress_cache = {}  # Cache actress data
        
    def _init_driver(self):
        """Initialize browser"""
        if self.driver is None:
            print("Initializing browser...")
            try:
                self.driver = Driver(
                    uc=True, 
                    headless=self.headless,
                    headless2=self.headless,
                    incognito=True
                )
                time.sleep(2)
                print("  >> Browser ready")
            except Exception as e:
                print(f"  !! Headless failed, trying non-headless: {e}")
                self.driver = Driver(uc=True, headless=False)
                time.sleep(2)
                print("  >> Browser ready")
    
    def _ensure_driver(self):
        """Ensure driver is alive"""
        if self.driver is None:
            self._init_driver()
        else:
            try:
                _ = self.driver.current_url
            except:
                print("  !! Browser dead, restarting...")
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                self._init_driver()
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
    
    def scrape_actress_profile(self, actress_name: str) -> Optional[ActressData]:
        """
        Scrape actress profile from JAVDatabase
        
        Args:
            actress_name: Name of actress (Japanese or English)
            
        Returns:
            ActressData object or None
        """
        # Check cache first
        if actress_name in self.actress_cache:
            return self.actress_cache[actress_name]
        
        try:
            self._ensure_driver()
            
            from urllib.parse import quote
            search_url = f"{self.BASE_URL}/idols/?q={quote(actress_name)}"
            
            print(f"    Searching actress: {actress_name}")
            self.driver.get(search_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find first valid profile link
            idol_links = soup.find_all('a', href=re.compile(r'/idols/[a-z0-9-]+/$'))
            valid_links = [l for l in idol_links if '/idols/?_' not in l.get('href', '')]
            
            if not valid_links:
                print(f"    XX No profile found")
                return None
            
            # Visit profile
            profile_url = valid_links[0].get('href')
            if not profile_url.startswith('http'):
                profile_url = self.BASE_URL + profile_url
            
            self.driver.get(profile_url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract data
            name_elem = soup.find('h1')
            name = name_elem.get_text(strip=True) if name_elem else actress_name
            
            # Get image
            img = soup.find('img', src=re.compile(r'/idolimages/'))
            image_url = ""
            if img:
                image_url = img.get('src', '')
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    image_url = self.BASE_URL + image_url
            
            # Get Japanese name and other details
            name_jp = actress_name  # Default to input
            age = None
            birthdate = None
            measurements = None
            height = None
            
            # Look for profile details
            profile_info = soup.find('div', class_='idol-info')
            if profile_info:
                text = profile_info.get_text()
                # Parse details (format varies)
                # This is a simplified version
                pass
            
            actress_data = ActressData(
                name=name,
                name_jp=name_jp,
                image_url=image_url,
                profile_url=profile_url,
                age=age,
                birthdate=birthdate,
                measurements=measurements,
                height=height
            )
            
            # Cache it
            self.actress_cache[actress_name] = actress_data
            print(f"    >> Found: {name}")
            
            return actress_data
            
        except Exception as e:
            print(f"    !! Error: {e}")
            return None
    
    def scrape_video_metadata(self, video_code: str) -> Optional[VideoMetadata]:
        """
        Scrape complete video metadata from JAVDatabase
        
        Args:
            video_code: Video code (e.g., "MIDA-486")
            
        Returns:
            VideoMetadata object or None
        """
        try:
            self._ensure_driver()
            
            print(f"  Scraping: {video_code}")
            
            # Try direct URL first (convert code to URL format)
            # JAVDatabase URLs are like: /movies/mida-486/
            code_lower = video_code.lower().replace('_', '-')
            direct_url = f"{self.BASE_URL}/movies/{code_lower}/"
            
            print(f"  Trying direct URL: {direct_url}")
            self.driver.get(direct_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Check if page exists (not 404)
            title_elem = soup.find('h1')
            if not title_elem or '404' in title_elem.get_text() or 'not found' in title_elem.get_text().lower():
                print(f"  XX Not found (404)")
                return None
            
            title = title_elem.get_text(strip=True)
            
            # Verify this is the right video by checking if code is in title
            if video_code.upper() not in title.upper():
                print(f"  XX Code mismatch in title: {title}")
                return None
            
            movie_url = direct_url
            
            # Extract metadata
            print(f"  >> Found: {title[:60]}...")
            
            # Get cover image
            cover_url = ""
            cover_img = soup.find('img', alt=re.compile(video_code, re.IGNORECASE))
            if not cover_img:
                # Try finding large images
                imgs = soup.find_all('img', src=True)
                for img in imgs:
                    src = img.get('src', '')
                    if '/covers/' in src and video_code.lower() in src.lower():
                        cover_img = img
                        break
            
            if cover_img:
                cover_url = cover_img.get('src', '')
                if cover_url.startswith('//'):
                    cover_url = 'https:' + cover_url
                elif cover_url.startswith('/'):
                    cover_url = self.BASE_URL + cover_url
            
            # Get actresses
            actresses = []
            actress_images = {}
            
            # Look for actress links in the page
            actress_links = soup.find_all('a', href=re.compile(r'/idols/[a-z0-9-]+/$'))
            # Filter out navigation links
            valid_actress_links = []
            for link in actress_links:
                href = link.get('href', '')
                if href not in ['/idols/', '/idols/?_sort_=most_favorited'] and '/idols/?_' not in href:
                    valid_actress_links.append(link)
            
            print(f"  Found {len(valid_actress_links)} actress links")
            
            for link in valid_actress_links:
                actress_name = link.get_text(strip=True)
                if actress_name and actress_name not in ['All Idols', 'Most Favorited', 'Teen', 'Twenties', 'MILF']:
                    actresses.append(actress_name)
                    
                    # Get actress image
                    print(f"    Getting image for: {actress_name}")
                    actress_data = self.scrape_actress_profile(actress_name)
                    if actress_data and actress_data.image_url:
                        actress_images[actress_name] = actress_data.image_url
            
            # Get other metadata from page
            release_date = ""
            runtime = ""
            director = ""
            studio = ""
            label = ""
            series = ""
            categories = []
            description = ""
            rating = 0.0
            
            # Look for metadata in structured format
            # JAVDatabase uses various formats, try to extract what we can
            page_text = soup.get_text()
            
            # Try to find release date
            date_match = re.search(r'Release Date:?\s*(\d{4}-\d{2}-\d{2})', page_text)
            if date_match:
                release_date = date_match.group(1)
            
            # Try to find runtime
            runtime_match = re.search(r'Runtime:?\s*(\d+)\s*min', page_text)
            if runtime_match:
                runtime = runtime_match.group(1) + ' min'
            
            # Get screenshots
            screenshots = []
            screenshot_imgs = soup.find_all('img', src=re.compile(r'/screenshots/'))
            for img in screenshot_imgs:
                src = img.get('src', '')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = self.BASE_URL + src
                    screenshots.append(src)
            
            print(f"  >> Actresses: {', '.join(actresses) if actresses else 'None'}")
            print(f"  >> Actress images: {len(actress_images)}")
            print(f"  >> Screenshots: {len(screenshots)}")
            
            return VideoMetadata(
                code=video_code.upper(),
                title=title,
                title_jp=title,
                release_date=release_date,
                runtime=runtime,
                director=director,
                studio=studio,
                label=label,
                series=series,
                cover_url=cover_url,
                thumbnail_url=cover_url,
                screenshots=screenshots,
                actresses=actresses,
                actress_images=actress_images,
                categories=categories,
                description=description,
                rating=rating,
                scraped_at=datetime.now().isoformat(),
                javdb_url=movie_url
            )
            
        except Exception as e:
            print(f"  !! Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_latest_videos(self, num_pages: int = 1) -> List[VideoMetadata]:
        """
        Scrape latest videos from JAVDatabase homepage
        
        Args:
            num_pages: Number of pages to scrape
            
        Returns:
            List of VideoMetadata objects
        """
        all_videos = []
        
        for page in range(1, num_pages + 1):
            print(f"\n{'='*60}")
            print(f"PAGE {page}/{num_pages}")
            print('='*60)
            
            try:
                self._ensure_driver()
                
                if page == 1:
                    url = f"{self.BASE_URL}/movies/"
                else:
                    url = f"{self.BASE_URL}/movies/?page={page}"
                
                self.driver.get(url)
                time.sleep(3)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Find all movie cards
                movie_cards = soup.find_all('div', class_='movie-card')
                print(f"Found {len(movie_cards)} movies on page")
                
                for i, card in enumerate(movie_cards, 1):
                    # Extract video code from card
                    code_elem = card.find('span', class_='movie-code')
                    if code_elem:
                        video_code = code_elem.get_text(strip=True)
                        
                        print(f"\n[{i}/{len(movie_cards)}] {video_code}")
                        
                        metadata = self.scrape_video_metadata(video_code)
                        if metadata:
                            all_videos.append(metadata)
                        
                        time.sleep(2)  # Be nice to server
                
            except Exception as e:
                print(f"!! Error on page {page}: {e}")
                continue
        
        return all_videos


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape metadata from JAVDatabase')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages to scrape')
    parser.add_argument('--code', help='Scrape specific video code')
    parser.add_argument('--output', default='database/javdb_metadata.json', help='Output file')
    
    args = parser.parse_args()
    
    scraper = JAVDatabaseScraper(headless=args.headless)
    
    try:
        if args.code:
            # Scrape single video
            print(f"\nScraping video: {args.code}")
            metadata = scraper.scrape_video_metadata(args.code)
            if metadata:
                print(f"\n{json.dumps(asdict(metadata), indent=2, ensure_ascii=False)}")
        else:
            # Scrape latest videos
            videos = scraper.scrape_latest_videos(num_pages=args.pages)
            
            print(f"\n{'='*60}")
            print(f"SCRAPING COMPLETE")
            print('='*60)
            print(f"Total videos: {len(videos)}")
            
            if videos:
                # Save to file
                print(f"\nSaving to: {args.output}")
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump([asdict(v) for v in videos], f, indent=2, ensure_ascii=False)
                print("Done!")
    
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
