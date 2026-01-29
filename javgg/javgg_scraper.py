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
import requests
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, asdict

from bs4 import BeautifulSoup
from seleniumbase import Driver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


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
    
    def __init__(self, headless: bool = True, download_dir: str = "downloaded_files"):
        # Force non-headless locally for better success rate
        is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
        if not is_ci:
            print("  ℹ️ Running locally - forcing non-headless mode for better compatibility")
            self.headless = False
        else:
            self.headless = headless
        
        self.download_dir = download_dir
        self.driver = None
        os.makedirs(download_dir, exist_ok=True)
    
    def _kill_stale_processes(self):
        """Kill stale Chrome/Chromedriver processes"""
        print("  🧹 Cleaning up stale browser processes...", flush=True)
        try:
            if os.name == 'nt':  # Windows
                try:
                    subprocess.run('taskkill /F /IM chrome.exe /T', shell=True, 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run('taskkill /F /IM chromedriver.exe /T', shell=True, 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    print(f"  ⚠️ Warning: Failed to kill Windows processes: {e}")
            else:  # Linux/Mac
                try:
                    subprocess.run(['pkill', '-f', 'chrome'], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(['pkill', '-f', 'chromedriver'], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    print(f"  ⚠️ Warning: Failed to kill Linux processes: {e}")
        except Exception as outside_e:
             print(f"  ⚠️ Critical error in process cleanup: {outside_e}")
        
        print("  ✅ Process cleanup finished", flush=True)

    def _init_driver(self):
        """Initialize browser with Cloudflare bypass - GitHub Actions compatible"""
        
        if self.driver is None:
            # Kill stale processes first to prevent hangs
            self._kill_stale_processes()
            
            print("🌐 Initializing browser...", flush=True)
            
            # In CI, try seleniumbase UC mode which works better than standard Chrome
            is_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
            
            # Always try UC mode first as it handles Cloudflare correctly
            print("  ℹ️ Using SeleniumBase UC mode for better Cloudflare bypass")
            methods = [
                self._init_with_uc_driver,
                self._init_with_standard_chrome
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
        print("  Trying SeleniumBase UC mode...")
        
        # UC mode can be slow to start, increase timeout
        try:
            self.driver = Driver(
                uc=True, 
                headless=False, # Force headful for better Cloudflare bypass
                incognito=True,
                # agent=None, # Let UC driver choose appropriate agent
                disable_csp=True,
                no_sandbox=True,
                page_load_strategy='none',  # Don't wait for full page load
                disable_gpu=True,  # Stability
                uc_subprocess=True,  # Better process management for UC
            )
            
            # Test if driver works
            _ = self.driver.current_url
            print("  ✅ UC driver initialized successfully")
            
        except Exception as e:
            print(f"  ⚠️ UC driver failed: {str(e)[:100]}")
            raise e
    
    def _init_with_standard_chrome(self):
        """Try standard Chrome with stealth options"""
        print("  Trying standard Chrome...", flush=True)

        
        print("  DEBUG: Creating Chrome Options...", flush=True)
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        else:
            print("  DEBUG: Running in HEADFUL mode", flush=True)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--ignore-certificate-errors')
        # options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # CRITICAL: Use 'none' page load strategy like jable scraper
        options.page_load_strategy = 'none'
        
        # Add preferences to appear more like a real browser
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Try to find Chrome/Chromium binary
        import shutil
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            shutil.which('google-chrome'),
            shutil.which('chromium-browser'),
        ]
        
        for path in chrome_paths:
            if path and os.path.exists(path):
                options.binary_location = path
                print(f"  DEBUG: Found Chrome binary at {path}", flush=True)
                break
        
        print("  DEBUG: Launching webdriver.Chrome with ChromeDriverManager...", flush=True)
        try:
            # Clean up PATH to avoid conflict with existing drivers
            try:
                # Remove local-packages/drivers from PATH if present to force new driver
                current_path = os.environ.get('PATH', '')
                new_path_dirs = [p for p in current_path.split(os.pathsep) if 'seleniumbase' not in p.lower()]
                os.environ['PATH'] = os.pathsep.join(new_path_dirs)
            except:
                pass

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("  DEBUG: webdriver.Chrome launched successfully", flush=True)
        except Exception as e:
            print(f"  ❌ webdriver.Chrome launch failed: {e}", flush=True)
            raise e
        
        # Execute CDP commands to hide automation
        # self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        #    "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
        # })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            '''
        })
    
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
    
    def _unpack_js(self, p, a, c, k):
        """Unpack JavaScript packed with Dean Edwards' packer"""
        
        def base_repr(num, base):
            """Convert number to base representation"""
            if num == 0:
                return '0'
            
            digits = '0123456789abcdefghijklmnopqrstuvwxyz'
            result = ''
            
            while num > 0:
                result = digits[num % base] + result
                num //= base
            
            return result
        
        # Replace tokens from highest to lowest
        while c > 0:
            c -= 1
            if c < len(k) and k[c]:
                # Get the token representation in the given base
                token = base_repr(c, a) if c >= a else str(c)
                # Replace with word boundaries
                pattern = r'\b' + re.escape(token) + r'\b'
                p = re.sub(pattern, k[c], p)
        
        return p
    
    def _extract_m3u8_from_embed(self, embed_url: str) -> Optional[str]:
        """Extract M3U8 URL from embed page - REQUESTS-BASED VERSION"""
        print(f"  🔍 Extracting M3U8 from embed...")
        
        # Use requests instead of Selenium to bypass anti-bot protection
        try:
            print(f"  📄 Fetching embed page with requests...")
            
            # Set up headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://javgg.net/',
            }
            
            # Create session for connection pooling
            session = requests.Session()
            
            # Fetch the embed page
            response = session.get(embed_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Handle gzip compression manually if needed
            page_source = response.text
            
            # If response looks binary/corrupted, try to decompress
            if len(page_source) < 1000 or not '<' in page_source[:100]:
                try:
                    import gzip
                    page_source = gzip.decompress(response.content).decode('utf-8')
                    print(f"  ✅ Decompressed gzip content")
                except:
                    # Not gzipped or decompression failed
                    page_source = response.content.decode('utf-8', errors='ignore')
            
            print(f"  ✅ Fetched {len(page_source)} bytes")
            
            # Look for packed JavaScript
            print(f"  🔍 Searching for packed JavaScript...")
            packed_pattern = r"eval\(function\(p,a,c,k,e,d\)\{[^}]+\}\('(.+?)',(\d+),(\d+),'(.+?)'\.split\('\|'\)\)\)"
            
            match = re.search(packed_pattern, page_source, re.DOTALL)
            
            if match:
                print(f"  ✅ Found packed JavaScript")
                
                # Extract components
                p = match.group(1)  # The packed code
                a = int(match.group(2))  # Base (usually 36)
                c = int(match.group(3))  # Count
                k = match.group(4).split('|')  # Dictionary
                
                print(f"  🔓 Unpacking (base={a}, count={c})...")
                
                # Unpack
                deobfuscated = self._unpack_js(p, a, c, k)
                
                print(f"  ✅ Deobfuscated {len(deobfuscated)} bytes")
                
                # Look for M3U8 URLs in deobfuscated code
                print(f"  🔍 Searching for M3U8 URLs...")
                m3u8_patterns = [
                    r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)',
                    r'"(https?://[^"]+\.m3u8[^"]*)"',
                    r"'(https?://[^']+\.m3u8[^']*)'",
                    r':\s*"([^"]+\.m3u8[^"]*)"',
                ]
                
                found_urls = []
                for pattern in m3u8_patterns:
                    m3u8_matches = re.findall(pattern, deobfuscated, re.IGNORECASE)
                    if m3u8_matches:
                        for m3u8_match in m3u8_matches:
                            if isinstance(m3u8_match, tuple):
                                m3u8_url = m3u8_match[-1] if m3u8_match[-1] else m3u8_match[0]
                            else:
                                m3u8_url = m3u8_match
                            
                            if m3u8_url and '.m3u8' in m3u8_url:
                                # Make URL absolute if needed
                                if m3u8_url.startswith('//'):
                                    m3u8_url = 'https:' + m3u8_url
                                elif m3u8_url.startswith('/'):
                                    # Relative to embed domain
                                    from urllib.parse import urlparse
                                    parsed = urlparse(embed_url)
                                    m3u8_url = f"{parsed.scheme}://{parsed.netloc}{m3u8_url}"
                                
                                if m3u8_url.startswith('http') and m3u8_url not in found_urls:
                                    found_urls.append(m3u8_url)
                
                if found_urls:
                    # Return the first URL (usually the best quality)
                    print(f"  ✅ Found {len(found_urls)} M3U8 URL(s)")
                    for i, url in enumerate(found_urls, 1):
                        print(f"     [{i}] {url[:80]}...")
                    return found_urls[0]
            
            # Fallback: Try to find M3U8 URLs directly in page source
            print(f"  🔍 Checking page source directly...")
            m3u8_patterns = [
                r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)',
                r'"(https?://[^"]+\.m3u8[^"]*)"',
                r"'(https?://[^']+\.m3u8[^']*)'",
            ]
            
            for pattern in m3u8_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        m3u8_url = match[-1]
                    else:
                        m3u8_url = match
                    
                    if m3u8_url and '.m3u8' in m3u8_url and m3u8_url.startswith('http'):
                        print(f"  ✅ Found M3U8 in page source: {m3u8_url[:80]}...")
                        return m3u8_url
            
            print(f"  ⚠️ No M3U8 URL found")
            
            # Save for debugging
            debug_file = os.path.join(self.download_dir, 'embed_page_debug.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"  💾 Saved embed page to {debug_file}")
            
            return None
            
        except requests.exceptions.Timeout:
            print(f"  ❌ Request timeout after 15 seconds")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request error: {str(e)[:100]}")
            return None
        except Exception as e:
            print(f"  ❌ M3U8 extraction error: {str(e)[:100]}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_video(self, video_url: str) -> Optional[VideoData]:
        """Scrape video metadata with timeout - tries requests first, then Selenium"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Scraping timeout")
        
        try:
            # Set alarm for 90 seconds (only on Unix systems)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(90)  # 90 second timeout for entire scraping
            
            print(f"\n{'='*70}")
            print(f"🎬 Scraping: {video_url}")
            print(f"{'='*70}")
            
            # Extract code
            code_match = re.search(r'/jav/([^/\?#]+)', video_url)
            if not code_match:
                return None
            
            code = code_match.group(1).upper()
            print(f"  📝 Code: {code}")
            
            # Method 1: Requests-based scraping removed as requested
            # Directly use Selenium
            return self._scrape_with_selenium(video_url, code)
            
        except TimeoutError:
            print(f"  ❌ Scraping timeout", flush=True)
            return None
        except Exception as e:
            print(f"  ❌ Scraping error: {str(e)[:200]}", flush=True)
            if "refused" in str(e) or "reset" in str(e) or "closed" in str(e) or "invalid session" in str(e) or "Max retries exceeded" in str(e):
                 print("  🔄 Connection lost (global catch), forcing driver re-init...")
                 try:
                     if self.driver: self.driver.quit()
                 except:
                     pass
                 self.driver = None
            return None
        finally:
            # Cancel alarm
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
    
    def _scrape_with_requests(self, video_url: str, code: str) -> Optional[VideoData]:
        """Try to scrape using requests library (faster, better Cloudflare bypass)"""
        try:
            import requests
            
            # Headers to mimic real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://javgg.net/',
            }
            
            # Add random delay
            import random
            time.sleep(random.uniform(1, 2))
            
            # Fetch page
            # Fetch page
            print(f"    📡 Fetching {video_url[:50]}...", flush=True)
            response = requests.get(video_url, headers=headers, timeout=20, allow_redirects=True)
            
            print(f"    📊 Status: {response.status_code}", flush=True)
            print(f"    📏 Content length: {len(response.text)} bytes", flush=True)
            print(f"    🔗 Final URL: {response.url[:60]}...", flush=True)
            
            # Check response - accept both 200 and 403 (some sites return 403 but still work)
            if response.status_code not in [200, 403]:
                print(f"    ⚠️ Unexpected status code: {response.status_code}")
                return None
            
            # If we got content, try to parse it regardless of status code
            if len(response.text) < 1000:
                print(f"    ⚠️ Response too small, likely blocked")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check what we actually got
            page_title = soup.find('title')
            print(f"    📄 Page title: {page_title.text if page_title else 'N/A'}")
            
            # Extract title
            title_elem = soup.find('h1', class_='entry-title') or soup.find('h1')
            title = title_elem.text.strip() if title_elem else code
            print(f"    📝 Video title: {title[:50]}...")
            
            # Extract thumbnail
            thumbnail_url = None
            og_image = soup.find('meta', property='og:image')
            if og_image:
                thumbnail_url = og_image.get('content')
                print(f"    🖼️ Thumbnail: {thumbnail_url[:50] if thumbnail_url else 'None'}...")
            
            # NEW: Try to find embed URL in raw HTML (before JavaScript)
            # Look for iframe src in script tags or data attributes
            embed_url = None
            
            # Method 1: Search in all script tags for embed URLs
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.string if script.string else ''
                # Look for common embed patterns
                embed_patterns = [
                    r'["\']https?://[^"\']+/embed/[^"\']+["\']',
                    r'["\']https?://[^"\']+/player/[^"\']+["\']',
                    r'src\s*[:=]\s*["\']([^"\']+/(?:embed|player)/[^"\']+)["\']',
                ]
                for pattern in embed_patterns:
                    matches = re.findall(pattern, script_text)
                    if matches:
                        # Clean up the match
                        potential_url = matches[0].strip('"\'')
                        if 'embed' in potential_url or 'player' in potential_url:
                            embed_url = potential_url
                            print(f"    ✅ Found embed URL in script: {embed_url[:60]}...")
                            break
                if embed_url:
                    break
            
            # Method 2: Look for iframes (even if not loaded by JS yet)
            if not embed_url:
                iframes = soup.find_all('iframe')
                print(f"    🎬 Found {len(iframes)} iframes in raw HTML")
                
                for iframe in iframes:
                    src = iframe.get('src', '') or iframe.get('data-src', '')
                    if src and ('embed' in src or 'player' in src or 'stream' in src):
                        if not src.startswith('http'):
                            src = 'https:' + src if src.startswith('//') else 'https://javgg.net' + src
                        embed_url = src
                        print(f"    ✅ Found embed URL in iframe: {embed_url[:60]}...")
                        break
            
            if not embed_url:
                print(f"    ⚠️ No embed URL found in raw HTML")
                return None
            
            print(f"    ✅ Found embed URL: {embed_url[:60]}...")
            
            # Try to extract M3U8 from embed
            m3u8_url = self._extract_m3u8_from_embed(embed_url)
            
            return VideoData(
                code=code,
                title=title,
                title_japanese="",
                embed_url=embed_url,
                m3u8_url=m3u8_url or "",
                thumbnail_url=thumbnail_url or "",
                release_date="",
                release_date_formatted="",
                duration="",
                duration_minutes=0,
                studio="",
                studio_japanese="",
                director="",
                series="",
                models=[],
                tags=[],
                scraped_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"    ⚠️ Requests error: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            return None
    
    def _scrape_with_selenium(self, video_url: str, code: str) -> Optional[VideoData]:
        """Scrape using Selenium (fallback method)"""
    def _scrape_with_selenium(self, video_url: str, code: str) -> Optional[VideoData]:
        """Scrape using Selenium (fallback method)"""
        try:
            self._init_driver()
            
            print(f"  🌐 Loading page with Selenium...")
            
            # Ensure we only have one tab
            if len(self.driver.window_handles) > 1:
                print(f"  🧹 Closing {len(self.driver.window_handles) - 1} extra tabs/popups...")
                current = self.driver.current_window_handle
                for handle in self.driver.window_handles:
                    if handle != current:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                self.driver.switch_to.window(current)
            
            # Load the page
            try:
                self.driver.get(video_url)
            except Exception as e:
                print(f"  ❌ Selenium navigation failed: {e}")
                if "refused" in str(e) or "reset" in str(e) or "closed" in str(e) or "invalid session" in str(e) or "Max retries exceeded" in str(e):
                     print("  🔄 Connection lost, forcing driver re-init next time...")
                     try:
                         self.driver.quit()
                     except:
                         pass
                     self.driver = None
                return None
            
            # Wait for body
            print(f"  ⏳ Waiting for page body...")
            body_loaded = False
            for i in range(20):
                try:
                    body = self.driver.find_element("tag name", "body")
                    if body:
                        body_loaded = True
                        print(f"  ✓ Page body loaded after {i * 0.5}s")
                        break
                except:
                    pass
                time.sleep(0.5)
            
            if not body_loaded:
                print(f"  ❌ Page body failed to load")
                return None
            
            # Check page title to see if we're blocked
            try:
                page_title = self.driver.title
                print(f"  📄 Page title: {page_title}")
                
                # If title indicates blocking, wait longer
                if "Checking" in page_title or "Just a moment" in page_title:
                    print(f"  ⏳ Detected challenge page, entering wait loop...")
                    max_wait = 60
                    waited = 0
                    while waited < max_wait:
                        time.sleep(2)
                        waited += 2
                        current_title = self.driver.title
                        if "Checking" not in current_title and "Just a moment" not in current_title and "javgg" in self.driver.current_url:
                            print(f"  ✅ Cloudflare check passed after {waited}s")
                            break
                        if waited % 10 == 0:
                            print(f"  ⏳ Still checking... ({waited}s)")
                    
                    page_title = self.driver.title
                    print(f"  📄 Final title: {page_title}")
            except Exception as e:
                print(f"  ⚠️ Error checking title: {e}")
            
            # Wait for JavaScript to execute
            print(f"  ⏳ Waiting 15 seconds for JavaScript...")
            time.sleep(15)
            
            # Scroll to trigger lazy loading
            print(f"  📜 Scrolling page...")
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            except Exception as e:
                print(f"  ⚠️ Scroll error: {str(e)[:100]}")
            
            # Now check for iframes
            print(f"  🔍 Checking for iframes...")
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Debug: Save page source
            debug_file = os.path.join(self.download_dir, f"{code}_selenium_page.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"  💾 Saved page source to {debug_file}")
            
            # Find iframes
            iframes = soup.find_all('iframe')
            print(f"  🎬 Found {len(iframes)} iframes")
            
            if len(iframes) == 0:
                # Try waiting more and checking again
                print(f"  ⏳ No iframes yet, waiting 10 more seconds...")
                time.sleep(10)
                
                # Try clicking on video area
                try:
                    self.driver.execute_script("""
                        var videoArea = document.querySelector('.entry-content, .video-container, .player-container, .video-player');
                        if (videoArea) {
                            videoArea.click();
                            console.log('Clicked video area');
                        }
                    """)
                    time.sleep(5)
                except:
                    pass
                
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                iframes = soup.find_all('iframe')
                print(f"  🎬 Now found {len(iframes)} iframes")
            
            if len(iframes) == 0:
                print(f"  ❌ No iframes found after all attempts")
                
                # Check if page has any video-related content
                video_divs = soup.find_all(['div', 'section'], class_=lambda x: x and ('video' in x.lower() or 'player' in x.lower()))
                print(f"  🔍 Found {len(video_divs)} video-related divs")
                
                # Check console for errors
                try:
                    logs = self.driver.get_log('browser')
                    if logs:
                        print(f"  🔍 Browser console has {len(logs)} messages")
                        for log in logs[:5]:
                            if 'error' in log.get('level', '').lower():
                                print(f"    ❌ {log.get('message', '')[:100]}")
                except:
                    pass
                
                return None
            
            # Extract embed URL from iframe
            embed_url = None
            for iframe in iframes:
                src = iframe.get('src', '') or iframe.get('data-src', '')
                if src:
                    print(f"  🔗 iframe src: {src[:80]}...")
                    if 'embed' in src or 'player' in src or 'stream' in src:
                        if not src.startswith('http'):
                            src = 'https:' + src if src.startswith('//') else 'https://javgg.net' + src
                        embed_url = src
                        print(f"  ✅ Selected embed URL: {embed_url[:80]}...")
                        break
            
            if not embed_url:
                print(f"  ❌ No valid embed URL found in iframes")
                return None
            
            # Extract other metadata
            title = code
            title_elem = soup.find('h1', class_='entry-title') or soup.find('h1')
            if title_elem:
                title = title_elem.text.strip()
            
            thumbnail_url = ""
            og_image = soup.find('meta', property='og:image')
            if og_image:
                thumbnail_url = og_image.get('content', '')
            
            # Try to extract M3U8 from embed
            m3u8_url = self._extract_m3u8_from_embed(embed_url)
            
            print(f"  ✅ Selenium scraping successful")
            
            return VideoData(
                code=code,
                title=title,
                title_japanese="",
                embed_url=embed_url,
                m3u8_url=m3u8_url or "",
                thumbnail_url=thumbnail_url,
                release_date="",
                release_date_formatted="",
                duration="",
                duration_minutes=0,
                studio="",
                studio_japanese="",
                director="",
                series="",
                models=[],
                tags=[],
                scraped_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"  ❌ Selenium scraping error: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            return None
            
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
            
            # Debug: Show all iframes found
            all_iframes = soup.find_all('iframe')
            print(f"  🔍 Found {len(all_iframes)} total iframes")
            
            # Try multiple methods to find embed iframe
            
            # Method 1: Look for iframes with metaframe class
            iframes = soup.find_all('iframe', class_=re.compile(r'metaframe'))
            if iframes:
                print(f"  📍 Found {len(iframes)} metaframe iframes")
            
            # Method 2: Look for iframes with known hosts
            if not iframes:
                embed_hosts = ['jav-vids.xyz', 'javggvideo.xyz', 'javstreamhg.xyz', 'streamhg', 'javstream']
                for iframe in all_iframes:
                    iframe_src = iframe.get('src', '') or iframe.get('data-src', '')
                    if iframe_src and any(host in iframe_src.lower() for host in embed_hosts):
                        iframes.append(iframe)
                if iframes:
                    print(f"  📍 Found {len(iframes)} iframes with known hosts")
            
            # Method 3: Look for any iframe with src
            if not iframes:
                iframes = [iframe for iframe in all_iframes if iframe.get('src') or iframe.get('data-src')]
                if iframes:
                    print(f"  📍 Found {len(iframes)} iframes with src")
            
            # Extract embed URL from found iframes
            for iframe in iframes:
                iframe_src = iframe.get('src', '') or iframe.get('data-src', '')
                if iframe_src:
                    # Skip non-video iframes (ads, social media, etc.)
                    skip_patterns = ['facebook', 'twitter', 'instagram', 'google', 'doubleclick', 'ads']
                    if any(pattern in iframe_src.lower() for pattern in skip_patterns):
                        continue
                    
                    # Make URL absolute if needed
                    if iframe_src.startswith('//'):
                        iframe_src = 'https:' + iframe_src
                    elif iframe_src.startswith('/'):
                        iframe_src = 'https://javgg.net' + iframe_src
                    
                    embed_url = iframe_src
                    print(f"  ✅ Embed URL: {embed_url[:80]}...")
                    break
            
            if not embed_url:
                print(f"  ❌ No embed URL found")
                
                # Debug: Check page title and URL to see if we're on the right page
                page_title = soup.find('title')
                if page_title:
                    print(f"  🔍 Page title: {page_title.text[:80]}")
                
                current_url = self.driver.current_url
                print(f"  🔍 Current URL: {current_url}")
                
                # Check if we got redirected or blocked
                if current_url != video_url and not current_url.startswith(video_url):
                    print(f"  ⚠️ Page was redirected - may be blocked or video removed")
                
                # Check for common block/error messages
                page_text = soup.get_text().lower()
                if 'not found' in page_text or '404' in page_text:
                    print(f"  ⚠️ Video appears to be removed (404)")
                elif 'access denied' in page_text or 'forbidden' in page_text:
                    print(f"  ⚠️ Access denied - may be geo-blocked")
                elif 'cloudflare' in page_text and 'checking' in page_text:
                    print(f"  ⚠️ Still stuck on Cloudflare check")
                
                # Debug: Save page source
                debug_file = os.path.join(self.download_dir, f"{code}_no_embed.html")
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"  💾 Saved page source to {debug_file} for debugging")
                
                # Show iframe details for debugging
                if all_iframes:
                    print(f"  🔍 Debug - All iframes found:")
                    for i, iframe in enumerate(all_iframes[:5]):  # Show first 5
                        src = iframe.get('src', '') or iframe.get('data-src', '') or 'NO SRC'
                        iframe_class = iframe.get('class', [])
                        print(f"     [{i+1}] class={iframe_class}, src={src[:60]}...")
                else:
                    # Check for video or script tags that might indicate the player
                    video_tags = soup.find_all('video')
                    script_tags = soup.find_all('script', src=True)
                    
                    if video_tags:
                        print(f"  🔍 Found {len(video_tags)} <video> tags (direct video, not iframe)")
                    
                    if script_tags:
                        player_scripts = [s for s in script_tags if 'player' in s.get('src', '').lower() or 'video' in s.get('src', '').lower()]
                        if player_scripts:
                            print(f"  🔍 Found {len(player_scripts)} player-related scripts")
                            for script in player_scripts[:3]:
                                print(f"     - {script.get('src', '')[:60]}")
                
                return None
            
            # Try to extract M3U8 URL from embed (needed for download)
            print(f"  🔍 Extracting stream URL from embed...")
            
            # Extract M3U8 URL from embed
            m3u8_url = self._extract_m3u8_from_embed(embed_url)
            
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
            
        except Exception as e:
            print(f"  ❌ Selenium scraping error: {str(e)[:100]}")
            return None
    
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
            sys.executable, '-m', 'yt_dlp',
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
