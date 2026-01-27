"""
Improved JAVDatabase scraper for JavaGG integration
Extracts complete metadata from JAVDatabase.com
"""

import re
import time
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

from bs4 import BeautifulSoup
from seleniumbase import Driver


@dataclass
class VideoMetadata:
    """Complete video metadata from JAVDatabase"""
    code: str
    title: str
    title_jp: str
    release_date: str
    release_year: str
    runtime: str
    runtime_minutes: int
    director: str
    director_url: str
    studio: str
    studio_url: str
    label: str
    label_url: str
    series: str
    series_url: str
    content_id: str
    dvd_id: str
    cover_url: str
    cover_url_large: str
    screenshots: List[str]
    actresses: List[str]
    actress_details: List[Dict]
    categories: List[str]
    description: str
    rating: float
    rating_text: str
    votes: int
    popularity_rank: int
    views: int
    favorites: int
    scraped_at: str
    javdb_url: str


def scrape_actress_profile(actress_url: str, driver) -> Dict:
    """
    Scrape detailed actress information from profile page
    
    Args:
        actress_url: URL to actress profile
        driver: Selenium driver instance
    
    Returns:
        Dict with actress details
    """
    try:
        print(f"       Fetching actress profile: {actress_url}")
        driver.get(actress_url)
        time.sleep(1.5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page_text = soup.get_text()
        
        details = {}
        
        # Extract Japanese name (multiple patterns)
        jp_name_match = re.search(r'(?:Japanese Name|Name in Japanese|Japanese):?\s*([^\n]{2,30})', page_text, re.I)
        if jp_name_match:
            jp_name = jp_name_match.group(1).strip()
            # Filter out non-Japanese characters patterns
            if any('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FFF' for c in jp_name):
                details['name_japanese'] = jp_name
        
        # Try alternative: look for Japanese characters near the English name
        if 'name_japanese' not in details:
            # Find h1 or title with actress name
            title_elem = soup.find('h1')
            if title_elem:
                title_text = title_elem.get_text()
                # Extract Japanese characters
                jp_chars = ''.join([c for c in title_text if '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FFF' or c in '・'])
                if jp_chars and len(jp_chars) >= 2:
                    details['name_japanese'] = jp_chars.strip()
        
        # Extract birthdate (multiple formats) - FULL DATE
        birthdate_match = re.search(r'(?:Birth ?date|Born|Birthday|DOB):?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})', page_text, re.I)
        if birthdate_match:
            details['birthdate'] = birthdate_match.group(1).replace('/', '-')
        
        # Extract age
        age_match = re.search(r'Age:?\s*(\d+)', page_text)
        if age_match:
            details['age'] = int(age_match.group(1))
        
        # Extract debut date (FULL DATE with year-month-day)
        debut_full_match = re.search(r'Debut:?\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})', page_text, re.I)
        if debut_full_match:
            details['debut_date'] = debut_full_match.group(1).replace('/', '-')
        elif not debut_full_match:
            # Fallback to year only
            debut_match = re.search(r'Debut:?\s*(\d{4})', page_text)
            if debut_match:
                details['debut_year'] = debut_match.group(1)
        
        # Extract debut age
        debut_age_match = re.search(r'Debut Age:?\s*(\d+)', page_text, re.I)
        if debut_age_match:
            details['debut_age'] = int(debut_age_match.group(1))
        
        # Extract height
        height_match = re.search(r'Height:?\s*(\d+)\s*cm', page_text, re.I)
        if height_match:
            details['height'] = height_match.group(1) + ' cm'
        
        # Extract weight
        weight_match = re.search(r'Weight:?\s*(\d+)\s*kg', page_text, re.I)
        if weight_match:
            details['weight'] = weight_match.group(1) + ' kg'
        
        # Extract shoe size
        shoe_match = re.search(r'Shoe Size:?\s*(\d+(?:\.\d+)?)\s*cm', page_text, re.I)
        if shoe_match:
            details['shoe_size'] = shoe_match.group(1) + ' cm'
        
        # Extract measurements (bust-waist-hips)
        measurements_match = re.search(r'(?:Measurements|BWH|Body):?\s*(\d+-\d+-\d+)', page_text, re.I)
        if measurements_match:
            details['measurements'] = measurements_match.group(1)
        
        # Extract individual measurements if not found together
        if 'measurements' not in details:
            bust_match = re.search(r'Bust:?\s*(\d+)', page_text, re.I)
            waist_match = re.search(r'Waist:?\s*(\d+)', page_text, re.I)
            hips_match = re.search(r'Hips:?\s*(\d+)', page_text, re.I)
            if bust_match and waist_match and hips_match:
                details['measurements'] = f"{bust_match.group(1)}-{waist_match.group(1)}-{hips_match.group(1)}"
        
        # Extract cup size
        cup_match = re.search(r'Cup:?\s*([A-Z])', page_text, re.I)
        if cup_match:
            details['cup_size'] = cup_match.group(1).upper()
        
        # Extract blood type
        blood_match = re.search(r'Blood(?: Type)?:?\s*([ABO]B?|AB)', page_text, re.I)
        if blood_match:
            details['blood_type'] = blood_match.group(1).upper()
        
        # Extract birthplace/hometown
        birthplace_match = re.search(r'(?:Birth ?place|Hometown|From):?\s*([^\n,]{3,40})', page_text, re.I)
        if birthplace_match:
            place = birthplace_match.group(1).strip()
            # Filter out non-location text
            if len(place) < 40 and not any(x in place.lower() for x in ['height', 'age', 'cup', 'blood', 'weight', 'debut', 'bust', 'waist', 'shoe']):
                details['birthplace'] = place
        
        # Extract zodiac sign
        zodiac_match = re.search(r'(?:Zodiac|Star Sign|Sign):?\s*([A-Za-z]+)', page_text, re.I)
        if zodiac_match:
            zodiac = zodiac_match.group(1).strip()
            if zodiac.lower() in ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo', 'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces']:
                details['zodiac_sign'] = zodiac.capitalize()
        
        # Extract hair length
        hair_length_match = re.search(r'Hair Length(?:\(s\))?:?\s*([^\n]{3,50})', page_text, re.I)
        if hair_length_match:
            details['hair_length'] = hair_length_match.group(1).strip()
        
        # Extract hair color
        hair_color_match = re.search(r'Hair Color(?:\(s\))?:?\s*([^\n]{3,50})', page_text, re.I)
        if hair_color_match:
            details['hair_color'] = hair_color_match.group(1).strip()
        
        # Extract hobbies
        hobbies_match = re.search(r'Hobbies:?\s*([^\n]{5,100})', page_text, re.I)
        if hobbies_match:
            hobbies = hobbies_match.group(1).strip()
            if len(hobbies) < 100:
                details['hobbies'] = hobbies
        
        # Extract skills/specialties
        skills_match = re.search(r'(?:Skills|Specialties):?\s*([^\n]{5,100})', page_text, re.I)
        if skills_match:
            skills = skills_match.group(1).strip()
            if len(skills) < 100:
                details['skills'] = skills
        
        # Extract profile images (both thumb and full size)
        profile_img = soup.find('img', class_=re.compile(r'idol|actress|profile', re.I))
        if not profile_img:
            profile_img = soup.find('img', alt=re.compile(r'idol|actress', re.I))
        
        if profile_img:
            img_src = profile_img.get('src', '') or profile_img.get('data-src', '')
            if img_src:
                # Get full size image
                img_src_full = img_src.replace('/thumb/', '/full/').replace('_thumb', '')
                if img_src_full.startswith('//'):
                    details['image_url_full'] = 'https:' + img_src_full
                elif img_src_full.startswith('/'):
                    details['image_url_full'] = 'https://www.javdatabase.com' + img_src_full
                else:
                    details['image_url_full'] = img_src_full
        
        # Extract social media links
        social_links = {}
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'twitter.com' in href or 'x.com' in href:
                if 'JAVDatabase' not in href:  # Skip JAVDatabase's own twitter
                    social_links['twitter'] = href
            elif 'instagram.com' in href:
                social_links['instagram'] = href
            elif 'tiktok.com' in href:
                social_links['tiktok'] = href
        
        if social_links:
            details['social_media'] = social_links
        
        # Extract total movies count
        movies_match = re.search(r'(\d+)\s*(?:movies|titles|videos)', page_text, re.I)
        if movies_match:
            details['total_movies'] = int(movies_match.group(1))
        
        return details
        
    except Exception as e:
        print(f"       ⚠️ Error fetching actress profile: {str(e)[:50]}")
        return {}


def scrape_javdb_metadata(video_code: str, headless: bool = True, fetch_actress_details: bool = True) -> Optional[VideoMetadata]:
    """
    Scrape video metadata from JAVDatabase
    
    Args:
        video_code: Video code (e.g., "SONE-572")
        headless: Run browser in headless mode
    
    Returns:
        VideoMetadata object or None
    """
    driver = None
    try:
        print(f"  🌐 Initializing browser...")
        driver = Driver(uc=True, headless=headless, incognito=True)
        time.sleep(2)
        print(f"  ✅ Browser ready")
        
        # Convert code to URL format
        code_lower = video_code.lower().replace('_', '-')
        direct_url = f"https://www.javdatabase.com/movies/{code_lower}/"
        
        print(f"  📄 Loading: {direct_url}")
        driver.get(direct_url)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Check if page exists
        title_elem = soup.find('h1')
        if not title_elem or '404' in title_elem.get_text() or 'not found' in title_elem.get_text().lower():
            print(f"  ❌ Video not found (404)")
            return None
        
        title = title_elem.get_text(strip=True)
        
        # Verify code is in title
        if video_code.upper() not in title.upper():
            print(f"  ❌ Code mismatch in title")
            return None
        
        print(f"  ✅ Found: {title[:60]}...")
        
        # Find main content
        main = soup.find('main')
        if not main:
            main = soup
        
        page_text = main.get_text()
        
        # Extract release date and year
        release_date = ""
        release_year = ""
        date_match = re.search(r'Release Date:?\s*(\d{4})-(\d{2})-(\d{2})', page_text)
        if date_match:
            release_date = date_match.group(0).split(':')[-1].strip()
            release_year = date_match.group(1)
            print(f"     - Release: {release_date}")
        
        # Extract runtime and convert to minutes
        runtime = ""
        runtime_minutes = 0
        runtime_match = re.search(r'Runtime:?\s*(\d+)\s*min', page_text, re.I)
        if runtime_match:
            runtime_minutes = int(runtime_match.group(1))
            runtime = str(runtime_minutes) + ' min'
            print(f"     - Runtime: {runtime}")
        
        # Extract views/popularity
        views = 0
        views_match = re.search(r'(\d+)\s*views?', page_text, re.I)
        if views_match:
            views = int(views_match.group(1))
            print(f"     - Views: {views}")
        
        # Extract favorites
        favorites = 0
        fav_match = re.search(r'(\d+)\s*favorites?', page_text, re.I)
        if fav_match:
            favorites = int(fav_match.group(1))
            print(f"     - Favorites: {favorites}")
        
        # Extract popularity rank
        popularity_rank = 0
        rank_match = re.search(r'Rank:?\s*#?(\d+)', page_text, re.I)
        if rank_match:
            popularity_rank = int(rank_match.group(1))
            print(f"     - Rank: #{popularity_rank}")
        
        # Extract director with URL
        director = ""
        director_url = ""
        director_link = main.find('a', href=re.compile(r'/directors/'))
        if director_link:
            director = director_link.text.strip()
            director_url = director_link.get('href', '')
            if director_url and not director_url.startswith('http'):
                if director_url.startswith('/'):
                    director_url = 'https://www.javdatabase.com' + director_url
            if director and len(director) < 50:
                print(f"     - Director: {director}")
        
        # Extract studio with URL
        studio = ""
        studio_url = ""
        studio_link = main.find('a', href=re.compile(r'/studios/'))
        if studio_link:
            studio = studio_link.text.strip()
            studio_url = studio_link.get('href', '')
            if studio_url and not studio_url.startswith('http'):
                if studio_url.startswith('/'):
                    studio_url = 'https://www.javdatabase.com' + studio_url
            if studio and len(studio) < 50:
                print(f"     - Studio: {studio}")
        
        # Extract label with URL
        label = ""
        label_url = ""
        label_match = re.search(r'Label:?\s*([^\n]+)', page_text)
        if label_match:
            label = label_match.group(1).strip()
            # Try to find label link
            label_link = main.find('a', text=re.compile(re.escape(label), re.I))
            if label_link:
                label_url = label_link.get('href', '')
                if label_url and not label_url.startswith('http'):
                    if label_url.startswith('/'):
                        label_url = 'https://www.javdatabase.com' + label_url
            if label and len(label) < 50:
                print(f"     - Label: {label}")
        
        # Extract series with URL (filter out DVD ID patterns)
        series = ""
        series_url = ""
        series_match = re.search(r'Series:?\s*([^\n]+)', page_text)
        if series_match:
            series = series_match.group(1).strip()
            # Filter out "DVD ID: CODE" pattern
            if series and 'DVD ID:' not in series and len(series) < 50:
                print(f"     - Series: {series}")
            else:
                series = ""  # Clear if it's just DVD ID
        
        # Extract Content ID
        content_id = ""
        content_id_match = re.search(r'Content ID:?\s*([^\n]+)', page_text)
        if content_id_match:
            content_id = content_id_match.group(1).strip()
            if content_id and len(content_id) < 50:
                print(f"     - Content ID: {content_id}")
        
        # Extract DVD ID
        dvd_id = ""
        dvd_id_match = re.search(r'DVD ID:?\s*([A-Z]+-\d+)', page_text, re.I)
        if dvd_id_match:
            dvd_id = dvd_id_match.group(1).strip().upper()
            print(f"     - DVD ID: {dvd_id}")
        
        # Extract rating and votes
        rating = 0.0
        rating_text = ""
        votes = 0
        
        # Extract votes
        votes_match = re.search(r'(\d+)\s*votes?,\s*average:\s*(\d+\.?\d*)\s*out of\s*(\d+)', page_text)
        if votes_match:
            votes = int(votes_match.group(1))
            rating = float(votes_match.group(2))
            max_rating = votes_match.group(3)
            rating_text = f"{rating}/{max_rating}"
            print(f"     - Rating: {rating_text} ({votes} votes)")
        else:
            # Try without votes
            rating_match = re.search(r'average:\s*(\d+\.?\d*)\s*out of\s*(\d+)', page_text)
            if rating_match:
                rating = float(rating_match.group(1))
                max_rating = rating_match.group(2)
                rating_text = f"{rating}/{max_rating}"
                print(f"     - Rating: {rating_text}")
        
        # Extract actresses with detailed information
        actresses = []
        actress_details = []
        
        # Also get direct links
        actress_links = main.find_all('a', href=re.compile(r'/idols/[a-z0-9-]+/$'))
        
        # Filter and deduplicate
        seen_actresses = set()
        exclude_names = {'all idols', 'most favorited', 'teen', 'twenties', 'milf', 'mature', 'big tits', 'big ass', 'loli'}
        
        for link in actress_links:
            name = link.text.strip()
            name_lower = name.lower()
            
            if name and name_lower not in exclude_names and name_lower not in seen_actresses:
                actresses.append(name)
                seen_actresses.add(name_lower)
                
                # Get actress URL
                actress_url = link.get('href', '')
                if actress_url and not actress_url.startswith('http'):
                    if actress_url.startswith('//'):
                        actress_url = 'https:' + actress_url
                    elif actress_url.startswith('/'):
                        actress_url = 'https://www.javdatabase.com' + actress_url
                
                # Try to find actress image near the link
                actress_image_url = ""
                
                # Method 1: Check parent container for image
                parent = link.find_parent()
                if parent:
                    actress_img = parent.find('img')
                    if actress_img:
                        img_src = actress_img.get('src', '') or actress_img.get('data-src', '')
                        if img_src and 'idol' in img_src.lower():
                            if img_src.startswith('//'):
                                actress_image_url = 'https:' + img_src
                            elif img_src.startswith('/'):
                                actress_image_url = 'https://www.javdatabase.com' + img_src
                            else:
                                actress_image_url = img_src
                
                # Method 2: Look for image with actress name in alt
                if not actress_image_url:
                    for img in soup.find_all('img', alt=re.compile(re.escape(name), re.I)):
                        img_src = img.get('src', '') or img.get('data-src', '')
                        if img_src:
                            if img_src.startswith('//'):
                                actress_image_url = 'https:' + img_src
                            elif img_src.startswith('/'):
                                actress_image_url = 'https://www.javdatabase.com' + img_src
                            else:
                                actress_image_url = img_src
                            break
                
                # Base actress details
                actress_info = {
                    'name': name,
                    'image_url': actress_image_url,
                    'profile_url': actress_url
                }
                
                # Fetch detailed profile information if enabled
                if fetch_actress_details and actress_url:
                    profile_details = scrape_actress_profile(actress_url, driver)
                    actress_info.update(profile_details)
                
                actress_details.append(actress_info)
        
        if actresses:
            print(f"     - Actresses: {', '.join(actresses)}")
        
        # Extract cover URL (both regular and large)
        cover_url = ""
        cover_url_large = ""
        cover_img = soup.find('img', alt=re.compile(video_code, re.IGNORECASE))
        if cover_img:
            cover_url = cover_img.get('src', '')
            if cover_url.startswith('//'):
                cover_url = 'https:' + cover_url
            elif cover_url.startswith('/'):
                cover_url = 'https://www.javdatabase.com' + cover_url
            
            # Get large version
            if '/thumb/' in cover_url:
                cover_url_large = cover_url.replace('/thumb/', '/full/')
            elif 'ps.webp' in cover_url:
                cover_url_large = cover_url.replace('ps.webp', 'pl.webp')
            else:
                cover_url_large = cover_url
            
            print(f"     - Cover: Yes")
        
        # Extract screenshots
        screenshots = []
        screenshot_imgs = soup.find_all('img', alt=re.compile(r'Screenshot', re.I))
        
        for img in screenshot_imgs:
            src = img.get('src', '') or img.get('data-src', '')
            if src:
                # Normalize URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/') and not src.startswith('//'):
                    src = 'https://www.javdatabase.com' + src
                
                # Only add if it's a valid screenshot URL
                if 'screenshot' in src.lower() or 'dmm.co.jp' in src or 'sample' in src.lower():
                    # Convert DMM URLs to highest quality (jp format - full size uncompressed)
                    if 'pics.dmm.co.jp/digital/video/' in src and '.jpg' in src:
                        # Change from: https://pics.dmm.co.jp/digital/video/ipx00001/ipx00001-1.jpg
                        # To: https://pics.dmm.co.jp/digital/video/ipx00001/ipx00001jp-1.jpg
                        # Insert 'jp' before the dash: ipx00001-1.jpg -> ipx00001jp-1.jpg
                        src = re.sub(r'([a-z0-9]+)-(\d+)\.jpg', r'\1jp-\2.jpg', src)
                    screenshots.append(src)
        
        if screenshots:
            print(f"     - Screenshots: {len(screenshots)}")
        
        # Extract categories/genres
        categories = []
        genre_links = main.find_all('a', href=re.compile(r'/genres/'))
        for link in genre_links:
            genre = link.text.strip()
            if genre and genre.lower() != 'genres':
                categories.append(genre)
        
        if categories:
            print(f"     - Genres: {len(categories)}")
        
        # Extract description (try multiple methods)
        description = ""
        
        # Method 1: Look for description div
        desc_elem = soup.find('div', class_=re.compile(r'description|synopsis', re.I))
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        
        # Method 2: Look for description in meta tags
        if not description:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
        
        # Method 3: Look for description in structured data
        if not description:
            desc_match = re.search(r'Description:?\s*([^\n]{20,})', page_text)
            if desc_match:
                description = desc_match.group(1).strip()
        
        return VideoMetadata(
            code=video_code.upper(),
            title=title,
            title_jp=title,  # JAVDatabase doesn't separate JP title
            release_date=release_date,
            release_year=release_year,
            runtime=runtime,
            runtime_minutes=runtime_minutes,
            director=director,
            director_url=director_url,
            studio=studio,
            studio_url=studio_url,
            label=label,
            label_url=label_url,
            series=series,
            series_url=series_url,
            content_id=content_id,
            dvd_id=dvd_id,
            cover_url=cover_url,
            cover_url_large=cover_url_large,
            screenshots=screenshots,
            actresses=actresses,
            actress_details=actress_details,
            categories=categories,
            description=description,
            rating=rating,
            rating_text=rating_text,
            votes=votes,
            popularity_rank=popularity_rank,
            views=views,
            favorites=favorites,
            scraped_at=datetime.now().isoformat(),
            javdb_url=direct_url
        )
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


# Test
if __name__ == "__main__":
    import json
    
    metadata = scrape_javdb_metadata("SONE-572", headless=False)
    
    if metadata:
        print("\n" + "="*70)
        print("EXTRACTED METADATA")
        print("="*70)
        print(json.dumps(asdict(metadata), indent=2, ensure_ascii=False))
    else:
        print("\n❌ Failed to scrape")
