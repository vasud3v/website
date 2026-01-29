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
    debut_date: Optional[str] = None
    debut_age: Optional[str] = None
    birthplace: Optional[str] = None
    zodiac_sign: Optional[str] = None
    blood_type: Optional[str] = None
    cup_size: Optional[str] = None
    shoe_size: Optional[str] = None
    hair_length: Optional[str] = None
    hair_color: Optional[str] = None


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
    actress_details: Dict[str, Dict] = None  # name -> full ActressData dict (must be last with default)


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
            
            # Get Japanese name and other details from profile page
            name_jp = actress_name  # Default to input
            age = None
            birthdate = None
            measurements = None
            height = None
            
            # Debug: Save page source for inspection
            debug_save = False  # Set to True to debug
            if debug_save:
                debug_file = f"actress_profile_{actress_name.replace(' ', '_')}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                print(f"      Debug: Saved to {debug_file}")
            
            # Look for profile details in various formats
            # Pattern 1: Look for <p class="mb-1"> tags with metadata
            info_paragraphs = soup.find_all('p', class_='mb-1')
            print(f"      Found {len(info_paragraphs)} info paragraphs")
            
            for p in info_paragraphs:
                text = p.get_text(strip=True)
                
                # Extract birthdate
                if 'Birth' in text or 'DOB' in text or 'Born' in text or 'Date of Birth' in text:
                    print(f"      Birth text: {text}")
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                    if date_match:
                        birthdate = date_match.group(1)
                        # Calculate age
                        try:
                            from datetime import datetime
                            birth_year = int(birthdate[:4])
                            current_year = datetime.now().year
                            age = str(current_year - birth_year)
                        except:
                            pass
                
                # Extract height
                if 'Height' in text or 'height' in text:
                    print(f"      Height text: {text}")
                    height_match = re.search(r'(\d+)\s*cm', text, re.I)
                    if height_match:
                        height = height_match.group(1) + ' cm'
                
                # Extract measurements (B-W-H)
                if 'Measurements' in text or 'BWH' in text or 'measurements' in text:
                    print(f"      Measurements text: {text}")
                    # Look for pattern like "88-58-86" or "B88-W58-H86"
                    meas_match = re.search(r'(\d{2,3}[-\s]*\d{2,3}[-\s]*\d{2,3})', text)
                    if meas_match:
                        measurements = meas_match.group(1)
            
            # Pattern 2: Look in table format
            if not birthdate or not height or not measurements:
                tables = soup.find_all('table')
                print(f"      Found {len(tables)} tables")
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            label = cells[0].get_text(strip=True).lower()
                            value = cells[1].get_text(strip=True)
                            
                            if 'birth' in label or 'dob' in label:
                                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', value)
                                if date_match:
                                    birthdate = date_match.group(1)
                            
                            if 'height' in label:
                                height_match = re.search(r'(\d+)', value)
                                if height_match:
                                    height = height_match.group(1) + ' cm'
                            
                            if 'measure' in label or 'bwh' in label:
                                meas_match = re.search(r'(\d{2,3}[-\s]*\d{2,3}[-\s]*\d{2,3})', value)
                                if meas_match:
                                    measurements = meas_match.group(1)
            
            # Pattern 3: Look for any text containing measurements pattern
            if not measurements:
                all_text = soup.get_text()
                # Look for B-W-H pattern anywhere in page
                meas_match = re.search(r'(?:BWH|Measurements|measurements)[\s:]*(\d{2,3}[-\s]*\d{2,3}[-\s]*\d{2,3})', all_text, re.I)
                if meas_match:
                    measurements = meas_match.group(1)
                    print(f"      Found measurements in text: {measurements}")
            
            # Pattern 4: Look for Japanese name
            # Often in format: "Name (Japanese Name)"
            if name and '(' in name and ')' in name:
                parts = name.split('(')
                if len(parts) == 2:
                    name = parts[0].strip()
                    name_jp = parts[1].replace(')', '').strip()
            
            print(f"      Details: age={age}, birth={birthdate}, height={height}, measurements={measurements}")
            
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
            
            actress_details = {}  # Store full actress data
            
            for link in valid_actress_links:
                actress_name = link.get_text(strip=True)
                if actress_name and actress_name not in ['All Idols', 'Most Favorited', 'Teen', 'Twenties', 'MILF']:
                    actresses.append(actress_name)
                    
                    # Get full actress profile data
                    print(f"    Getting profile for: {actress_name}")
                    actress_data = self.scrape_actress_profile(actress_name)
                    if actress_data:
                        # Store image URL for backward compatibility
                        if actress_data.image_url:
                            actress_images[actress_name] = actress_data.image_url
                        
                        # Store full actress details
                        actress_details[actress_name] = {
                            'name': actress_data.name,
                            'name_jp': actress_data.name_jp,
                            'image': actress_data.image_url,
                            'profile_url': actress_data.profile_url,
                            'age': actress_data.age,
                            'birthdate': actress_data.birthdate,
                            'measurements': actress_data.measurements,
                            'height': actress_data.height
                        }
                        print(f"      ✓ Profile saved: {actress_data.name}")
            
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
            
            # Look for metadata in structured format using HTML parsing
            # JAVDatabase uses <p class="mb-1"><b>Field:</b> value</p> format
            
            # Try to find release date
            release_date = ""
            date_elem = soup.find('b', string=re.compile(r'Release Date:', re.I))
            if date_elem and date_elem.parent:
                date_text = date_elem.parent.get_text()
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                if date_match:
                    release_date = date_match.group(1)
            
            # Try to find runtime
            runtime = ""
            runtime_elem = soup.find('b', string=re.compile(r'Runtime:', re.I))
            if runtime_elem and runtime_elem.parent:
                runtime_text = runtime_elem.parent.get_text()
                runtime_match = re.search(r'(\d+)\s*min', runtime_text)
                if runtime_match:
                    runtime = runtime_match.group(1) + ' min'
            
            # Try to find director
            director = ""
            director_elem = soup.find('b', string=re.compile(r'Director:', re.I))
            if director_elem and director_elem.parent:
                # Get the parent <p> tag
                p_tag = director_elem.parent
                # Look for <a> tag after the <b> tag
                link = p_tag.find('a')
                if link:
                    director = link.get_text(strip=True)
            
            # Try to find studio
            studio = ""
            studio_elem = soup.find('b', string=re.compile(r'Studio:', re.I))
            if studio_elem and studio_elem.parent:
                p_tag = studio_elem.parent
                link = p_tag.find('a')
                if link:
                    studio = link.get_text(strip=True)
            
            # Try to find label (not present in this video, but keep for others)
            label = ""
            label_elem = soup.find('b', string=re.compile(r'Label:', re.I))
            if label_elem and label_elem.parent:
                p_tag = label_elem.parent
                link = p_tag.find('a')
                if link:
                    label = link.get_text(strip=True)
            
            # Try to find series
            series = ""
            series_elem = soup.find('b', string=re.compile(r'JAV Series:', re.I))
            if series_elem and series_elem.parent:
                p_tag = series_elem.parent
                link = p_tag.find('a')
                if link:
                    series = link.get_text(strip=True)
            
            # Get categories/genres
            categories = []
            # Pattern 1: Look for "Genres:" or "Categories:" label
            genre_elem = soup.find('b', string=re.compile(r'Genres?:|Categories:', re.I))
            if genre_elem and genre_elem.parent:
                p_tag = genre_elem.parent
                # Get all <a> tags after the <b> tag
                genre_links = p_tag.find_all('a')
                for link in genre_links:
                    genre = link.get_text(strip=True)
                    if genre and genre not in categories:
                        categories.append(genre)
            
            # Pattern 2: Look for links with /genres/ in href
            if not categories:
                genre_links = soup.find_all('a', href=re.compile(r'/genres/'))
                for link in genre_links:
                    genre = link.get_text(strip=True)
                    # Filter out navigation items
                    if genre and genre not in ['All Genres', 'Most Popular'] and genre not in categories:
                        categories.append(genre)
            
            # Get description
            description = ""
            # Look for description in various places
            desc_elem = soup.find('div', class_='movie-description')
            if not desc_elem:
                desc_elem = soup.find('p', class_='description')
            if not desc_elem:
                # Look for any paragraph with substantial text
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 100 and video_code.upper() not in text.upper():
                        desc_elem = p
                        break
            
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Get rating
            rating = 0.0
            # Look for rating in various formats
            rating_elem = soup.find('span', class_='rating')
            if not rating_elem:
                rating_elem = soup.find('div', class_='rating')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                    except:
                        pass
            
            # Get screenshots - look for multiple patterns and try to get full-size
            screenshots = []
            
            # Pattern 1: Look for <a> tags with data-image-href (full-size URL already provided)
            screenshot_links = soup.find_all('a', attrs={'data-image-href': True})
            for link in screenshot_links:
                full_size = link.get('data-image-href', '')
                if full_size and 'cap_e_' in full_size:  # mgstage full-size pattern
                    if full_size.startswith('//'):
                        full_size = 'https:' + full_size
                    elif full_size.startswith('/'):
                        full_size = 'https://www.javdatabase.com' + full_size
                    if full_size not in screenshots:
                        screenshots.append(full_size)
            
            # Pattern 2: Look for images with "Screenshot" in alt text and convert to full-size
            if not screenshots:
                screenshot_imgs = soup.find_all('img', alt=re.compile(r'Screenshot', re.I))
                for img in screenshot_imgs:
                    src = img.get('src', '')
                    if src and 'cap_t1_' in src:  # mgstage screenshot pattern (thumbnail)
                        # Convert to full-size version by replacing cap_t1_ with cap_e_
                        full_size = src.replace('cap_t1_', 'cap_e_')
                        if full_size.startswith('//'):
                            full_size = 'https:' + full_size
                        elif full_size.startswith('/'):
                            full_size = 'https://www.javdatabase.com' + full_size
                        if full_size not in screenshots:
                            screenshots.append(full_size)
            
            # Pattern 3: Look for images from mgstage with cap_t1_ pattern
            if not screenshots:
                all_imgs = soup.find_all('img', src=re.compile(r'cap_t1_'))
                for img in all_imgs:
                    src = img.get('src', '')
                    if src:
                        # Convert to full-size version
                        full_size = src.replace('cap_t1_', 'cap_e_')
                        if full_size.startswith('//'):
                            full_size = 'https:' + full_size
                        elif full_size.startswith('/'):
                            full_size = 'https://www.javdatabase.com' + full_size
                        if full_size not in screenshots:
                            screenshots.append(full_size)
            
            # Pattern 4: Original pattern for /screenshots/ URLs
            if not screenshots:
                screenshot_imgs = soup.find_all('img', src=re.compile(r'/screenshots/'))
                for img in screenshot_imgs:
                    src = img.get('src', '')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = self.BASE_URL + src
                        if src not in screenshots:
                            screenshots.append(src)
            
            print(f"  >> Actresses: {', '.join(actresses) if actresses else 'None'}")
            print(f"  >> Actress images: {len(actress_images)}")
            print(f"  >> Actress details: {len(actress_details)}")
            print(f"  >> Screenshots: {len(screenshots)}")
            print(f"  >> Categories: {len(categories)} - {', '.join(categories[:5]) if categories else 'None'}")
            print(f"  >> Director: {director if director else 'None'}")
            print(f"  >> Studio: {studio if studio else 'None'}")
            print(f"  >> Label: {label if label else 'None'}")
            print(f"  >> Series: {series if series else 'None'}")
            print(f"  >> Release Date: {release_date if release_date else 'None'}")
            print(f"  >> Runtime: {runtime if runtime else 'None'}")
            print(f"  >> Rating: {rating if rating > 0 else 'None'}")
            print(f"  >> Description: {description[:100] if description else 'None'}...")
            
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
                actress_details=actress_details,  # Add full actress details
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
