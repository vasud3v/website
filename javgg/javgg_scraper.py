#!/usr/bin/env python3
"""
JavaGG.net Core Scraper
Scrapes metadata and downloads videos one by one with 32 parallel workers for chunks
"""

import re
import time
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, asdict

from bs4 import BeautifulSoup
from seleniumbase import Driver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@dataclass
class VideoData:
    """Video metadata"""
    code: str
    title: str
    title_japanese: str
    embed_url: str
    m3u8_url: str
    thumbnail_url: str
    release_date: str
    release_date_formatted: str
    duration: str
    duration_minutes: int
    studio: str
    studio_japanese: str
    director: str
    series: str
    models: List[str]
    tags: List[str]
    scraped_at: str


class JavaGGScraper:
    """Core scraper for javgg.net"""
    
    def __init__(self, headless: bool = False, download_dir: str = "downloaded_files"):
        self.headless = headless
        self.download_dir = download_dir
        self.driver = None
        os.makedirs(download_dir, exist_ok=True)
    
    def _init_driver(self):
        """Initialize browser with Cloudflare bypass - GitHub Actions compatible"""
        if self.driver is None:
            print("🌐 Initializing browser...")
            
            # Try multiple initialization methods
            methods = [
                self._init_with_uc_driver,
                self._init_with_standard_chrome,
                self._init_with_chromium
            ]
            
            last_error = None
            for method in methods:
                try:
                    method()
                    if self.driver:
                        # Set additional timeouts
                        self.driver.set_page_load_timeout(60)
                        self.driver.set_script_timeout(30)
                        print("  ✅ Browser ready")
                        return
                except Exception as e:
                    last_error = e
                    print(f"  ⚠️ Method failed: {str(e)[:80]}")
                    if self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.driver = None
            
            # All methods failed
            print(f"  ❌ All browser initialization methods failed")
            if last_error:
                raise last_error
            else:
                raise Exception("Failed to initialize browser")
    
    def _init_with_uc_driver(self):
        """Try undetected-chromedriver (best for Cloudflare)"""
        print("  Trying undetected-chromedriver...")
        self.driver = Driver(
            uc=True, 
            headless=self.headless, 
            incognito=True,
            agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            disable_csp=True,
            no_sandbox=True
        )
    
    def _init_with_standard_chrome(self):
        """Try standard Chrome with stealth options"""
        print("  Trying standard Chrome...")
        from selenium.webdriver.chrome.service import Service
        
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Try to find Chrome/Chromium binary
        import shutil
        chrome_paths = [
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/usr/bin/google-chrome',
            shutil.which('chromium-browser'),
            shutil.which('google-chrome'),
        ]
        
        for path in chrome_paths:
            if path and os.path.exists(path):
                options.binary_location = path
                break
        
        self.driver = webdriver.Chrome(options=options)
    
    def _init_with_chromium(self):
        """Try Chromium specifically (GitHub Actions)"""
        print("  Trying Chromium...")
        from selenium.webdriver.chrome.service import Service
        
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Force Chromium binary
        options.binary_location = '/usr/bin/chromium-browser'
        
        # Try chromium-chromedriver
        service = None
        if os.path.exists('/usr/bin/chromedriver'):
            service = Service('/usr/bin/chromedriver')
        
        if service:
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
    
    def _extract_m3u8_from_embed_fast(self, embed_url: str) -> Optional[str]:
        """Fast M3U8 extraction with minimal waits"""
        print(f"  🔍 Quick M3U8 extraction...")
        
        driver = None
        try:
            options = Options()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--headless')
            options.page_load_strategy = 'none'  # Don't wait for page load
            options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            # Find Chrome binary
            import shutil
            chrome_paths = [
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/usr/bin/google-chrome',
                shutil.which('chromium-browser'),
                shutil.which('google-chrome'),
            ]
            
            chrome_binary = None
            for path in chrome_paths:
                if path and os.path.exists(path):
                    chrome_binary = path
                    break
            
            if chrome_binary:
                options.binary_location = chrome_binary
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(10)
            
            # Load page
            driver.get(embed_url)
            time.sleep(2)  # Minimal wait
            
            # Try to play video
            try:
                driver.execute_script("var v=document.querySelector('video');if(v){v.muted=true;v.play();}")
                time.sleep(1)  # Quick wait
            except:
                pass
            
            # Check logs once
            try:
                logs = driver.get_log('performance')
                for log in logs:
                    try:
                        message = json.loads(log['message'])
                        if message.get('message', {}).get('method') == 'Network.responseReceived':
                            url = message.get('message', {}).get('params', {}).get('response', {}).get('url', '')
                            if '.m3u8' in url:
                                driver.quit()
                                return url
                    except:
                        continue
            except:
                pass
            
            driver.quit()
            return None
            
        except Exception as e:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return None
    
    def _extract_m3u8_from_embed(self, embed_url: str) -> Optional[str]:
        """Extract M3U8 URL from embed using network monitoring"""
        print(f"  🔍 Extracting M3U8 from embed...")
        
        driver = None
        try:
            options = Options()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--headless')
            options.page_load_strategy = 'eager'
            options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            # Try to find Chrome binary (GitHub Actions uses chromium-browser)
            import shutil
            chrome_paths = [
                '/usr/bin/chromium-browser',  # GitHub Actions
                '/usr/bin/chromium',
                '/usr/bin/google-chrome',
                '/usr/bin/chrome',
                shutil.which('chromium-browser'),
                shutil.which('chromium'),
                shutil.which('google-chrome'),
            ]
            
            chrome_binary = None
            for path in chrome_paths:
                if path and os.path.exists(path):
                    chrome_binary = path
                    break
            
            if chrome_binary:
                options.binary_location = chrome_binary
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            driver.set_script_timeout(30)
            
            print(f"  ⏳ Loading embed page...")
            try:
                driver.get(embed_url)
            except Exception as e:
                if 'timeout' not in str(e).lower():
                    raise
            
            time.sleep(3)  # Reduced from 5 to 3 seconds
            
            # Try multiple methods to trigger video and find M3U8
            print(f"  ▶️ Triggering video play...")
            
            # Method 1: Click play button
            try:
                driver.execute_script("""
                    var playBtn = document.querySelector('.vjs-big-play-button, .play-button, button[aria-label*="Play"]');
                    if (playBtn) playBtn.click();
                """)
                time.sleep(1)  # Reduced from 2 to 1
            except:
                pass
            
            # Method 2: Play video element directly
            try:
                driver.execute_script("""
                    var video = document.querySelector('video');
                    if (video) {
                        video.muted = true;
                        video.play();
                    }
                """)
                time.sleep(2)  # Reduced from 3 to 2
            except:
                pass
            
            # Method 3: Check for jwplayer
            try:
                driver.execute_script("""
                    if (typeof jwplayer !== 'undefined') {
                        var player = jwplayer();
                        if (player) player.play();
                    }
                """)
                time.sleep(1)  # Reduced from 2 to 1
            except:
                pass
            
            print(f"  🔍 Checking network logs for M3U8...")
            
            # Wait and check logs - reduced iterations
            m3u8_url = None
            for attempt in range(2):  # Reduced from 3 to 2 attempts
                try:
                    logs = driver.get_log('performance')
                    
                    for log in logs:
                        try:
                            message = json.loads(log['message'])
                            method = message.get('message', {}).get('method', '')
                            
                            if method == 'Network.responseReceived':
                                response = message.get('message', {}).get('params', {}).get('response', {})
                                url = response.get('url', '')
                                
                                # Look for M3U8 URLs
                                if '.m3u8' in url:
                                    print(f"  ✅ Found M3U8: {url[:80]}...")
                                    m3u8_url = url
                                    break
                        except:
                            continue
                    
                    if m3u8_url:
                        break
                    
                    time.sleep(1)  # Reduced from 2 to 1
                except:
                    pass
            
            driver.quit()
            
            if m3u8_url:
                return m3u8_url
            else:
                print(f"  ⚠️ No M3U8 found in network logs")
                return None
            
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"  ⚠️ M3U8 extraction error: {error_msg}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            return None
    
    def scrape_video(self, video_url: str) -> Optional[VideoData]:
        """Scrape video metadata with timeout"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Scraping timeout")
        
        try:
            self._init_driver()
            
            print(f"\n{'='*70}")
            print(f"🎬 Scraping: {video_url}")
            print(f"{'='*70}")
            
            # Set alarm for 60 seconds (only on Unix systems)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)  # 60 second timeout for entire scraping
            
            # Extract code
            code_match = re.search(r'/jav/([^/\?#]+)', video_url)
            if not code_match:
                return None
            
            code = code_match.group(1).upper()
            print(f"  📝 Code: {code}")
            
            # Load page with timeout
            print(f"  🌐 Loading page...")
            try:
                self.driver.set_page_load_timeout(20)  # Reduced from 30 to 20
                self.driver.get(video_url)
                time.sleep(2)  # Reduced from 3 to 2
                print(f"  ✅ Page loaded")
            except Exception as e:
                print(f"  ⚠️ Page load timeout or error: {str(e)[:100]}")
                time.sleep(1)  # Reduced from 2 to 1
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract title (full from description)
            title = ""
            title_japanese = ""
            
            # Get full title from description meta tag
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                desc = og_desc.get('content', '')
                # Format: "CODE JAV (English Title) ActressName 日本語タイトル"
                # Extract English title (between "JAV" and actress name or Japanese text)
                # Try to extract English part (after "JAV" and before Japanese characters)
                jav_match = re.search(r'JAV\s+(.+?)(?=[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]|$)', desc)
                if jav_match:
                    title = jav_match.group(1).strip()
                
                # Extract Japanese title (Japanese characters)
                jp_match = re.search(r'([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF…]+)', desc)
                if jp_match:
                    title_japanese = jp_match.group(1).strip()
            
            # Fallback to og:title if description parsing failed
            if not title:
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    title = og_title.get('content', '')
            
            # Final fallback to code
            if not title:
                title = code
            
            # Extract embed URL (REAL VIDEO)
            embed_url = ""
            iframes = soup.find_all('iframe', class_=re.compile(r'metaframe'))
            if not iframes:
                iframes = soup.find_all('iframe', src=True)
            
            embed_hosts = ['jav-vids.xyz', 'javggvideo.xyz', 'javstreamhg.xyz']
            
            for iframe in iframes:
                iframe_src = iframe.get('src', '')
                if any(host in iframe_src.lower() for host in embed_hosts):
                    embed_url = iframe_src
                    print(f"  ✅ Embed URL: {embed_url[:80]}...")
                    break
            
            if not embed_url:
                print(f"  ❌ No embed URL found")
                return None
            
            # Try to extract M3U8 URL from embed (needed for download)
            print(f"  🔍 Extracting stream URL from embed...")
            
            # Quick extraction with reduced timeouts
            m3u8_url = self._extract_m3u8_from_embed_fast(embed_url)
            
            if m3u8_url:
                print(f"  ✅ Found stream URL")
            else:
                print(f"  ⚠️ Could not extract stream URL, will try embed directly")
            
            # Extract thumbnail
            thumbnail_url = ""
            og_image = soup.find('meta', property='og:image')
            if og_image:
                thumbnail_url = og_image.get('content', '')
            
            # Extract release date
            release_date = ""
            release_date_formatted = ""
            
            # Try to get from article:published_time meta tag
            published_meta = soup.find('meta', property='article:published_time')
            if published_meta:
                published_time = published_meta.get('content', '')
                if published_time:
                    # Parse ISO format: 2025-02-07T12:42:25+08:00
                    try:
                        dt = datetime.fromisoformat(published_time.replace('+08:00', ''))
                        release_date = dt.strftime('%Y-%m-%d')
                        # Format as "2nd Feb 2025"
                        day = dt.day
                        suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
                        release_date_formatted = dt.strftime(f'%d{suffix} %b %Y').lstrip('0')
                    except:
                        pass
            
            # Fallback: search in page source
            if not release_date:
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', self.driver.page_source)
                if date_match:
                    release_date = date_match.group(1)
                    try:
                        dt = datetime.strptime(release_date, '%Y-%m-%d')
                        day = dt.day
                        suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
                        release_date_formatted = dt.strftime(f'%d{suffix} %b %Y').lstrip('0')
                    except:
                        release_date_formatted = release_date
            
            # Extract duration
            duration = ""
            duration_minutes = 0
            
            # Look for duration in .extra class
            extra_div = soup.find('div', class_='extra')
            if extra_div:
                extra_text = extra_div.get_text(strip=True)
                # Format: "Feb. 07, 2025157 Min." - need to extract just the minutes
                # Look for pattern: number followed by "Min" (not part of a date)
                duration_match = re.search(r'(\d{2,3})\s*Min', extra_text, re.I)
                if duration_match:
                    duration_minutes = int(duration_match.group(1))
                    duration = f"{duration_minutes} min"
            
            # Extract studio/maker
            studio = ""
            studio_japanese = ""
            
            # Look for studio in main content only
            main_content = soup.find('div', id='single')
            if main_content:
                maker_links = main_content.find_all('a', href=re.compile(r'/maker/'))
                for link in maker_links:
                    text = link.text.strip()
                    # Skip if it has count in parentheses (sidebar link)
                    if '(' not in text:
                        # Check if it's Japanese or English
                        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text):
                            studio_japanese = text
                        else:
                            studio = text
                        if studio and studio_japanese:
                            break
            
            # Extract director
            director = ""
            if main_content:
                director_links = main_content.find_all('a', href=re.compile(r'/director/'))
                for link in director_links:
                    text = link.text.strip()
                    if text and '(' not in text:
                        director = text
                        break
            
            # Extract series/label
            series = ""
            if main_content:
                label_links = main_content.find_all('a', href=re.compile(r'/label/'))
                for link in label_links:
                    text = link.text.strip()
                    # Skip if it has count or is the same as code
                    if '(' not in text and text.upper() != code:
                        series = text
                        break
            
            # Extract models - ONLY from main content area, not sidebar/menu
            models = []
            main_content = soup.find('div', id='single')
            if main_content:
                model_links = main_content.find_all('a', href=re.compile(r'/star/'))
                exclude_texts = ['jav actress list', 'chinese actress', 'japanese actress', 'korean actress', 'all actress', 'actress list']
                for link in model_links:
                    text = link.text.strip()
                    # Skip if it's a navigation link
                    text_lower = text.lower()
                    if any(excl in text_lower for excl in exclude_texts):
                        continue
                    if text:
                        # Remove count in parentheses if present
                        if '(' in text:
                            text = text.split('(')[0].strip()
                        if text:  # Make sure there's still text after removing count
                            models.append(text)
                    if len(models) >= 10:  # Limit to 10
                        break
            
            # If no models found in main content, extract from title
            if not models:
                # Try to extract actress name from title (often in format "CODE — Name, ...")
                title_match = re.search(r'—\s*([^,]+)', title)
                if title_match:
                    actress_name = title_match.group(1).strip()
                    # Clean up common words
                    if actress_name and not any(word in actress_name.lower() for word in ['who works', 'the ', 'a ', 'an ', 'is a', 'has ']):
                        models.append(actress_name)
            
            # Extract genres (from /genre/ URLs, not /tag/)
            tags = []
            genre_links = soup.find_all('a', href=re.compile(r'/genre/'))
            for link in genre_links:
                text = link.text.strip()
                # Skip if it's a navigation link or contains count in parentheses
                if text and text.lower() != 'genre' and '(' not in text:
                    tags.append(text)
                if len(tags) >= 10:  # Limit to 10
                    break
            
            print(f"  ✅ Metadata extracted")
            
            return VideoData(
                code=code,
                title=title,
                title_japanese=title_japanese,
                embed_url=embed_url,
                m3u8_url=m3u8_url,
                thumbnail_url=thumbnail_url,
                release_date=release_date,
                release_date_formatted=release_date_formatted,
                duration=duration,
                duration_minutes=duration_minutes,
                studio=studio,
                studio_japanese=studio_japanese,
                director=director,
                series=series,
                models=models,
                tags=tags,
                scraped_at=datetime.now().isoformat()
            )
            
        except TimeoutError:
            print(f"  ❌ Scraping timeout (60 seconds)")
            return None
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None
        finally:
            # Cancel alarm if set
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
    
    def download_video(self, video_data: VideoData) -> bool:
        """Download video using yt-dlp with 32 concurrent fragments"""
        output_path = os.path.join(self.download_dir, f"{video_data.code}.mp4")
        
        # Check if already downloaded
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024*1024:
            print(f"  ✅ Already downloaded: {output_path}")
            return True
        
        print(f"\n{'='*70}")
        print(f"📥 Downloading: {video_data.code}")
        print(f"{'='*70}")
        print(f"  Title: {video_data.title[:60]}...")
        print(f"  URL: {video_data.m3u8_url[:80]}...")
        
        # Use yt-dlp with 32 concurrent fragments
        cmd = [
            'yt-dlp',
            '--no-warnings',
            '--concurrent-fragments', '32',
            '--retries', '10',
            '--fragment-retries', '10',
            '-o', output_path,
            '--newline',
            video_data.m3u8_url
        ]
        
        try:
            start_time = time.time()
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                line = line.strip()
                if line and ('[download]' in line or '%' in line):
                    print(f"  {line}")
            
            process.wait()
            elapsed = time.time() - start_time
            
            if process.returncode == 0 and os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024*1024)
                print(f"  ✅ Downloaded: {size_mb:.1f} MB in {elapsed:.1f}s")
                return True
            else:
                print(f"  ❌ Download failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def scrape_and_download(self, video_url: str) -> bool:
        """Scrape metadata and download video"""
        # Scrape metadata
        video_data = self.scrape_video(video_url)
        if not video_data:
            return False
        
        # Save metadata
        metadata_file = os.path.join(self.download_dir, f"{video_data.code}.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(video_data), f, indent=2, ensure_ascii=False)
        print(f"  💾 Metadata saved: {metadata_file}")
        
        # Download video
        return self.download_video(video_data)
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("  JAVGG.NET SCRAPER")
    print("="*70)
    
    # Get video URLs
    video_urls = []
    
    print("\nEnter video URLs (one per line, empty line to finish):")
    while True:
        url = input("> ").strip()
        if not url:
            break
        video_urls.append(url)
    
    if not video_urls:
        print("❌ No URLs provided")
        return
    
    print(f"\n📊 Processing {len(video_urls)} videos...")
    
    scraper = JavaGGScraper(headless=False)
    
    try:
        success = 0
        failed = 0
        
        for i, url in enumerate(video_urls, 1):
            print(f"\n{'='*70}")
            print(f"Video {i}/{len(video_urls)}")
            print(f"{'='*70}")
            
            if scraper.scrape_and_download(url):
                success += 1
            else:
                failed += 1
            
            time.sleep(2)
        
        print(f"\n{'='*70}")
        print("COMPLETE")
        print(f"{'='*70}")
        print(f"✅ Success: {success}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Files: {scraper.download_dir}")
        print(f"{'='*70}")
        
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
