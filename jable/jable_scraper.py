"""
Jable.tv Complete Scraper
Scrapes everything from Jable.tv: videos, metadata, M3U8 URLs
Stores in JSON database
"""

import re
import time
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

from bs4 import BeautifulSoup
from seleniumbase import Driver


def parse_relative_time(relative_time_str: str) -> str:
    """
    Convert relative time string to absolute ISO timestamp
    
    Args:
        relative_time_str: String like "1 hour ago", "2 days ago", "3 weeks ago"
        
    Returns:
        ISO format timestamp string
    """
    if not relative_time_str:
        return datetime.now().isoformat()
    
    try:
        # Parse the relative time
        match = re.match(r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago', relative_time_str.lower())
        
        if not match:
            # If can't parse, return current time
            return datetime.now().isoformat()
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        # Calculate the absolute time
        now = datetime.now()
        
        if unit == 'second':
            upload_time = now - timedelta(seconds=amount)
        elif unit == 'minute':
            upload_time = now - timedelta(minutes=amount)
        elif unit == 'hour':
            upload_time = now - timedelta(hours=amount)
        elif unit == 'day':
            upload_time = now - timedelta(days=amount)
        elif unit == 'week':
            upload_time = now - timedelta(weeks=amount)
        elif unit == 'month':
            upload_time = now - timedelta(days=amount * 30)  # Approximate
        elif unit == 'year':
            upload_time = now - timedelta(days=amount * 365)  # Approximate
        else:
            upload_time = now
        
        return upload_time.isoformat()
        
    except Exception as e:
        print(f"  ⚠️ Could not parse relative time '{relative_time_str}': {e}")
        return datetime.now().isoformat()


@dataclass
class VideoData:
    """Complete video data from Jable.tv"""
    code: str
    title: str
    m3u8_url: str
    thumbnail_url: str
    duration: str
    views: str
    likes: str
    release_date: str
    upload_time: str  # Absolute ISO timestamp
    upload_time_relative: str  # Original relative time like "1 hour ago"
    hd_quality: bool
    categories: List[str]
    models: List[str]
    tags: List[str]
    preview_images: List[str]
    scraped_at: str
    source_url: str


class JableScraper:
    """Complete scraper for Jable.tv"""
    
    BASE_URL = "https://jable.tv"
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        
    def _init_driver(self):
        """Initialize browser with error handling and fallback"""
        if self.driver is None:
            print("Initializing browser...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Try headless mode first if requested
                    if self.headless:
                        try:
                            self.driver = Driver(
                                uc=True, 
                                headless=True,
                                headless2=True,
                                incognito=True,
                                page_load_strategy='eager'  # Don't wait for all resources
                            )
                            time.sleep(2)
                            # Set reasonable timeouts
                            self.driver.set_page_load_timeout(30)  # Shorter timeout
                            self.driver.set_script_timeout(15)
                            print("  ✅ Browser initialized in headless mode (eager loading)")
                            return
                        except Exception as e:
                            print(f"  ⚠️ Headless mode failed: {e}")
                            if attempt == max_retries - 1:
                                # Last attempt: try non-headless as fallback
                                print("  🔄 Falling back to non-headless mode...")
                                self.driver = Driver(
                                    uc=True, 
                                    headless=False,
                                    page_load_strategy='eager'
                                )
                                time.sleep(2)
                                self.driver.set_page_load_timeout(30)
                                self.driver.set_script_timeout(15)
                                print("  ✅ Browser initialized in non-headless mode (eager loading)")
                                return
                    else:
                        self.driver = Driver(
                            uc=True, 
                            headless=False,
                            page_load_strategy='eager'
                        )
                        time.sleep(2)
                        self.driver.set_page_load_timeout(30)
                        self.driver.set_script_timeout(15)
                        print("  ✅ Browser initialized (eager loading)")
                        return
                except Exception as e:
                    print(f"  ⚠️ Browser init attempt {attempt+1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(5)
                    else:
                        raise Exception(f"Failed to initialize browser after {max_retries} attempts")
    
    def _ensure_driver(self):
        """Ensure driver is alive and restart if needed"""
        if self.driver is None:
            self._init_driver()
        else:
            # Check if driver is still alive
            try:
                _ = self.driver.current_url
            except Exception as e:
                print(f"  ⚠️ Browser appears dead, restarting: {e}")
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                self._init_driver()
    
    def close(self):
        """Close browser safely"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"  ⚠️ Error closing browser: {e}")
                try:
                    # Force kill if quit fails
                    self.driver.close()
                except:
                    pass
            finally:
                self.driver = None
    
    def get_video_links_from_page(self, page_url: str) -> List[str]:
        """
        Get all video links from a page (homepage, category, etc.)
        
        Args:
            page_url: URL of the page to scrape
            
        Returns:
            List of video URLs
        """
        self._ensure_driver()
        
        # Add English language parameter
        if '?' in page_url:
            page_url += '&lang=en'
        else:
            page_url += '?lang=en'
        
        print(f"📄 Loading page: {page_url}")
        
        try:
            # Use a more aggressive approach: load page and immediately stop it
            # This prevents hanging on slow-loading resources
            print(f"  ⏳ Starting page load...")
            
            # Start loading the page in a separate thread-like manner
            # by using execute_async_script
            try:
                # Navigate to page
                self.driver.get(page_url)
                print(f"  ✓ Page navigation started")
            except Exception as e:
                # If get() times out or fails, that's okay - we'll try to work with what loaded
                print(f"  ⚠️ Page load interrupted (this is normal): {str(e)[:80]}")
            
            # Give it more time to load content (increased from 3 to 5 seconds)
            time.sleep(5)
            
            # Force stop any ongoing page loads
            try:
                self.driver.execute_script("window.stop();")
                print(f"  ✓ Stopped page load to prevent hanging")
            except:
                pass
            
            # Wait for body to appear
            print(f"  ⏳ Waiting for page body...")
            start_time = time.time()
            timeout = 10
            body_found = False
            while time.time() - start_time < timeout:
                try:
                    if self.driver.find_element("tag name", "body"):
                        body_found = True
                        print(f"  ✓ Page body loaded")
                        break
                except:
                    pass
                time.sleep(0.5)
            
            if not body_found:
                print(f"  ❌ Page body not found, cannot proceed")
                return []
            
            # Wait for JavaScript to render content
            print(f"  ⏳ Waiting for content to render...")
            time.sleep(5)
            
            # Check for video links
            try:
                video_elements = self.driver.find_elements("css selector", "a[href*='/videos/']")
                print(f"  🔍 Found {len(video_elements)} potential video links")
                
                if len(video_elements) == 0:
                    print(f"  ⏳ No links yet, waiting 5 more seconds...")
                    time.sleep(5)
                    video_elements = self.driver.find_elements("css selector", "a[href*='/videos/']")
                    print(f"  🔍 Now found {len(video_elements)} potential video links")
            except Exception as e:
                print(f"  ⚠️ Error checking for video links: {e}")
            
            # Scroll to trigger lazy loading (increased wait time)
            try:
                print(f"  📜 Scrolling to load lazy content...")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Increased from 2 to 3 seconds
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Increased from 2 to 3 seconds
            except Exception as e:
                print(f"  ⚠️ Error scrolling: {e}")
            
            print(f"  ✓ Page ready for parsing")
            
        except Exception as e:
            print(f"  ❌ Critical error loading page: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Debug: Check if page has content
        print(f"  🔍 Page source length: {len(self.driver.page_source)} characters")
        
        # Debug: Check for common Jable elements
        video_containers = soup.find_all('div', class_='video-img-box')
        print(f"  🔍 Found {len(video_containers)} video containers")
        
        # If no videos found, restart browser and retry once
        if len(video_containers) == 0:
            print(f"  ⚠️ No video containers found - restarting browser for fresh session...")
            try:
                self.close()
                time.sleep(5)
                self._init_driver()
                print(f"  ✅ Browser restarted")
                print(f"  🔄 Retrying page load...")
                
                # Retry the page load
                try:
                    self.driver.get(page_url)
                    time.sleep(5)
                    self.driver.execute_script("window.stop();")
                    time.sleep(5)
                    
                    # Scroll again
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    # Re-parse
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    video_containers = soup.find_all('div', class_='video-img-box')
                    print(f"  🔍 After restart: Found {len(video_containers)} video containers")
                except Exception as retry_error:
                    print(f"  ⚠️ Retry after restart failed: {retry_error}")
            except Exception as restart_error:
                print(f"  ❌ Browser restart failed: {restart_error}")
        
        video_links = []
        
        # Find all video links
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Video URLs have format: /videos/code/ or https://jable.tv/videos/code/
            if '/videos/' in href:
                # Normalize URL
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = f"{self.BASE_URL}{href}"
                else:
                    full_url = f"{self.BASE_URL}/{href}"
                
                # Filter: must have a code after /videos/
                # Valid: https://jable.tv/videos/fpre-216/
                # Invalid: https://jable.tv/videos/ or https://jable.tv/videos/2/
                if (full_url not in video_links and 
                    not full_url.endswith('/videos/') and
                    '/videos/' in full_url):
                    # Extract code part
                    code_match = re.search(r'/videos/([^/]+)/?$', full_url)
                    if code_match:
                        code = code_match.group(1)
                        # Code should contain letters and numbers (not just numbers for pagination)
                        if re.search(r'[a-zA-Z]', code):
                            video_links.append(full_url)
                        if re.search(r'[a-zA-Z]', code):
                            video_links.append(full_url)
        
        print(f"✅ Found {len(video_links)} video links")
        return video_links
    
    def scrape_video(self, video_url: str) -> Optional[VideoData]:
        """
        Scrape complete data from a single video page
        
        Args:
            video_url: URL of the video page
            
        Returns:
            VideoData object or None if failed
        """
        # Validate URL
        if not video_url or not isinstance(video_url, str):
            print(f"  ❌ Invalid video URL: {video_url}")
            return None
        
        if not video_url.startswith('http'):
            print(f"  ❌ URL must start with http/https: {video_url}")
            return None
        
        try:
            self._ensure_driver()
            
            # Extract code from URL - more robust parsing
            code_match = re.search(r'/videos/([^/\?#]+)', video_url)
            if not code_match:
                print(f"  ❌ Could not extract code from URL: {video_url}")
                return None
            
            code = code_match.group(1).upper()
            
            # Validate code contains letters (not just pagination numbers)
            if not re.search(r'[a-zA-Z]', code):
                print(f"  ❌ Invalid code (no letters): {code}")
                return None
            
            print(f"  📹 Scraping: {code}")
            
            # Load page with English language
            video_url_en = video_url.split('?')[0].split('#')[0]  # Remove existing params
            video_url_en += '?lang=en'
            self.driver.get(video_url_en)
            time.sleep(5)
            
            # Click the video player to trigger M3U8 loading
            try:
                # Try to find and click the play button or video element
                play_button = self.driver.find_element('css selector', '.plyr__control--overlaid')
                if play_button:
                    play_button.click()
                    print(f"  ▶️ Clicked play button")
                    time.sleep(5)  # Wait longer for full video M3U8 to load (not just preview)
            except:
                try:
                    # Alternative: click the video element directly
                    video_elem = self.driver.find_element('tag name', 'video')
                    if video_elem:
                        video_elem.click()
                        print(f"  ▶️ Clicked video element")
                        time.sleep(5)  # Wait longer
                except:
                    print(f"  ⚠️ Could not click video player, trying to extract M3U8 anyway")
            
            # Wait additional time for full video URL to load (preview loads first, then full video)
            print(f"  ⏳ Waiting for full video URL to load...")
            time.sleep(8)  # Total wait: 5 + 8 = 13 seconds after click
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Check if page exists
            title_tag = soup.find('title')
            if title_tag and ('404' in title_tag.get_text() or 'not found' in title_tag.get_text().lower()):
                print(f"  ⚠️ Video not found (404)")
                return None
            
            # Extract title
            title = ""
            h4_title = soup.find('h4', class_='title')
            if h4_title:
                title = h4_title.get_text(strip=True)
            if not title:
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    title = og_title.get('content', '')
            
            # If still no title, use code as fallback
            if not title:
                title = code
                print(f"  ⚠️ No title found, using code as title")
            
            # Extract M3U8 URL - only accept full video, reject previews
            m3u8_url = ""
            m3u8_pattern = r'(https?://[^"\'<>\s]+\.m3u8[^"\'<>\s]*)'
            m3u8_matches = re.findall(m3u8_pattern, page_source)
            if m3u8_matches:
                print(f"  Found {len(m3u8_matches)} m3u8 URLs")
                
                # Filter out preview/trailer URLs completely
                full_video_urls = []
                
                for match in m3u8_matches:
                    match_lower = match.lower()
                    
                    # Skip cloudflare and obviously bad URLs
                    if 'cloudflare' in match_lower:
                        continue
                    
                    # REJECT preview/trailer URLs completely
                    if any(keyword in match_lower for keyword in ['preview', 'trailer', 'sample', 'promo']):
                        print(f"  ⚠️ Skipping preview URL: {match[:80]}...")
                        continue
                    
                    # Accept URLs that look like full videos
                    if any(keyword in match_lower for keyword in ['master', 'playlist', 'index', 'video']):
                        full_video_urls.append(match)
                        print(f"  ✓ Found full video URL (length: {len(match)})")
                    else:
                        # Accept other URLs that aren't explicitly previews
                        full_video_urls.append(match)
                        print(f"  ✓ Found video URL (length: {len(match)})")
                
                # Sort by URL length (longer URLs are usually full videos with more parameters)
                full_video_urls.sort(key=len, reverse=True)
                
                # Only use full video URLs
                if full_video_urls:
                    m3u8_url = full_video_urls[0]
                    print(f"  ✅ Selected longest URL ({len(m3u8_url)} chars) as full video")
                else:
                    print(f"  ❌ No full video URL found (only previews/trailers)")
                    return None
            
            # Validate M3U8 URL
            if not m3u8_url:
                print(f"  ⚠️ No M3U8 URL found")
                return None
            
            if not m3u8_url.startswith('http'):
                print(f"  ⚠️ Invalid M3U8 URL format: {m3u8_url[:50]}")
                return None
            
            # Increased limit from 2000 to 3000
            if len(m3u8_url) > 3000:
                print(f"  ⚠️ M3U8 URL suspiciously long: {len(m3u8_url)} chars")
                return None
            
            # Extract thumbnail
            thumbnail_url = ""
            og_image = soup.find('meta', property='og:image')
            if og_image:
                thumbnail_url = og_image.get('content', '')
            
            # Extract duration from player (after clicking play)
            duration = ""
            try:
                # Try to get duration from the seek slider's aria-valuetext
                seek_input = self.driver.find_element('css selector', 'input[data-plyr="seek"]')
                if seek_input:
                    aria_text = seek_input.get_attribute('aria-valuetext')
                    if aria_text and ' of ' in aria_text:
                        # Format: "00:04 of 2:03:53"
                        duration = aria_text.split(' of ')[-1].strip()
            except:
                pass
            
            # Fallback: search in page source
            if not duration:
                duration_match = re.search(r'aria-valuetext="[^"]*of\s+([0-9:]+)"', page_source)
                if duration_match:
                    duration = duration_match.group(1)
            
            # Extract views and upload time from info-header
            views = ""
            upload_time = ""
            info_header = soup.find('div', class_='info-header')
            if info_header:
                h6_elem = info_header.find('h6')
                if h6_elem:
                    # Get all spans in the h6
                    spans = h6_elem.find_all('span', class_='mr-3', recursive=False)
                    if len(spans) >= 2:
                        upload_time = spans[0].get_text(strip=True)  # "1 day ago"
                        views = spans[1].get_text(strip=True)  # "120 445"
                    elif len(spans) == 1:
                        # Only one span found, assume it's views
                        views = spans[0].get_text(strip=True)
            
            # Extract release date from header-right (inside video-info section)
            release_date = ""
            video_info = soup.find('section', class_='video-info')
            if video_info:
                header_right = video_info.find('div', class_='header-right')
                if header_right:
                    inactive_span = header_right.find('span', class_='inactive-color')
                    if inactive_span:
                        release_date = inactive_span.get_text(strip=True)
            
            # Extract HD quality flag
            hd_quality = False
            if video_info:
                header_right = video_info.find('div', class_='header-right')
                if header_right:
                    hd_text = header_right.get_text()
                    if 'HD' in hd_text or 'Original Video' in hd_text:
                        hd_quality = True
            
            # Extract likes (count in fav button)
            likes = ""
            fav_button = soup.find('button', class_='fav')
            if fav_button:
                count_span = fav_button.find('span', class_='count')
                if count_span:
                    likes = count_span.get_text(strip=True)
            
            # Extract categories (links with class="cat")
            categories = []
            for cat_link in soup.find_all('a', class_='cat'):
                cat_text = cat_link.get_text(strip=True)
                if cat_text and cat_text not in categories:
                    categories.append(cat_text)
            
            # Extract models/cast (from models div)
            models = []
            models_div = soup.find('div', class_='models')
            if models_div:
                for model_link in models_div.find_all('a', class_='model'):
                    # Model name is in data-original-title attribute
                    model_name = model_link.find('span', class_='placeholder')
                    if model_name and model_name.get('data-original-title'):
                        name = model_name.get('data-original-title')
                        if name and name not in models:
                            models.append(name)
            
            # Extract tags (links in tags section, after separator)
            tags = []
            tags_section = soup.find('h5', class_='tags')
            if tags_section:
                # Find all links that are NOT categories (don't have class="cat")
                for link in tags_section.find_all('a'):
                    if 'cat' not in link.get('class', []) and '/tags/' in link.get('href', ''):
                        tag_text = link.get_text(strip=True)
                        if tag_text and tag_text not in tags:
                            tags.append(tag_text)
            
            # Extract preview images/thumbnails (VTT file for video scrubbing)
            preview_images = []
            # Look for vttUrl in the page source (this is the actual video preview)
            vtt_match = re.search(r"var vttUrl = '([^']+)'", page_source)
            if vtt_match:
                vtt_url = vtt_match.group(1)
                preview_images.append(vtt_url)
            
            # Also look for poster/thumbnail images specific to this video
            poster_match = re.search(r'poster="([^"]+)"', page_source)
            if poster_match:
                poster_url = poster_match.group(1)
                if poster_url not in preview_images:
                    preview_images.append(poster_url)
            
            print(f"  ✅ Success: {title[:50]}...")
            print(f"     M3U8: {m3u8_url[:60]}...")
            print(f"     Categories: {len(categories)}, Models: {len(models)}, Tags: {len(tags)}")
            
            # Convert relative upload time to absolute timestamp
            upload_time_absolute = parse_relative_time(upload_time)
            
            return VideoData(
                code=code,
                title=title,
                m3u8_url=m3u8_url,
                thumbnail_url=thumbnail_url,
                duration=duration,
                views=views,
                likes=likes,
                release_date=release_date,
                upload_time=upload_time_absolute,  # Absolute ISO timestamp
                upload_time_relative=upload_time,  # Original "1 hour ago"
                hd_quality=hd_quality,
                categories=categories,
                models=models,
                tags=tags,
                preview_images=preview_images,
                scraped_at=datetime.now().isoformat(),
                source_url=video_url
            )
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_homepage(self, num_pages: int = 1) -> List[VideoData]:
        """
        Scrape videos from homepage
        
        Args:
            num_pages: Number of pages to scrape
            
        Returns:
            List of VideoData objects
        """
        all_videos = []
        
        for page in range(1, num_pages + 1):
            print(f"\n{'='*60}")
            print(f"PAGE {page}/{num_pages}")
            print('='*60)
            
            # Construct page URL
            if page == 1:
                page_url = f"{self.BASE_URL}/"
            else:
                page_url = f"{self.BASE_URL}/{page}/"
            
            try:
                # Get video links from page
                video_links = self.get_video_links_from_page(page_url)
                
                if not video_links:
                    print(f"  ⚠️ No video links found on page {page}")
                    continue
                
                # Scrape each video
                for i, link in enumerate(video_links, 1):
                    print(f"\n[{i}/{len(video_links)}] {link}")
                    
                    try:
                        video_data = self.scrape_video(link)
                        if video_data:
                            all_videos.append(video_data)
                    except Exception as e:
                        print(f"  ❌ Failed to scrape video: {e}")
                        continue
                    
                    # Be nice to the server
                    time.sleep(2)
                    
            except Exception as e:
                print(f"  ❌ Failed to scrape page {page}: {e}")
                continue
        
        return all_videos
    
    def scrape_category(self, category_slug: str, num_pages: int = 1) -> List[VideoData]:
        """
        Scrape videos from a category
        
        Args:
            category_slug: Category slug (e.g., 'censored', 'uncensored')
            num_pages: Number of pages to scrape
            
        Returns:
            List of VideoData objects
        """
        all_videos = []
        
        for page in range(1, num_pages + 1):
            print(f"\n{'='*60}")
            print(f"CATEGORY: {category_slug} - PAGE {page}/{num_pages}")
            print('='*60)
            
            # Construct category URL
            if page == 1:
                page_url = f"{self.BASE_URL}/categories/{category_slug}/"
            else:
                page_url = f"{self.BASE_URL}/categories/{category_slug}/{page}/"
            
            # Get video links from page
            video_links = self.get_video_links_from_page(page_url)
            
            # Scrape each video
            for i, link in enumerate(video_links, 1):
                print(f"\n[{i}/{len(video_links)}] {link}")
                
                video_data = self.scrape_video(link)
                if video_data:
                    all_videos.append(video_data)
                
                # Be nice to the server
                time.sleep(2)
        
        return all_videos


if __name__ == "__main__":
    # Quick test
    scraper = JableScraper(headless=False)
    
    try:
        print("\n" + "="*60)
        print("JABLE.TV SCRAPER - TEST")
        print("="*60)
        
        # Test with homepage, first page only
        videos = scraper.scrape_homepage(num_pages=1)
        
        print(f"\n{'='*60}")
        print(f"SCRAPING COMPLETE")
        print('='*60)
        print(f"Total videos scraped: {len(videos)}")
        
        if videos:
            print(f"\nFirst video:")
            print(json.dumps(asdict(videos[0]), indent=2))
        
    finally:
        scraper.close()
