"""
Scrape JAVDatabase using video codes from Jable database
This matches Jable videos with JAVDatabase metadata
"""

import json
import time
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from seleniumbase import Driver


@dataclass
class ActressProfile:
    """Actress profile details"""
    name: str
    name_jp: str
    image_url: str
    profile_url: str
    age: Optional[str] = None
    birthdate: Optional[str] = None
    measurements: Optional[str] = None
    height: Optional[str] = None
    blood_type: Optional[str] = None
    debut: Optional[str] = None


@dataclass
class VideoData:
    """Video metadata from JAVDatabase"""
    code: str
    title: str
    title_jp: str  # Japanese title
    cover_url: str
    screenshots: List[str]  # Screenshot images
    actresses: List[str]
    actress_images: Dict[str, str]
    actress_profiles: Dict[str, dict]  # name -> full profile data
    release_date: str
    runtime: str
    director: str
    studio: str
    label: str  # Production label
    series: str  # Series name
    categories: List[str]  # Genres/tags
    description: str  # Plot/description
    rating: Optional[float]  # User rating
    rating_count: Optional[int]  # Number of ratings
    javdb_url: str
    scraped_at: str
    found: bool  # Whether found on JAVDatabase


class JAVDBCodeScraper:
    """Scrape JAVDatabase using specific video codes"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.actress_cache = {}
        
    def _init_driver(self):
        """Initialize browser"""
        if self.driver is None:
            print("Initializing browser...")
            self.driver = Driver(uc=True, headless=self.headless)
            time.sleep(2)
            print("Browser ready\n")
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def _extract_actress_profile(self, soup: BeautifulSoup, profile_url: str, actress_name: str) -> Optional[dict]:
        """Extract all actress profile data from profile page"""
        try:
            # Get name from page
            h1 = soup.find('h1')
            name_on_page = h1.get_text(strip=True) if h1 else actress_name
            
            # Get image
            image_url = ""
            img = soup.find('img', src=re.compile(r'/idolimages/'))
            if img:
                image_url = img.get('src', '')
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    image_url = 'https://www.javdatabase.com' + image_url
            
            # Extract all profile details from page text
            page_text = soup.get_text()
            
            # Age
            age = None
            age_match = re.search(r'Age[:\s]+(\d+)', page_text, re.I)
            if age_match:
                age = age_match.group(1)
            
            # Birthdate
            birthdate = None
            birth_match = re.search(r'(?:Birth|DOB|Born)[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})', page_text, re.I)
            if birth_match:
                birthdate = birth_match.group(1)
            
            # Measurements (B-W-H)
            measurements = None
            meas_match = re.search(r'(?:Measurements|BWH)[:\s]*(\d{2,3}[-\s]+\d{2,3}[-\s]+\d{2,3})', page_text, re.I)
            if meas_match:
                measurements = meas_match.group(1).replace(' ', '-')
            
            # Height
            height = None
            height_match = re.search(r'Height[:\s]+(\d+)\s*cm', page_text, re.I)
            if height_match:
                height = height_match.group(1) + ' cm'
            
            # Blood type
            blood_type = None
            blood_match = re.search(r'Blood\s*Type[:\s]+([ABO]+)', page_text, re.I)
            if blood_match:
                blood_type = blood_match.group(1)
            
            # Debut year
            debut = None
            debut_match = re.search(r'Debut[:\s]+(\d{4})', page_text, re.I)
            if debut_match:
                debut = debut_match.group(1)
            
            # Birthplace
            birthplace = None
            birthplace_match = re.search(r'(?:Birthplace|From)[:\s]+([^\n]+)', page_text, re.I)
            if birthplace_match:
                birthplace = birthplace_match.group(1).strip()
            
            # Cup size
            cup_size = None
            cup_match = re.search(r'Cup[:\s]+([A-Z]+)', page_text, re.I)
            if cup_match:
                cup_size = cup_match.group(1)
            
            # Japanese name from title or meta
            name_jp = actress_name
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                jp_match = re.search(r'([ぁ-んァ-ヶー一-龯]+)', title_text)
                if jp_match:
                    name_jp = jp_match.group(1)
            
            return {
                'name': name_on_page,
                'name_jp': name_jp,
                'image_url': image_url,
                'profile_url': profile_url,
                'age': age,
                'birthdate': birthdate,
                'measurements': measurements,
                'height': height,
                'blood_type': blood_type,
                'debut': debut,
                'birthplace': birthplace,
                'cup_size': cup_size
            }
        except Exception as e:
            print(f"         Error extracting profile: {e}")
            return None
    
    def scrape_actress_profile(self, actress_name: str, timeout: int = 5) -> Optional[ActressProfile]:
        """Get full actress profile with all details"""
        # Check cache
        if actress_name in self.actress_cache:
            return self.actress_cache[actress_name]
        
        try:
            from urllib.parse import quote
            url = f"https://www.javdatabase.com/idols/?q={quote(actress_name)}"
            
            # Set page load timeout
            self.driver.set_page_load_timeout(timeout)
            
            try:
                self.driver.get(url)
            except:
                # Timeout, skip
                self.actress_cache[actress_name] = None
                return None
            
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find first valid idol link
            links = soup.find_all('a', href=re.compile(r'/idols/[a-z0-9-]+/$'))
            valid = [l for l in links if '/idols/?_' not in l.get('href', '')]
            
            if not valid:
                self.actress_cache[actress_name] = None
                return None
            
            profile_url = valid[0].get('href')
            if not profile_url.startswith('http'):
                profile_url = 'https://www.javdatabase.com' + profile_url
            
            try:
                self.driver.get(profile_url)
            except:
                # Timeout, skip
                self.actress_cache[actress_name] = None
                return None
            
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Get name from page
            h1 = soup.find('h1')
            name_on_page = h1.get_text(strip=True) if h1 else actress_name
            
            # Get image
            image_url = ""
            img = soup.find('img', src=re.compile(r'/idolimages/'))
            if img:
                image_url = img.get('src', '')
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/'):
                    image_url = 'https://www.javdatabase.com' + image_url
            
            # Extract profile details
            age = None
            birthdate = None
            measurements = None
            height = None
            blood_type = None
            debut = None
            name_jp = actress_name
            
            # Look for profile info section
            # JAVDatabase uses various formats, try to extract what we can
            page_text = soup.get_text()
            
            # Try to extract age
            age_match = re.search(r'Age[:\s]+(\d+)', page_text, re.I)
            if age_match:
                age = age_match.group(1)
            
            # Try to extract birthdate
            birth_match = re.search(r'(?:Birth|DOB|Born)[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})', page_text, re.I)
            if birth_match:
                birthdate = birth_match.group(1)
            
            # Try to extract measurements (B-W-H format)
            meas_match = re.search(r'(?:Measurements|BWH)[:\s]*(\d{2,3}[-\s]+\d{2,3}[-\s]+\d{2,3})', page_text, re.I)
            if meas_match:
                measurements = meas_match.group(1).replace(' ', '-')
            
            # Try to extract height
            height_match = re.search(r'Height[:\s]+(\d+)\s*cm', page_text, re.I)
            if height_match:
                height = height_match.group(1) + ' cm'
            
            # Try to extract blood type
            blood_match = re.search(r'Blood\s*Type[:\s]+([ABO]+)', page_text, re.I)
            if blood_match:
                blood_type = blood_match.group(1)
            
            # Try to extract debut year
            debut_match = re.search(r'Debut[:\s]+(\d{4})', page_text, re.I)
            if debut_match:
                debut = debut_match.group(1)
            
            # Look for Japanese name in title or meta
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                # Japanese characters are usually in the title
                jp_match = re.search(r'([ぁ-んァ-ヶー一-龯]+)', title_text)
                if jp_match:
                    name_jp = jp_match.group(1)
            
            profile = ActressProfile(
                name=name_on_page,
                name_jp=name_jp,
                image_url=image_url,
                profile_url=profile_url,
                age=age,
                birthdate=birthdate,
                measurements=measurements,
                height=height,
                blood_type=blood_type,
                debut=debut
            )
            
            # Cache it
            self.actress_cache[actress_name] = profile
            return profile
            
        except Exception as e:
            # Cache negative result
            self.actress_cache[actress_name] = None
            return None
    
    def scrape_video_by_code(self, video_code: str) -> Optional[VideoData]:
        """
        Scrape video metadata using video code
        
        Args:
            video_code: Video code like "MIDA-486"
            
        Returns:
            VideoData object or None
        """
        try:
            # Build direct URL
            code_lower = video_code.lower()
            url = f"https://www.javdatabase.com/movies/{code_lower}/"
            
            # Set page load timeout
            self.driver.set_page_load_timeout(15)  # Increased from 10
            
            print(f"  Fetching: {url}")
            
            # Try with retry
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    self.driver.get(url)
                    break  # Success
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
            
            # Check for 404
            if '404' in title or 'not found' in title.lower():
                print(f"  XX Not found (404)")
                return None
            
            print(f"  >> Found: {title[:60]}...")
            
            # Extract Japanese title if available
            title_jp = title
            jp_title_elem = soup.find('h2', class_=re.compile(r'jp|japanese'))
            if jp_title_elem:
                title_jp = jp_title_elem.get_text(strip=True)
            
            # Get cover image
            cover_url = ""
            cover_img = soup.find('img', alt=re.compile(r'JAV Movie|Cover', re.I))
            if not cover_img:
                # Try any large image
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
            
            # Get actresses
            actresses = []
            actress_images = {}
            actress_profiles = {}
            
            # Find actress links (filter out navigation)
            actress_links = soup.find_all('a', href=re.compile(r'/idols/[a-z0-9-]+/$'))
            for link in actress_links:
                href = link.get('href', '')
                # Skip navigation links
                if '/idols/?_' in href or href == '/idols/':
                    continue
                
                name = link.get_text(strip=True)
                if name and len(name) > 2 and name not in actresses:
                    # Filter out common navigation text
                    if name in ['All Idols', 'Most Favorited', 'Teen', 'Twenties', 'MILF', 'Thirties']:
                        continue
                    
                    actresses.append(name)
                    print(f"     Actress: {name}")
                    
                    # Try to get image from link
                    img = link.find('img')
                    if img:
                        img_url = img.get('src', '')
                        if img_url:
                            if img_url.startswith('//'):
                                img_url = 'https:' + img_url
                            elif img_url.startswith('/'):
                                img_url = 'https://www.javdatabase.com' + img_url
                            actress_images[name] = img_url
                            print(f"       Image (inline): {img_url[:50]}...")
                    
                    # Get full profile by clicking the link
                    try:
                        # Get profile URL from the link
                        profile_href = link.get('href', '')
                        if profile_href:
                            if not profile_href.startswith('http'):
                                profile_href = 'https://www.javdatabase.com' + profile_href
                            
                            # Visit profile directly
                            print(f"       Visiting profile: {profile_href[:60]}...")
                            try:
                                self.driver.set_page_load_timeout(10)
                                self.driver.get(profile_href)
                                time.sleep(2)
                                
                                profile_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                                
                                # Extract all profile data
                                profile_data = self._extract_actress_profile(profile_soup, profile_href, name)
                                if profile_data:
                                    actress_profiles[name] = profile_data
                                    
                                    # Use profile image if we don't have one
                                    if name not in actress_images and profile_data.get('image_url'):
                                        actress_images[name] = profile_data['image_url']
                                    
                                    # Print profile details
                                    details = []
                                    if profile_data.get('age'):
                                        details.append(f"Age: {profile_data['age']}")
                                    if profile_data.get('height'):
                                        details.append(f"Height: {profile_data['height']}")
                                    if profile_data.get('measurements'):
                                        details.append(f"Measurements: {profile_data['measurements']}")
                                    if details:
                                        print(f"       Details: {', '.join(details)}")
                                else:
                                    print(f"       Profile: Could not extract data")
                                
                                # Go back to movie page
                                self.driver.back()
                                time.sleep(1)
                                
                            except Exception as e:
                                print(f"       Profile: Timeout/Error - {e}")
                                # Try to go back
                                try:
                                    self.driver.back()
                                    time.sleep(1)
                                except:
                                    pass
                        else:
                            print(f"       Profile: No link found")
                    except Exception as e:
                        print(f"       Profile: Error - {e}")
            
            # Get other metadata
            release_date = ""
            runtime = ""
            director = ""
            studio = ""
            label = ""
            series = ""
            categories = []
            description = ""
            rating = None
            rating_count = None
            screenshots = []
            
            # Extract from page text
            page_text = soup.get_text()
            
            # Release date
            release_match = re.search(r'Release[d]?\s*Date[:\s]+(\d{4}[-/]\d{1,2}[-/]\d{1,2})', page_text, re.I)
            if release_match:
                release_date = release_match.group(1)
            
            # Runtime/Duration
            runtime_match = re.search(r'(?:Runtime|Duration)[:\s]+(\d+)\s*min', page_text, re.I)
            if runtime_match:
                runtime = runtime_match.group(1) + ' min'
            
            # Director
            director_match = re.search(r'Director[:\s]+([^\n]+)', page_text, re.I)
            if director_match:
                director = director_match.group(1).strip()
            
            # Studio
            studio_match = re.search(r'Studio[:\s]+([^\n]+)', page_text, re.I)
            if studio_match:
                studio = studio_match.group(1).strip()
            
            # Label
            label_match = re.search(r'Label[:\s]+([^\n]+)', page_text, re.I)
            if label_match:
                label = label_match.group(1).strip()
            
            # Series
            series_match = re.search(r'Series[:\s]+([^\n]+)', page_text, re.I)
            if series_match:
                series = series_match.group(1).strip()
            
            # Categories/Genres - Extract from "Genre(s):" section
            # First try to find Genre(s): in text
            genre_match = re.search(r'Genre\(s\)[:\s]+([^\n]+)', page_text, re.I)
            if genre_match:
                genre_text = genre_match.group(1)
                # Split by common separators
                genres = re.split(r'[,;]|\s{2,}', genre_text)
                for genre in genres:
                    genre = genre.strip()
                    if genre and len(genre) > 1 and genre not in categories:
                        categories.append(genre)
            
            # Also look for category links
            category_links = soup.find_all('a', href=re.compile(r'/categories/'))
            for link in category_links:
                cat_name = link.get_text(strip=True)
                if cat_name and cat_name not in categories and len(cat_name) > 1:
                    categories.append(cat_name)
            
            # Description/Plot
            desc_elem = soup.find(['p', 'div'], class_=re.compile(r'description|plot|synopsis'))
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Rating
            rating_elem = soup.find(['span', 'div'], class_=re.compile(r'rating|score'))
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    try:
                        rating = float(rating_match.group(1))
                    except:
                        pass
            
            # Rating count
            rating_count_elem = soup.find(['span', 'div'], class_=re.compile(r'rating.*count|votes'))
            if rating_count_elem:
                count_text = rating_count_elem.get_text()
                count_match = re.search(r'(\d+)', count_text)
                if count_match:
                    try:
                        rating_count = int(count_match.group(1))
                    except:
                        pass
            
            # Screenshots - look for all images that might be screenshots
            # They're usually in the movie page, not in /screenshots/ path
            all_imgs = soup.find_all('img', src=True)
            for img in all_imgs:
                src = img.get('src', '')
                # Skip logos, covers, and actress images
                if any(x in src for x in ['logo', 'flag', 'icon', '/covers/', '/idolimages/']):
                    continue
                # Look for screenshot-like images
                if any(x in src for x in ['screenshot', 'gallery', 'sample', 'scene']):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.javdatabase.com' + src
                    if src not in screenshots:
                        screenshots.append(src)
            
            # If no screenshots found, try to find thumbnail images
            if not screenshots:
                thumb_imgs = soup.find_all('img', class_=re.compile(r'thumb|preview|sample'))
                for img in thumb_imgs:
                    src = img.get('src', '')
                    if src and '/covers/' not in src and '/idolimages/' not in src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = 'https://www.javdatabase.com' + src
                        if src not in screenshots:
                            screenshots.append(src)
            
            print(f"     Metadata: Release: {release_date}, Runtime: {runtime}")
            print(f"     Studio: {studio}, Categories: {len(categories)}")
            print(f"     Screenshots: {len(screenshots)}")
            
            from datetime import datetime
            return VideoData(
                code=video_code.upper(),
                title=title,
                title_jp=title_jp,
                cover_url=cover_url,
                screenshots=screenshots,
                actresses=actresses,
                actress_images=actress_images,
                actress_profiles=actress_profiles,
                release_date=release_date,
                runtime=runtime,
                director=director,
                studio=studio,
                label=label,
                series=series,
                categories=categories,
                description=description,
                rating=rating,
                rating_count=rating_count,
                javdb_url=url,
                scraped_at=datetime.now().isoformat(),
                found=True
            )
            
        except Exception as e:
            print(f"  !! Error: {e}")
            return None
    
    def scrape_from_jable_database(self, jable_db_path: str) -> List[VideoData]:
        """
        Scrape JAVDatabase metadata for all videos in Jable database
        
        Args:
            jable_db_path: Path to Jable videos_complete.json
            
        Returns:
            List of VideoData objects
        """
        self._init_driver()
        
        print("="*60)
        print("Scraping JAVDatabase by Video Codes")
        print("="*60)
        
        # Load Jable database
        print(f"\nLoading Jable database: {jable_db_path}")
        with open(jable_db_path, 'r', encoding='utf-8') as f:
            jable_videos = json.load(f)
        
        print(f"Found {len(jable_videos)} videos in Jable database\n")
        
        # Extract unique codes
        codes = []
        for video in jable_videos:
            code = video.get('code', '')
            if code and code not in codes:
                codes.append(code)
        
        print(f"Unique video codes: {len(codes)}\n")
        
        # Scrape each code
        all_videos = []
        for i, code in enumerate(codes, 1):
            print(f"[{i}/{len(codes)}] {code}")
            
            video_data = self.scrape_video_by_code(code)
            if video_data:
                all_videos.append(video_data)
            
            time.sleep(2)  # Be nice to server
        
        return all_videos


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape JAVDatabase using video codes')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--jable-db', default='../jable/database/videos_complete.json', 
                       help='Path to Jable database')
    parser.add_argument('--output', default='database/javdb_by_code.json', help='Output file')
    parser.add_argument('--limit', type=int, help='Limit number of videos (for testing)')
    parser.add_argument('--code', help='Scrape single video code')
    
    args = parser.parse_args()
    
    scraper = JAVDBCodeScraper(headless=args.headless)
    
    try:
        if args.code:
            # Scrape single code
            scraper._init_driver()  # Initialize driver
            print(f"\nScraping: {args.code}\n")
            video_data = scraper.scrape_video_by_code(args.code)
            if video_data:
                print(f"\n{json.dumps(asdict(video_data), indent=2, ensure_ascii=False)}")
        else:
            # Scrape from Jable database
            videos = scraper.scrape_from_jable_database(args.jable_db)
            
            if args.limit:
                videos = videos[:args.limit]
            
            print(f"\n{'='*60}")
            print("SCRAPING COMPLETE")
            print("="*60)
            print(f"Total videos scraped: {len(videos)}")
            print(f"With actresses: {sum(1 for v in videos if v.actresses)}")
            print(f"With actress images: {sum(1 for v in videos if v.actress_images)}")
            
            if videos:
                # Save to file
                print(f"\nSaving to: {args.output}")
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump([asdict(v) for v in videos], f, indent=2, ensure_ascii=False)
                print("Done!")
                
                # Show summary
                print("\nSample videos:")
                for v in videos[:5]:
                    print(f"  {v.code}: {len(v.actresses)} actresses, {len(v.actress_images)} images")
    
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
