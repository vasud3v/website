"""
Clean JAVDatabase Scraper with Proper Data Structure
Scrapes complete metadata with well-organized format
"""

import json
import time
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
from bs4 import BeautifulSoup
from seleniumbase import Driver
from datetime import datetime


@dataclass
class ActressProfile:
    """Actress profile with clean structure"""
    actress_name: str
    actress_name_jp: Optional[str] = None
    actress_name_alt: Optional[str] = None  # Alternate name
    actress_image_url: Optional[str] = None
    
    # Physical attributes
    actress_age: Optional[int] = None
    actress_birthdate: Optional[str] = None  # Debut date if DOB not available
    actress_birthplace: Optional[str] = None
    actress_height_cm: Optional[int] = None
    actress_shoe_size: Optional[str] = None
    
    # Measurements
    actress_bust_cm: Optional[int] = None
    actress_waist_cm: Optional[int] = None
    actress_hips_cm: Optional[int] = None
    actress_cup_size: Optional[str] = None
    
    # Appearance
    actress_hair_length: Optional[str] = None
    actress_hair_color: Optional[str] = None
    
    # Other
    actress_blood_type: Optional[str] = None
    actress_zodiac_sign: Optional[str] = None
    actress_debut_date: Optional[str] = None
    actress_debut_age: Optional[int] = None


@dataclass
class VideoMetadata:
    """Video metadata with clean structure"""
    # Identifiers
    code: str
    title: str
    title_jp: Optional[str] = None
    
    # Media URLs
    cover_url: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    
    # Cast (list of full profile objects)
    cast: List[ActressProfile] = field(default_factory=list)
    
    # Production Info
    release_date: Optional[str] = None  # YYYY-MM-DD format
    runtime_minutes: Optional[int] = None
    director: Optional[str] = None
    studio: Optional[str] = None
    label: Optional[str] = None
    series: Optional[str] = None
    
    # Content
    genres: List[str] = field(default_factory=list)
    description: Optional[str] = None
    
    # Ratings
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    
    # Metadata
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None


class CleanJAVDBScraper:
    """Clean scraper with proper data structure"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.actress_cache = {}
        
    def _init_driver(self):
        """Initialize browser"""
        if self.driver is None:
            print("Initializing browser...")
            try:
                # Try with headless2 mode for better compatibility on Windows
                self.driver = Driver(
                    uc=True, 
                    headless=self.headless,
                    headless2=self.headless,  # Use new headless mode
                    incognito=True
                )
                time.sleep(2)
                print("Browser ready\n")
            except Exception as e:
                print(f"Headless mode failed: {e}")
                print("Trying non-headless mode...")
                try:
                    self.driver = Driver(uc=True, headless=False)
                    time.sleep(2)
                    print("Browser ready (non-headless)\n")
                except Exception as e2:
                    print(f"Browser initialization failed: {e2}")
                    raise
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def _parse_measurements(self, text: str) -> tuple:
        """Parse measurements string like '88-58-86' into tuple"""
        try:
            match = re.search(r'(\d{2,3})[-\s]+(\d{2,3})[-\s]+(\d{2,3})', text)
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except:
            pass
        return (None, None, None)
    
    def _extract_actress_profile(self, soup: BeautifulSoup, profile_url: str, actress_name: str) -> Optional[ActressProfile]:
        """Extract actress profile with clean structure"""
        try:
            # Get name from page
            h1 = soup.find('h1')
            name_on_page = h1.get_text(strip=True) if h1 else actress_name
            # Remove " - JAV Profile" suffix
            name_on_page = re.sub(r'\s*-\s*JAV Profile\s*$', '', name_on_page)
            
            # Get image
            image_url = None
            img = soup.find('img', src=re.compile(r'/idolimages/'))
            if img:
                image_url = img.get('src', '')
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    image_url = 'https://www.javdatabase.com' + image_url
            
            page_text = soup.get_text()
            
            # Helper function to extract value (returns None if value is '?')
            def extract_value(pattern, text, group=1, convert=None):
                match = re.search(pattern, text, re.I)
                if match:
                    value = match.group(group).strip()
                    if value and value != '?':
                        if convert:
                            try:
                                return convert(value)
                            except:
                                return None
                        return value
                return None
            
            # Age
            age = extract_value(r'Age[:\s]*([^\s-]+)', page_text, convert=lambda x: int(x) if x != '?' else None)
            
            # DOB (Date of Birth)
            dob = extract_value(r'DOB[:\s]*([^\s-]+)', page_text)
            
            # Debut date
            debut_date = extract_value(r'Debut[:\s]*(\d{4}-\d{2}-\d{2})', page_text)
            
            # Debut age
            debut_age = extract_value(r'Debut Age[:\s]*([^\s-]+)', page_text, convert=lambda x: int(x) if x != '?' else None)
            
            # Birthplace
            birthplace = extract_value(r'Birthplace[:\s]*([^\s-]+)', page_text)
            
            # Zodiac sign
            zodiac_sign = extract_value(r'Sign[:\s]*([^\s-]+)', page_text)
            
            # Blood type
            blood_type = extract_value(r'Blood[:\s]*([^\s-]+)', page_text)
            
            # Measurements - try multiple patterns
            measurements_text = extract_value(r'Measurements[:\s]*([^\s-]+)', page_text)
            bust_cm, waist_cm, hips_cm = None, None, None
            if measurements_text and measurements_text != '?':
                bust_cm, waist_cm, hips_cm = self._parse_measurements(measurements_text)
            
            # If not found, try alternative format like "B88-W58-H86"
            if not bust_cm:
                alt_measurements = re.search(r'B(\d{2,3})[-\s]*W(\d{2,3})[-\s]*H(\d{2,3})', page_text, re.I)
                if alt_measurements:
                    bust_cm = int(alt_measurements.group(1))
                    waist_cm = int(alt_measurements.group(2))
                    hips_cm = int(alt_measurements.group(3))
            
            # Cup size
            cup_size = extract_value(r'Cup[:\s]*([^\s-]+)', page_text)
            
            # Height
            height_cm = extract_value(r'Height[:\s]*(\d+)\s*cm', page_text, convert=int)
            
            # Shoe size
            shoe_size = extract_value(r'Shoe Size[:\s]*([^\s-]+)', page_text)
            
            # Hair length - clean up trailing commas
            hair_length = extract_value(r'Hair Length\(s\)[:\s]*([^\s-]+)', page_text)
            if hair_length:
                hair_length = hair_length.rstrip(',')
            
            # Hair color - clean up trailing commas
            hair_color = extract_value(r'Hair Color\(s\)[:\s]*([^\n-]+)', page_text)
            if hair_color:
                hair_color = hair_color.rstrip(',')
            
            # Tags - filter out "Suggest Tags"
            tags = []
            tags_match = re.search(r'Tags[:\s]+([^\n]+)', page_text, re.I)
            if tags_match:
                tags_text = tags_match.group(1)
                tag_list = re.split(r'\s*-\s*', tags_text)
                tags = [t.strip() for t in tag_list if t.strip() and t.strip() != '?' and 'Suggest Tags' not in t]
            
            # Japanese name
            name_jp = extract_value(r'JP[:\s]+([^\s-]+)', page_text)
            
            # Alternate name
            name_alt = extract_value(r'Alt[:\s]+([^\n]+)', page_text)
            
            return ActressProfile(
                actress_name=name_on_page,
                actress_name_jp=name_jp,
                actress_name_alt=name_alt,
                actress_image_url=image_url,
                actress_age=age,
                actress_birthdate=dob or debut_date,  # Use debut date if DOB not available
                actress_birthplace=birthplace,
                actress_height_cm=height_cm,
                actress_shoe_size=shoe_size,
                actress_bust_cm=bust_cm,
                actress_waist_cm=waist_cm,
                actress_hips_cm=hips_cm,
                actress_cup_size=cup_size,
                actress_hair_length=hair_length,
                actress_hair_color=hair_color,
                actress_blood_type=blood_type,
                actress_zodiac_sign=zodiac_sign,
                actress_debut_date=debut_date,
                actress_debut_age=debut_age
            )
        except Exception as e:
            print(f"         Error extracting profile: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_video_by_code(self, video_code: str) -> Optional[VideoMetadata]:
        """
        Scrape video metadata with clean structure
        
        Args:
            video_code: Video code like "MIDA-486"
            
        Returns:
            VideoMetadata object or None
        """
        try:
            # Ensure driver is initialized
            if self.driver is None:
                self._init_driver()
            
            # Build direct URL
            code_lower = video_code.lower()
            url = f"https://www.javdatabase.com/movies/{code_lower}/"
            
            self.driver.set_page_load_timeout(15)
            
            print(f"  Fetching: {url}")
            
            # Try with retry
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    self.driver.get(url)
                    break
                except:
                    if attempt < max_retries - 1:
                        print(f"  .. Retry {attempt + 1}/{max_retries}")
                        time.sleep(2)
                    else:
                        print(f"  XX Timeout loading page")
                        return None
            
            time.sleep(2)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Check if found
            h1 = soup.find('h1')
            if not h1:
                print(f"  XX Not found")
                return None
            
            title = h1.get_text(strip=True)
            
            if '404' in title or 'not found' in title.lower():
                print(f"  XX Not found (404)")
                return None
            
            print(f"  >> Found: {title[:60]}...")
            
            # Japanese title - look in multiple places
            title_jp = None
            jp_title_elem = soup.find('h2', class_=re.compile(r'jp|japanese', re.I))
            if not jp_title_elem:
                # Try finding by text pattern (Japanese characters)
                h2_tags = soup.find_all('h2')
                for h2 in h2_tags:
                    text = h2.get_text(strip=True)
                    # Check if contains Japanese characters
                    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text):
                        jp_title_elem = h2
                        break
            if jp_title_elem:
                title_jp = jp_title_elem.get_text(strip=True)
            
            # Cover image
            cover_url = None
            cover_img = soup.find('img', alt=re.compile(r'JAV Movie|Cover', re.I))
            if not cover_img:
                imgs = soup.find_all('img', src=True)
                for img in imgs:
                    src = img.get('src', '')
                    if '/covers/' in src:
                        cover_img = img
                        break
            
            if cover_img:
                cover_url = cover_img.get('src', '')
                if cover_url.startswith('//'):
                    cover_url = 'https:' + cover_url
                elif cover_url.startswith('/'):
                    cover_url = 'https://www.javdatabase.com' + cover_url
            
            # Cast profiles
            cast = []
            actress_links = soup.find_all('a', href=re.compile(r'/idols/[a-z0-9-]+/$'))
            
            for link in actress_links:
                href = link.get('href', '')
                if '/idols/?_' in href or href == '/idols/':
                    continue
                
                name = link.get_text(strip=True)
                if name and len(name) > 2:
                    if name in ['All Idols', 'Most Favorited', 'Teen', 'Twenties', 'MILF', 'Thirties']:
                        continue
                    
                    # Check if already added
                    if any(actress.actress_name == name for actress in cast):
                        continue
                    
                    print(f"     Actress: {name}")
                    
                    # Visit profile
                    try:
                        profile_href = href if href.startswith('http') else 'https://www.javdatabase.com' + href
                        
                        self.driver.set_page_load_timeout(10)
                        self.driver.get(profile_href)
                        time.sleep(2)
                        
                        profile_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        profile = self._extract_actress_profile(profile_soup, profile_href, name)
                        
                        if profile:
                            cast.append(profile)
                            details = []
                            if profile.actress_age:
                                details.append(f"Age: {profile.actress_age}")
                            if profile.actress_height_cm:
                                details.append(f"Height: {profile.actress_height_cm}cm")
                            if profile.actress_bust_cm:
                                details.append(f"B{profile.actress_bust_cm}-W{profile.actress_waist_cm}-H{profile.actress_hips_cm}")
                            if details:
                                print(f"       {', '.join(details)}")
                        
                        self.driver.back()
                        time.sleep(1)
                    except Exception as e:
                        print(f"       Error: {e}")
                        try:
                            self.driver.back()
                            time.sleep(1)
                        except:
                            pass
            
            # Extract metadata
            page_text = soup.get_text()
            
            # Release date
            release_date = None
            release_match = re.search(r'Release[d]?\s*Date[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})', page_text, re.I)
            if release_match:
                release_date = release_match.group(1).replace('/', '-')
            
            # Runtime
            runtime_minutes = None
            runtime_match = re.search(r'(?:Runtime|Duration)[:\s]+(\d+)\s*min', page_text, re.I)
            if runtime_match:
                runtime_minutes = int(runtime_match.group(1))
            
            # Director
            director = None
            director_match = re.search(r'Director[:\s]+([^\n]+)', page_text, re.I)
            if director_match:
                director = director_match.group(1).strip()
                # Clean up if it contains other fields
                for field in ['Genre(s):', 'Studio:', 'Label:', 'Series:']:
                    if field in director:
                        director = director.split(field)[0].strip()
                # Filter out if it's just a placeholder
                if director in ['?', '-', 'N/A', '']:
                    director = None
            
            # Studio
            studio = None
            studio_match = re.search(r'Studio[:\s]+([^\n]+)', page_text, re.I)
            if studio_match:
                studio = studio_match.group(1).strip()
                # Clean up
                for field in ['Label:', 'Series:', 'Genre(s):']:
                    if field in studio:
                        studio = studio.split(field)[0].strip()
                if studio in ['?', '-', 'N/A', '']:
                    studio = None
            
            # Label
            label = None
            label_match = re.search(r'Label[:\s]+([^\n]+)', page_text, re.I)
            if label_match:
                label = label_match.group(1).strip()
                # Clean up
                for field in ['Series:', 'Genre(s):', 'Studio:']:
                    if field in label:
                        label = label.split(field)[0].strip()
                if label in ['?', '-', 'N/A', '']:
                    label = None
            
            # Series
            series = None
            series_match = re.search(r'Series[:\s]+([^\n]+)', page_text, re.I)
            if series_match:
                series = series_match.group(1).strip()
                # Clean up
                for field in ['Genre(s):', 'Studio:', 'Label:']:
                    if field in series:
                        series = series.split(field)[0].strip()
                # Filter out navigation text and placeholders
                if series in ['Studios', 'Series', '?', '-', 'N/A', '']:
                    series = None
            
            # Genres - split by spaces and clean up
            genres = []
            genre_match = re.search(r'Genre\(s\)[:\s]+([^\n]+)', page_text, re.I)
            if genre_match:
                genre_text = genre_match.group(1)
                # Split by multiple spaces or common separators
                genre_list = re.split(r'\s{2,}|,\s*', genre_text)
                for genre in genre_list:
                    genre = genre.strip()
                    # Further split camelCase or concatenated words
                    if genre and len(genre) > 1:
                        # Split by capital letters for things like "BigTitsCreampie"
                        words = re.findall(r'[A-Z][a-z]*|[a-z]+', genre)
                        if len(words) > 1:
                            genres.extend([w for w in words if len(w) > 1])
                        else:
                            genres.append(genre)
            
            # Screenshots - extract both thumbnail and high-quality versions
            screenshots = []
            
            # Method 1: Look for images with data-image-href attribute (high-quality versions)
            modal_imgs = soup.find_all('a', attrs={'data-image-href': True})
            for link in modal_imgs:
                hq_src = link.get('data-image-href', '')  # High quality with 'jp' suffix
                if hq_src and 'pics.dmm.co.jp' in hq_src:
                    if hq_src not in screenshots:
                        screenshots.append(hq_src)
            
            # Method 2: If no high-quality found, use data-image-src (standard quality)
            if not screenshots:
                modal_imgs = soup.find_all('a', attrs={'data-image-src': True})
                for link in modal_imgs:
                    src = link.get('data-image-src', '')
                    if src and 'pics.dmm.co.jp' in src:
                        if src not in screenshots:
                            screenshots.append(src)
            
            # Method 3: Look for screenshot images with alt text containing "Screenshot"
            if not screenshots:
                screenshot_imgs = soup.find_all('img', alt=re.compile(r'Screenshot', re.I))
                for img in screenshot_imgs:
                    src = img.get('src', '')
                    if src and 'pics.dmm.co.jp' in src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        if src not in screenshots:
                            screenshots.append(src)
            
            print(f"     Release: {release_date}, Runtime: {runtime_minutes}min")
            print(f"     Studio: {studio}, Genres: {len(genres)}")
            print(f"     Cast: {len(cast)}, Screenshots: {len(screenshots)}")
            
            return VideoMetadata(
                code=video_code.upper(),
                title=title,
                title_jp=title_jp,
                cover_url=cover_url,
                screenshots=screenshots,
                cast=cast,
                release_date=release_date,
                runtime_minutes=runtime_minutes,
                director=director,
                studio=studio,
                label=label,
                series=series,
                genres=genres,
                source_url=url,
                scraped_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"  !! Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_from_jable_database(self, jable_db_path: str) -> List[VideoMetadata]:
        """Scrape all videos from Jable database"""
        self._init_driver()
        
        print("="*60)
        print("Clean JAVDatabase Scraper")
        print("="*60)
        
        # Load Jable database
        print(f"\nLoading Jable database: {jable_db_path}")
        with open(jable_db_path, 'r', encoding='utf-8') as f:
            jable_videos = json.load(f)
        
        print(f"Found {len(jable_videos)} videos\n")
        
        # Extract codes
        codes = [v.get('code') for v in jable_videos if v.get('code')]
        codes = list(dict.fromkeys(codes))  # Remove duplicates
        
        print(f"Unique codes: {len(codes)}\n")
        
        # Scrape each
        all_videos = []
        for i, code in enumerate(codes, 1):
            print(f"[{i}/{len(codes)}] {code}")
            
            video_data = self.scrape_video_by_code(code)
            if video_data:
                all_videos.append(video_data)
            
            time.sleep(2)
        
        return all_videos


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean JAVDatabase scraper')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--jable-db', default='../jable/database/videos_complete.json', help='Jable database path')
    parser.add_argument('--output', default='database/javdb_clean.json', help='Output file')
    parser.add_argument('--limit', type=int, help='Limit number of videos')
    parser.add_argument('--code', help='Scrape single video code')
    
    args = parser.parse_args()
    
    scraper = CleanJAVDBScraper(headless=args.headless)
    
    try:
        if args.code:
            scraper._init_driver()
            print(f"\nScraping: {args.code}\n")
            video_data = scraper.scrape_video_by_code(args.code)
            if video_data:
                # Convert to dict for JSON
                output = asdict(video_data)
                print(f"\n{json.dumps(output, indent=2, ensure_ascii=False)}")
        else:
            videos = scraper.scrape_from_jable_database(args.jable_db)
            
            if args.limit:
                videos = videos[:args.limit]
            
            print(f"\n{'='*60}")
            print("COMPLETE")
            print("="*60)
            print(f"Videos scraped: {len(videos)}")
            print(f"With cast: {sum(1 for v in videos if v.cast)}")
            
            if videos:
                print(f"\nSaving to: {args.output}")
                output = [asdict(v) for v in videos]
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
                print("Done!")
    
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
