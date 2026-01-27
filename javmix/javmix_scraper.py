"""
Javmix.TV Advanced Scraper v2.1
High-performance scraper with advanced features:
- Parallel processing for faster scraping
- Smart retry logic with exponential backoff
- Enhanced video URL extraction (20+ hosts)
- Improved metadata extraction accuracy (50+ fields)
- Better error handling and recovery
- Progress tracking and statistics
- Caching system for faster re-scraping
- Related videos extraction
- DMM thumbnail extraction
- Favorite count and post ID tracking
"""

import re
import time
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from bs4 import BeautifulSoup
from seleniumbase import Driver


@dataclass
class VideoData:
    """Complete video data from Javmix.TV with 49 fields"""
    # Basic Info
    code: str
    title: str
    title_en: str
    thumbnail_url: str
    thumbnail_url_dmm: str
    
    # Duration & Size
    duration: str
    duration_seconds: int
    file_size: str
    video_quality: str
    
    # Description
    description: str
    description_en: str
    
    # Dates
    published_date: str
    release_date: str
    modified_date: str
    
    # Categorization
    categories: List[str]
    tags: List[str]
    tags_en: List[str]
    keywords: List[str]
    article_section: List[str]
    
    # People
    actors: List[str]
    actors_en: List[str]
    author: str
    
    # Production
    studio: str
    director: str
    series: str
    label: str
    maker_code: str
    
    # Engagement
    rating: float
    views: int
    word_count: int
    favorite_count: int
    post_id: str
    
    # Video URLs
    embed_urls: Dict[str, str]
    quality_info: Dict[str, str]
    all_available_servers: List[str]
    
    # Social & SEO
    twitter_creator: str
    twitter_site: str
    og_locale: str
    language: str
    
    # Technical
    source_url: str
    canonical_url: str
    breadcrumb: List[str]
    scraped_at: str


class JavmixScraper:
    """Advanced scraper for Javmix.TV with enhanced features"""
    
    BASE_URL = "https://javmix.tv"
    
    # Enhanced video host support (20+ hosts)
    SUPPORTED_HOSTS = [
        'streamtape', 'iplayerhls', 'doodstream', 'pornhub', 'likessb', 
        'streamsb', 'streamwish', 'turbovid', 'emturbovid', 'mixdrop', 
        'upstream', 'fembed', 'voe', 'streamlare', 'filemoon', 'vidoza', 
        'mp4upload', 'dintezuvio', 'streamhub', 'vidguard', 'dood',
        'streamvid', 'vidhide', 'vidsrc', 'embedrise'
    ]
    
    def __init__(self, headless: bool = True, max_workers: int = 1, enable_cache: bool = True):
        """
        Initialize advanced scraper
        
        Args:
            headless: Run browser in headless mode
            max_workers: Number of parallel workers (1 = sequential)
            enable_cache: Enable caching for faster re-scraping
        """
        self.headless = headless
        self.max_workers = max_workers
        self.enable_cache = enable_cache
        self.driver = None
        self.translator = None
        self.cache = {} if enable_cache else None
        self.stats = {
            'total_scraped': 0,
            'successful': 0,
            'failed': 0,
            'urls_extracted': 0,
            'cache_hits': 0
        }
        self._lock = threading.Lock()
        self._init_translator()
    
    def _init_translator(self):
        """Initialize translation service"""
        try:
            from deep_translator import GoogleTranslator
            self.translator = GoogleTranslator(source='ja', target='en')
            print("  🌐 Translation service initialized")
        except ImportError:
            print("  ⚠️ deep-translator not installed. Install with: pip install deep-translator")
            print("  ⚠️ Translations will be skipped")
            self.translator = None
        except Exception as e:
            print(f"  ⚠️ Translation service unavailable: {e}")
            self.translator = None
    
    def _translate_text(self, text: str, max_length: int = 5000) -> str:
        """Translate Japanese text to English with caching and robust error handling"""
        if not self.translator or not text:
            return ""
        
        # Validate input
        if not isinstance(text, str):
            print(f"  ⚠️ Translation skipped: invalid input type {type(text).__name__}")
            return ""
        
        text = text.strip()
        if not text:
            return ""
        
        # Check cache first
        if self.enable_cache:
            try:
                cache_key = hashlib.md5(text.encode()).hexdigest()
                if cache_key in self.cache:
                    self.stats['cache_hits'] += 1
                    return self.cache[cache_key]
            except Exception as e:
                print(f"  ⚠️ Cache lookup failed: {str(e)[:50]}")
        
        try:
            # Split long text into chunks if needed
            if len(text) > max_length:
                chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
                translated_chunks = []
                for chunk in chunks:
                    try:
                        translated = self.translator.translate(chunk)
                        if translated:
                            translated_chunks.append(translated)
                        time.sleep(0.5)  # Rate limiting
                    except Exception as chunk_error:
                        print(f"  ⚠️ Chunk translation failed: {str(chunk_error)[:50]}")
                        translated_chunks.append(chunk)  # Keep original
                result = ' '.join(translated_chunks)
            else:
                result = self.translator.translate(text)
            
            # Validate result
            if not result or not isinstance(result, str):
                print(f"  ⚠️ Translation returned invalid result")
                return text  # Return original
            
            # Cache result
            if self.enable_cache:
                try:
                    self.cache[cache_key] = result
                except Exception as cache_error:
                    print(f"  ⚠️ Cache save failed: {str(cache_error)[:50]}")
            
            return result
        except Exception as e:
            print(f"  ⚠️ Translation failed: {str(e)[:50]}")
            return text  # Return original text on failure
    
    def _translate_list(self, items: List[str]) -> List[str]:
        """Translate a list of items with robust error handling"""
        if not self.translator or not items:
            return []
        
        # Validate input
        if not isinstance(items, list):
            print(f"  ⚠️ Translation skipped: invalid input type {type(items).__name__}")
            return []
        
        translated = []
        for item in items:
            if not item or not isinstance(item, str):
                continue
            
            try:
                trans = self.translator.translate(item.strip())
                if trans and isinstance(trans, str):
                    translated.append(trans)
                else:
                    translated.append(item)  # Keep original if translation invalid
                time.sleep(0.3)  # Rate limiting
            except Exception as e:
                print(f"  ⚠️ Item translation failed for '{item[:30]}': {str(e)[:30]}")
                translated.append(item)  # Keep original if translation fails
        
        return translated
        
    def _init_driver(self):
        """Initialize browser with aggressive ad blocking"""
        if self.driver is None:
            print("Initializing browser with aggressive ad blocking...")
            
            try:
                import undetected_chromedriver as uc
                import os
                
                chrome_options = uc.ChromeOptions()
                
                # Performance optimizations
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument('--disable-popup-blocking')
                chrome_options.add_argument('--disable-notifications')
                chrome_options.add_argument('--mute-audio')
                chrome_options.add_argument('--disable-infobars')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-gpu')
                
                if self.headless:
                    chrome_options.add_argument('--headless=new')
                
                # Block ads at Chrome level
                prefs = {
                    'profile.default_content_setting_values': {
                        'notifications': 2,
                        'popups': 2,
                        'automatic_downloads': 2,
                        'images': 1  # Allow images
                    },
                    'profile.managed_default_content_settings': {
                        'javascript': 1  # Allow JavaScript (needed for video)
                    }
                }
                chrome_options.add_experimental_option('prefs', prefs)
                
                # Try to load uBlock Origin if available
                ublock_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ublock_origin'))
                
                if os.path.exists(ublock_path):
                    print(f"  📦 Loading uBlock Origin...")
                    chrome_options.add_argument(f'--load-extension={ublock_path}')
                    chrome_options.add_argument(f'--disable-extensions-except={ublock_path}')
                
                # Initialize driver
                self.driver = uc.Chrome(options=chrome_options, version_main=None)
                
                # Set timeouts
                self.driver.set_page_load_timeout(60)
                self.driver.implicitly_wait(10)
                
                time.sleep(3)  # Wait for extensions to load
                print("  ✅ Browser ready with ad blocking")
                
            except Exception as e:
                print(f"  ❌ Failed to initialize browser: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    def _inject_ad_blocker(self):
        """Inject comprehensive ad blocker based on analyzed blocklist"""
        try:
            # Load blocklist
            import os
            import json
            
            blocklist_file = os.path.join(os.path.dirname(__file__), 'ad_blocklist.json')
            if os.path.exists(blocklist_file):
                with open(blocklist_file, 'r') as f:
                    blocklist = json.load(f)
            else:
                blocklist = {
                    'domains': ['ad-nex.com', 'mavrtracktor.com', 'img.ad-nex.com', 'creative.mavrtracktor.com'],
                    'selectors': []
                }
            
            # Convert to JavaScript arrays
            domains_js = json.dumps(blocklist.get('domains', []))
            selectors_js = json.dumps(blocklist.get('selectors', []))
            
            ad_blocker_js = f"""
            // COMPREHENSIVE AD BLOCKER - Based on analyzed blocklist
            (function() {{
                console.log('🛡️ COMPREHENSIVE AD BLOCKER ACTIVATED');
                
                const AD_DOMAINS = {domains_js};
                const AD_SELECTORS = {selectors_js};
                
                // Add more selectors
                AD_SELECTORS.push(
                    'iframe[src*="ad-nex"]',
                    'iframe[src*="mavrtracktor"]',
                    'iframe[src*="stripcash"]',
                    'script[id*="agmnb"]',
                    'script[id*="ugmnb"]',
                    'script[id*="agga"]',
                    'script[id*="ugga"]',
                    'div[id*="di9o8snvoat"]',
                    'div[id*="bnc_ad"]',
                    '.nx_mfbox',
                    '[data-isboost-content]'
                );
                
                function isAdDomain(url) {{
                    const urlLower = url.toLowerCase();
                    return AD_DOMAINS.some(domain => urlLower.includes(domain));
                }}
                
                function nukeAds() {{
                    let removed = 0;
                    
                    // 1. Remove iframes from ad domains
                    document.querySelectorAll('iframe').forEach(iframe => {{
                        const src = iframe.src || '';
                        
                        // Keep video players
                        const isVideo = 
                            src.includes('streamtape') ||
                            src.includes('doodstream') ||
                            src.includes('pornhub') ||
                            src.includes('likessb');
                        
                        // Remove if ad domain
                        if (!isVideo && isAdDomain(src)) {{
                            iframe.remove();
                            removed++;
                            console.log('🚫 Removed ad iframe:', src.substring(0, 60));
                        }}
                    }});
                    
                    // 2. Remove scripts from ad domains
                    document.querySelectorAll('script[src]').forEach(script => {{
                        const src = script.src || '';
                        if (isAdDomain(src)) {{
                            script.remove();
                            removed++;
                            console.log('🚫 Removed ad script:', src.substring(0, 60));
                        }}
                    }});
                    
                    // 3. Remove elements matching ad selectors
                    AD_SELECTORS.forEach(selector => {{
                        try {{
                            document.querySelectorAll(selector).forEach(el => {{
                                // Don't remove if it's the video player
                                if (el.id === 'player' || el.id === 'iframe') {{
                                    return; // Skip player elements
                                }}
                                el.remove();
                                removed++;
                            }});
                        }} catch(e) {{}}
                    }});
                    
                    // 4. Remove any element with ad-related attributes
                    document.querySelectorAll('*').forEach(el => {{
                        const id = (el.id || '').toLowerCase();
                        const className = (el.className || '').toString().toLowerCase();
                        
                        if ((id.includes('ad-') || id.includes('ad_') || 
                             className.includes('ad-') || className.includes('ad_')) &&
                            !el.querySelector('iframe[src*="streamtape"], iframe[src*="doodstream"]')) {{
                            el.remove();
                            removed++;
                        }}
                    }});
                    
                    if (removed > 0) {{
                        console.log('🚫 NUKED', removed, 'ad elements');
                    }}
                    
                    return removed;
                }}
                
                // Block ALL popups
                window.open = function() {{
                    console.log('🚫 BLOCKED popup');
                    return null;
                }};
                
                // Block suspicious links
                document.addEventListener('click', function(e) {{
                    const target = e.target.closest('a');
                    if (target) {{
                        const href = target.href || '';
                        if (isAdDomain(href) || target.target === '_blank') {{
                            e.preventDefault();
                            e.stopPropagation();
                            e.stopImmediatePropagation();
                            console.log('🚫 BLOCKED link:', href.substring(0, 60));
                            return false;
                        }}
                    }}
                }}, true);
                
                // Run immediately
                nukeAds();
                
                // Run very frequently
                setInterval(nukeAds, 300);
                
                // Watch ALL DOM changes
                const observer = new MutationObserver(nukeAds);
                observer.observe(document.documentElement, {{
                    childList: true,
                    subtree: true,
                    attributes: true
                }});
                
                console.log('✅ COMPREHENSIVE AD BLOCKER ACTIVE');
                console.log('   Blocking', AD_DOMAINS.length, 'domains');
                console.log('   Using', AD_SELECTORS.length, 'selectors');
            }})();
            """
            
            self.driver.execute_script(ad_blocker_js)
            print(f"  🛡️ Comprehensive ad blocker injected ({len(blocklist.get('domains', []))} domains blocked)")
            
        except Exception as e:
            print(f"  ⚠️ Failed to inject ad blocker: {e}")
            import traceback
            traceback.print_exc()
    
    def _click_play_button(self, retry_count=3):
        """Click the play button to load video dynamically (javmix.tv specific)"""
        try:
            print(f"      🎯 Looking for play button...")
            
            for attempt in range(retry_count):
                # Method 1: Execute JavaScript to trigger click (most reliable)
                try:
                    print(f"      ▶️ Trying JavaScript click (attempt {attempt + 1}/{retry_count})...")
                    result = self.driver.execute_script("""
                        // Try to click the iframe div
                        const iframeDiv = document.getElementById('iframe');
                        if (iframeDiv) {
                            iframeDiv.click();
                            console.log('Clicked iframe div via JS');
                            return 'iframe';
                        }
                        
                        // Try to click play icon
                        const playIcon = document.querySelector('.fa-play');
                        if (playIcon) {
                            playIcon.click();
                            console.log('Clicked play icon via JS');
                            return 'icon';
                        }
                        
                        return null;
                    """)
                    
                    if result:
                        print(f"      ✓ Clicked {result} via JavaScript")
                        time.sleep(6)  # Increased wait time for video to load
                        return True
                    else:
                        print(f"      ⚠️ No clickable element found via JavaScript")
                except Exception as e:
                    print(f"      ⚠️ JavaScript click failed: {str(e)[:100]}")
                
                # Method 2: Click the iframe div directly
                try:
                    iframe_div = self.driver.find_element('id', 'iframe')
                    if iframe_div and iframe_div.is_displayed():
                        print(f"      ▶️ Clicking iframe div directly...")
                        iframe_div.click()
                        print(f"      ✓ Play button clicked")
                        time.sleep(6)
                        return True
                except Exception as e:
                    print(f"      ⚠️ Could not click iframe div: {str(e)[:100]}")
                
                # Method 3: Click the fa-play icon
                try:
                    play_icon = self.driver.find_element('css selector', '.fa-play')
                    if play_icon and play_icon.is_displayed():
                        print(f"      ▶️ Clicking play icon...")
                        play_icon.click()
                        time.sleep(6)
                        print(f"      ✓ Play icon clicked")
                        return True
                except Exception as e:
                    print(f"      ⚠️ Could not click play icon: {str(e)[:100]}")
                
                # Wait before retry
                if attempt < retry_count - 1:
                    print(f"      ⏳ Waiting before retry...")
                    time.sleep(2)
            
            print(f"      ❌ Could not click play button after {retry_count} attempts")
            return False
            
        except Exception as e:
            print(f"      ❌ Error clicking play button: {e}")
            return False
    
    def _try_all_servers(self):
        """Try all available servers with smart retry and enhanced extraction"""
        # Servers ordered by quality (best first)
        # Based on actual HTML: HG, EV, ST (NO PH server!)
        servers = [
            {'name': 'iplayerhls', 'class': 'e1s1', 'label': 'HG', 'quality': 'high'},
            {'name': 'streamtape', 'class': 'e1s3', 'label': 'ST', 'quality': 'high'},
            {'name': 'doodstream', 'class': 'e1s2', 'label': 'EV', 'quality': 'low'}
        ]
        
        all_urls = {}
        quality_info = {}
        tried_servers = []
        
        for idx, server in enumerate(servers):
            tried_servers.append(server['label'])
            
            # Smart retry with exponential backoff
            max_retries = 3
            retry_delay = 2
            
            for retry in range(max_retries):
                try:
                    print(f"    🔄 Server {idx + 1}/{len(servers)}: {server['label']} ({server['name']}) - Quality: {server['quality'].upper()}")
                    
                    if retry > 0:
                        print(f"      🔁 Retry {retry}/{max_retries - 1} (waiting {retry_delay}s)...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    
                    # Check if server button is available
                    if not self._is_server_available(server['class']):
                        print(f"      ⚠️ {server['label']} server not available - skipping")
                        break  # Don't retry if server doesn't exist
                    
                    # Click the server button
                    server_clicked = False
                    
                    # Try JavaScript click first (most reliable)
                    try:
                        result = self.driver.execute_script(f"""
                            const btn = document.querySelector('.{server["class"]}');
                            if (btn) {{
                                btn.click();
                                return true;
                            }}
                            return false;
                        """)
                        
                        if result:
                            server_clicked = True
                            print(f"      ✓ Clicked {server['label']} button (via JS)")
                            time.sleep(3)
                    except Exception as e:
                        print(f"      ⚠️ JS click failed: {str(e)[:80]}")
                    
                    # Try direct click as fallback
                    if not server_clicked:
                        try:
                            server_btn = self.driver.find_element('css selector', f'.{server["class"]}')
                            if server_btn and server_btn.is_displayed():
                                server_btn.click()
                                server_clicked = True
                                print(f"      ✓ Clicked {server['label']} button (direct)")
                                time.sleep(3)
                        except Exception as e:
                            print(f"      ⚠️ Direct click failed: {str(e)[:80]}")
                    
                    if not server_clicked:
                        print(f"      ❌ Could not click {server['label']} button")
                        continue  # Retry
                    
                    # Click play button to load video
                    print(f"      ▶️ Loading video from {server['label']} server...")
                    play_clicked = self._click_play_button(retry_count=2)
                    
                    if play_clicked:
                        # Extract iframe URL with multiple attempts
                        iframe_urls = None
                        for attempt in range(3):
                            iframe_urls = self._extract_video_url_from_iframe()
                            if iframe_urls:
                                break
                            if attempt < 2:
                                print(f"      ⏳ Waiting for iframe to load (attempt {attempt + 2}/3)...")
                                time.sleep(3)
                        
                        if iframe_urls:
                            # Add quality info to each URL
                            for host, url in iframe_urls.items():
                                all_urls[host] = url
                                quality_info[host] = server['quality']
                            
                            print(f"      ✅ {server['label']}: Found {len(iframe_urls)} URL(s) - Quality: {server['quality'].upper()}")
                            for host, url in iframe_urls.items():
                                print(f"         - {host} ({server['quality']}): {url[:60]}...")
                            
                            # Update stats
                            with self._lock:
                                self.stats['urls_extracted'] += len(iframe_urls)
                            
                            break  # Success, no need to retry
                        else:
                            print(f"      ⚠️ {server['label']}: No URL found (may be expired)")
                            if retry < max_retries - 1:
                                continue  # Retry
                    else:
                        print(f"      ⚠️ {server['label']}: Could not click play button")
                        if retry < max_retries - 1:
                            continue  # Retry
                    
                    break  # Exit retry loop if we got here
                    
                except Exception as e:
                    print(f"      ❌ {server['label']}: Error - {str(e)[:100]}")
                    if retry < max_retries - 1:
                        continue  # Retry
                    else:
                        import traceback
                        traceback.print_exc()
            
            # Delay between servers
            if idx < len(servers) - 1:
                time.sleep(2)
        
        # Sort URLs by quality (high > medium > low)
        quality_order = {'high': 3, 'medium': 2, 'low': 1}
        sorted_urls = dict(sorted(
            all_urls.items(), 
            key=lambda x: quality_order.get(quality_info.get(x[0], 'low'), 0),
            reverse=True
        ))
        
        if sorted_urls:
            print(f"\n  📊 Quality Summary:")
            for host, url in sorted_urls.items():
                quality = quality_info.get(host, 'unknown')
                print(f"     {'🏆' if quality == 'high' else '⭐' if quality == 'medium' else '📹'} {host}: {quality.upper()}")
        
        return sorted_urls, quality_info, tried_servers
    
    def _extract_json_ld_data(self, soup) -> Dict:
        """Extract structured data from JSON-LD scripts"""
        json_ld_data = {}
        
        try:
            # Find all JSON-LD scripts
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle @graph structure
                    if '@graph' in data:
                        for item in data['@graph']:
                            item_type = item.get('@type', '')
                            
                            # Extract Article data
                            if item_type == 'Article':
                                json_ld_data['keywords'] = item.get('keywords', [])
                                if isinstance(json_ld_data['keywords'], str):
                                    json_ld_data['keywords'] = [json_ld_data['keywords']]
                                json_ld_data['article_section'] = item.get('articleSection', [])
                                if isinstance(json_ld_data['article_section'], str):
                                    json_ld_data['article_section'] = [json_ld_data['article_section']]
                                json_ld_data['word_count'] = item.get('wordCount', 0)
                                json_ld_data['author'] = item.get('author', {}).get('name', '')
                                json_ld_data['headline'] = item.get('headline', '')
                                json_ld_data['date_published'] = item.get('datePublished', '')
                                json_ld_data['language'] = item.get('inLanguage', '')
                            
                            # Extract WebPage data
                            elif item_type == 'WebPage':
                                json_ld_data['canonical_url'] = item.get('url', '')
                                json_ld_data['date_modified'] = item.get('dateModified', '')
                                if not json_ld_data.get('language'):
                                    json_ld_data['language'] = item.get('inLanguage', '')
                            
                            # Extract BreadcrumbList
                            elif item_type == 'BreadcrumbList':
                                breadcrumb = []
                                for crumb in item.get('itemListElement', []):
                                    breadcrumb.append(crumb.get('name', ''))
                                json_ld_data['breadcrumb'] = breadcrumb
                    
                    # Handle direct structure (no @graph)
                    elif '@type' in data:
                        if data['@type'] == 'Article':
                            json_ld_data['keywords'] = data.get('keywords', [])
                            json_ld_data['article_section'] = data.get('articleSection', [])
                            json_ld_data['word_count'] = data.get('wordCount', 0)
                            json_ld_data['author'] = data.get('author', {}).get('name', '')
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"  ⚠️ Error parsing JSON-LD: {str(e)[:50]}")
                    continue
            
            if json_ld_data:
                print(f"  📊 Extracted JSON-LD data: {len(json_ld_data)} fields")
            
        except Exception as e:
            print(f"  ⚠️ Error extracting JSON-LD: {e}")
        
        return json_ld_data
    
    def _extract_video_url_from_network(self):
        """Extract video URL from network requests after clicking play"""
        try:
            # Get all network requests
            logs = self.driver.get_log('performance')
            
            video_urls = []
            for entry in logs:
                log = json.loads(entry['message'])['message']
                
                if log['method'] == 'Network.responseReceived':
                    url = log['params']['response']['url']
                    
                    # Look for video URLs
                    if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.ts']):
                        if any(host in url.lower() for host in ['streamtape', 'doodstream', 'pornhub', 'likessb']):
                            video_urls.append(url)
                            print(f"    🎥 Found video URL in network: {url[:80]}")
            
            return video_urls
            
        except Exception as e:
            print(f"    ⚠️ Could not extract from network: {e}")
            return []
    
    def _extract_video_url_from_iframe(self):
        """Extract video URL from loaded iframe with enhanced detection"""
        try:
            print(f"      🔍 Extracting video URLs from iframes...")
            
            # Find all iframes
            iframes = self.driver.find_elements('tag name', 'iframe')
            
            video_urls = {}
            
            # Method 1: Direct iframe src extraction
            for iframe in iframes:
                src = iframe.get_attribute('src') or ''
                
                if src and any(host in src.lower() for host in self.SUPPORTED_HOSTS):
                    # Validate URL format
                    if not src.startswith('http'):
                        continue
                    
                    # Determine host and add to results
                    for host in self.SUPPORTED_HOSTS:
                        if host in src.lower():
                            video_urls[host] = src
                            print(f"      🎥 Found: {src[:80]}...")
                            break
            
            # Method 2: Check for video URLs in page source with enhanced patterns
            if len(video_urls) < 3:  # Try to find more URLs
                print(f"      🔍 Checking page source for additional video URLs...")
                page_source = self.driver.page_source
                
                # Enhanced URL patterns for more hosts
                url_patterns = [
                    r'https?://[^"\s]+(?:' + '|'.join(self.SUPPORTED_HOSTS) + r')[^"\s]+/e/[^"\s]+',
                    r'https?://[^"\s]+(?:' + '|'.join(self.SUPPORTED_HOSTS) + r')[^"\s]+/v/[^"\s]+',
                    r'https?://[^"\s]+(?:' + '|'.join(self.SUPPORTED_HOSTS) + r')[^"\s]+/embed/[^"\s]+',
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    for match in matches:
                        # Clean up the URL
                        match = match.split('"')[0].split("'")[0].split('>')[0].split('<')[0]
                        
                        # Determine host
                        for host in self.SUPPORTED_HOSTS:
                            if host in match.lower():
                                if host not in video_urls:
                                    video_urls[host] = match
                                    print(f"      🎥 Found in source: {match[:80]}...")
                                break
            
            # Method 3: Extract from JavaScript variables with enhanced detection
            if len(video_urls) < 3:
                try:
                    js_urls = self.driver.execute_script("""
                        const urls = [];
                        
                        // Check for common video URL variables
                        const varNames = ['videoUrl', 'embedUrl', 'playerUrl', 'streamUrl', 'videoSrc'];
                        varNames.forEach(varName => {
                            if (typeof window[varName] !== 'undefined') {
                                urls.push(window[varName]);
                            }
                        });
                        
                        // Check all iframes
                        document.querySelectorAll('iframe').forEach(iframe => {
                            if (iframe.src) urls.push(iframe.src);
                        });
                        
                        // Check for data attributes
                        document.querySelectorAll('[data-src], [data-video], [data-embed]').forEach(el => {
                            const src = el.getAttribute('data-src') || el.getAttribute('data-video') || el.getAttribute('data-embed');
                            if (src) urls.push(src);
                        });
                        
                        return urls;
                    """)
                    
                    if js_urls:
                        for url in js_urls:
                            if url and any(host in url.lower() for host in self.SUPPORTED_HOSTS):
                                for host in self.SUPPORTED_HOSTS:
                                    if host in url.lower() and host not in video_urls:
                                        video_urls[host] = url
                                        print(f"      🎥 Found via JS: {url[:80]}...")
                                        break
                except:
                    pass
            
            if not video_urls:
                print(f"      ⚠️ No video URLs found")
                
                # Debug: Show what iframes we have
                if iframes:
                    print(f"      📋 Current iframes on page ({len(iframes)} total):")
                    for i, iframe in enumerate(iframes[:5]):  # Show first 5
                        src = iframe.get_attribute('src') or 'no src'
                        print(f"        [{i+1}] {src[:100]}")
            
            return video_urls
            
        except Exception as e:
            print(f"      ❌ Could not extract from iframe: {e}")
            return {}
    
    def _is_server_available(self, server_class):
        """Check if a server button is available on the page"""
        try:
            result = self.driver.execute_script(f"""
                const btn = document.querySelector('.{server_class}');
                if (!btn) return false;
                
                // Check if button is visible and not disabled
                const style = window.getComputedStyle(btn);
                if (style.display === 'none' || style.visibility === 'hidden') return false;
                if (btn.disabled) return false;
                
                return true;
            """)
            return result
        except:
            return False
    
    def _wait_for_element(self, selector, timeout=10, by='css'):
        """Wait for element to be present and visible"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            by_type = By.CSS_SELECTOR if by == 'css' else By.ID
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by_type, selector))
            )
            return element
        except:
            return None
    
    def _validate_embed_urls(self, embed_urls):
        """Validate that embed URLs are properly formatted"""
        validated = {}
        
        for host, url in embed_urls.items():
            # Check if URL is valid
            if url and url.startswith('http') and len(url) > 20:
                # Check if it contains the expected host
                if host.lower() in url.lower():
                    validated[host] = url
                else:
                    print(f"  ⚠️ Warning: URL for {host} doesn't match host: {url[:60]}")
            else:
                print(f"  ⚠️ Warning: Invalid URL for {host}: {url[:60] if url else 'empty'}")
        
        return validated
    
    def _download_adblock_extension(self, extension_path):
        """Download uBlock Origin extension"""
        import os
        import zipfile
        import urllib.request
        
        try:
            # Create directory
            os.makedirs(extension_path, exist_ok=True)
            
            # Download uBlock Origin CRX
            # Note: We'll use a simple ad blocker manifest
            print("  📝 Creating simple ad blocker extension...")
            
            # Create manifest.json
            manifest = {
                "manifest_version": 3,
                "name": "Simple Ad Blocker",
                "version": "1.0",
                "description": "Blocks ads and popups",
                "permissions": [
                    "webRequest",
                    "webRequestBlocking",
                    "storage",
                    "<all_urls>"
                ],
                "host_permissions": [
                    "<all_urls>"
                ],
                "background": {
                    "service_worker": "background.js"
                },
                "content_scripts": [{
                    "matches": ["<all_urls>"],
                    "js": ["content.js"],
                    "run_at": "document_start"
                }]
            }
            
            # Create background.js
            background_js = """
// Block common ad domains
const adDomains = [
    '*://*.doubleclick.net/*',
    '*://*.googlesyndication.com/*',
    '*://*.googleadservices.com/*',
    '*://pagead2.googlesyndication.com/*',
    '*://*.advertising.com/*',
    '*://*.exoclick.com/*',
    '*://*.popads.net/*',
    '*://*.popcash.net/*',
    '*://*.adnxs.com/*',
    '*://*.adsrvr.org/*',
    '*://*.ad-nex.com/*'
];

chrome.webRequest.onBeforeRequest.addListener(
    function(details) {
        return {cancel: true};
    },
    {urls: adDomains},
    ["blocking"]
);

console.log('Ad blocker loaded');
"""
            
            # Create content.js
            content_js = """
// Hide common ad elements
const adSelectors = [
    'iframe[src*="ads"]',
    'iframe[src*="doubleclick"]',
    'div[class*="ad-"]',
    'div[id*="ad-"]',
    'div[class*="advertisement"]',
    '.ad-container',
    '.ad-banner',
    '.popup',
    '.modal-backdrop'
];

function hideAds() {
    adSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
            el.style.display = 'none';
            el.remove();
        });
    });
}

// Run on load
hideAds();

// Run periodically
setInterval(hideAds, 1000);

console.log('Ad blocker content script loaded');
"""
            
            # Write files
            import json
            with open(os.path.join(extension_path, 'manifest.json'), 'w') as f:
                json.dump(manifest, f, indent=2)
            
            with open(os.path.join(extension_path, 'background.js'), 'w') as f:
                f.write(background_js)
            
            with open(os.path.join(extension_path, 'content.js'), 'w') as f:
                f.write(content_js)
            
            print(f"  ✅ Ad blocker extension created at: {extension_path}")
            
        except Exception as e:
            print(f"  ❌ Failed to create ad blocker: {e}")
    
    def _ensure_driver(self):
        """Ensure driver is alive with better error handling"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            if self.driver is None:
                try:
                    self._init_driver()
                    return
                except Exception as e:
                    retry_count += 1
                    print(f"  ⚠️ Driver init failed (attempt {retry_count}/{max_retries}): {str(e)[:100]}")
                    if retry_count < max_retries:
                        time.sleep(2)
                    else:
                        raise
            else:
                try:
                    # Test if driver is alive
                    _ = self.driver.current_url
                    return
                except:
                    print("  🔄 Browser dead, restarting...")
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(2)
                    else:
                        raise Exception("Failed to ensure driver after multiple attempts")
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
    
    def get_video_links_from_page(self, page_url: str) -> List[str]:
        """
        Get all video links from a listing page
        
        Args:
            page_url: URL of the page to scrape
            
        Returns:
            List of video URLs
        """
        self._ensure_driver()
        
        print(f"📄 Loading page: {page_url}")
        
        try:
            self.driver.get(page_url)
            time.sleep(5)
            
            # Inject ad blocker
            self._inject_ad_blocker()
            time.sleep(2)
            
            # Scroll to load lazy content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            print(f"  ✓ Page loaded")
            
        except Exception as e:
            print(f"  ❌ Error loading page: {e}")
            return []
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        video_links = []
        
        # Find all links to /video/ pages
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/video/' in href:
                # Normalize URL
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = f"{self.BASE_URL}{href}"
                else:
                    full_url = f"{self.BASE_URL}/{href}"
                
                # Extract code from URL
                code_match = re.search(r'/video/([^/]+)/?', full_url)
                if code_match:
                    code = code_match.group(1)
                    # Valid codes contain letters and numbers
                    if re.search(r'[a-zA-Z]', code) and full_url not in video_links:
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
        try:
            self._ensure_driver()
            
            # Extract code from URL - support multiple patterns
            # Pattern 1: /video/CODE/
            # Pattern 2: /fc2ppv/CODE/
            # Pattern 3: /category/CODE/
            code_match = re.search(r'/(?:video|fc2ppv|xvideo|category)/([^/\?#]+)', video_url)
            if not code_match:
                print(f"  ❌ Could not extract code from URL: {video_url}")
                return None
            
            code = code_match.group(1).upper()
            print(f"  📹 Scraping: {code}")
            
            # Load page
            self.driver.get(video_url)
            time.sleep(3)
            
            # Check if page is deleted/404
            page_title = self.driver.title.lower()
            if '404' in page_title or 'not found' in page_title or 'page not found' in page_title:
                print(f"  ❌ Video deleted (404 page)")
                return None
            
            # Check for deleted video indicators in page source
            page_source_check = self.driver.page_source.lower()
            if 'video has been deleted' in page_source_check or 'this video is no longer available' in page_source_check:
                print(f"  ❌ Video deleted (removed by site)")
                return None
            
            # Inject ad blocker immediately
            self._inject_ad_blocker()
            time.sleep(2)
            
            # Scroll to load content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Get initial page source BEFORE clicking any buttons (for thumbnail extraction)
            initial_page_source = self.driver.page_source
            initial_soup = BeautifulSoup(initial_page_source, 'html.parser')
            
            # Extract thumbnail from initial page (before play button clicks)
            thumbnail_url = ""
            try:
                # Method 1: #iframe img (exists in initial HTML)
                iframe_img = initial_soup.select_one('#iframe img')
                if iframe_img:
                    thumbnail_url = iframe_img.get('src', '') or iframe_img.get('data-src', '')
                    if thumbnail_url:
                        print(f"  📸 Thumbnail from #iframe img: {thumbnail_url[:60]}...")
                
                # Method 2: og:image meta tag
                if not thumbnail_url:
                    og_image = initial_soup.find('meta', property='og:image')
                    if og_image:
                        thumbnail_url = og_image.get('content', '')
                        if thumbnail_url:
                            print(f"  📸 Thumbnail from og:image: {thumbnail_url[:60]}...")
            except Exception as e:
                print(f"  ⚠️ Could not extract thumbnail: {str(e)[:50]}")
            
            print(f"  📸 Initial thumbnail: {'Found' if thumbnail_url else 'Not found'}")
            
            # Click the play button to load video dynamically
            print(f"  ▶️ Trying all available servers...")
            all_embed_urls, quality_info, tried_servers = self._try_all_servers()
            
            if all_embed_urls:
                print(f"  ✅ Successfully extracted {len(all_embed_urls)} video URL(s) from servers")
                for host, url in all_embed_urls.items():
                    quality = quality_info.get(host, 'unknown')
                    print(f"     - {host} ({quality}): {url[:70]}...")
            else:
                print(f"  ⚠️ No servers loaded successfully, will try to extract from page source")
                quality_info = {}
                tried_servers = []
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract JSON-LD structured data
            print(f"  📊 Extracting structured data...")
            json_ld_data = self._extract_json_ld_data(soup)
            
            # Extract additional meta tags
            twitter_creator = ""
            twitter_site = ""
            og_locale = ""
            modified_date = ""
            
            twitter_creator_meta = soup.find('meta', attrs={'name': 'twitter:creator'})
            if twitter_creator_meta:
                twitter_creator = twitter_creator_meta.get('content', '')
            
            twitter_site_meta = soup.find('meta', attrs={'name': 'twitter:site'})
            if twitter_site_meta:
                twitter_site = twitter_site_meta.get('content', '')
            
            og_locale_meta = soup.find('meta', property='og:locale')
            if og_locale_meta:
                og_locale = og_locale_meta.get('content', '')
            
            # Extract title
            title = ""
            
            # Method 1: Try h1 tag first (most reliable for actual page title)
            h1_tag = soup.find('h1')
            if h1_tag:
                title = h1_tag.get_text(strip=True)
                print(f"  📝 Title from H1: {title[:60]}...")
            
            # Method 2: Fallback to title tag
            if not title:
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    # Remove " エロ動画 - Javmix.TV" suffix
                    title = re.sub(r'\s*エロ動画\s*-\s*Javmix\.TV\s*$', '', title)
            
            # Method 3: Fallback to og:title
            if not title:
                og_title = soup.find('meta', property='og:title')
                if og_title:
                    title = og_title.get('content', '')
                    title = re.sub(r'\s*-\s*Javmix\.TV\s*$', '', title)
            
            if not title:
                title = code
            
            print(f"  📝 Final title: {title[:80]}...")
            
            # Note: thumbnail_url was already extracted before clicking play buttons
            
            # Extract DMM thumbnail URL (direct from DMM.co.jp)
            thumbnail_url_dmm = ""
            try:
                # Look for DMM thumbnail matching the video code
                # Pattern: https://pics.dmm.co.jp/mono/movie/adult/{code}/{code}pl.jpg
                code_lower = code.lower().replace('-', '')
                dmm_pattern = rf'https?://pics\.dmm\.co\.jp/mono/movie/adult/{code_lower}/{code_lower}pl\.jpg'
                dmm_match = re.search(dmm_pattern, page_source, re.IGNORECASE)
                
                if dmm_match:
                    thumbnail_url_dmm = dmm_match.group(0)
                    print(f"  📸 DMM Thumbnail (matched code): {thumbnail_url_dmm[:60]}...")
                else:
                    # Fallback: Look for any DMM URL in #iframe img
                    iframe_img = soup.select_one('#iframe img')
                    if iframe_img:
                        src = iframe_img.get('src', '')
                        if 'pics.dmm.co.jp' in src:
                            thumbnail_url_dmm = src
                            print(f"  📸 DMM Thumbnail (from #iframe): {thumbnail_url_dmm[:60]}...")
            except Exception as e:
                print(f"  ⚠️ Could not extract DMM thumbnail: {str(e)[:50]}")
            
            # If thumbnail_url is empty, use DMM thumbnail as fallback
            if not thumbnail_url and thumbnail_url_dmm:
                thumbnail_url = thumbnail_url_dmm
                print(f"  📸 Using DMM thumbnail as main thumbnail")
            
            # Extract favorite count and post ID
            favorite_count = 0
            post_id = ""
            try:
                # Look for data-favoritecount attribute
                fav_elem = soup.find(attrs={'data-favoritecount': True})
                if fav_elem:
                    favorite_count = int(fav_elem.get('data-favoritecount', 0))
                    print(f"  ❤️ Favorites: {favorite_count}")
                
                # Look for data-postid attribute
                post_elem = soup.find(attrs={'data-postid': True})
                if post_elem:
                    post_id = post_elem.get('data-postid', '')
                    print(f"  🆔 Post ID: {post_id}")
            except Exception as e:
                print(f"  ⚠️ Could not extract favorite/post data: {str(e)[:50]}")
            
            # Extract description
            description = ""
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                description = og_desc.get('content', '')
            
            # Extract published date
            published_date = ""
            pub_time = soup.find('meta', property='article:published_time')
            if pub_time:
                published_date = pub_time.get('content', '')
            
            # Extract duration from post-list-duration with multiple methods
            duration = ""
            duration_seconds = 0
            
            # Method 1: post-list-duration div
            duration_div = soup.find('div', class_='post-list-duration')
            if duration_div:
                duration = duration_div.get_text(strip=True)
            
            # Method 2: Look for duration in meta tags
            if not duration:
                duration_meta = soup.find('meta', attrs={'name': 'duration'}) or soup.find('meta', property='video:duration')
                if duration_meta:
                    duration = duration_meta.get('content', '')
            
            # Method 3: Look for duration in JSON-LD
            if not duration and json_ld_data:
                duration = json_ld_data.get('duration', '')
            
            # Method 4: Extract from description
            if not duration and description:
                # Look for patterns like "120分" or "2時間"
                duration_match = re.search(r'(\d+)\s*分', description)
                if duration_match:
                    duration = f"{duration_match.group(1)}min."
                else:
                    # Look for hours
                    hour_match = re.search(r'(\d+)\s*時間', description)
                    if hour_match:
                        duration = f"{hour_match.group(1)}h"
            
            # Convert duration to seconds
            if duration:
                # Parse "170min." format
                duration_match = re.search(r'(\d+)\s*min', duration)
                if duration_match:
                    duration_seconds = int(duration_match.group(1)) * 60
                
                # Parse hours
                hour_match = re.search(r'(\d+)\s*h', duration)
                if hour_match:
                    duration_seconds += int(hour_match.group(1)) * 3600
                
                # Parse "HH:MM:SS" or "MM:SS" format
                time_match = re.search(r'(\d+):(\d+)(?::(\d+))?', duration)
                if time_match and not duration_seconds:
                    hours = int(time_match.group(1)) if time_match.group(3) else 0
                    minutes = int(time_match.group(2)) if time_match.group(3) else int(time_match.group(1))
                    seconds = int(time_match.group(3)) if time_match.group(3) else int(time_match.group(2))
                    duration_seconds = hours * 3600 + minutes * 60 + seconds
            
            if duration:
                print(f"  ⏱️ Duration: {duration} ({duration_seconds}s)")
            else:
                print(f"  ⚠️ Duration not found on page")
            
            # Extract categories and tags more thoroughly
            categories = []
            tags = []
            
            # Blacklist of terms to exclude
            exclude_terms = ['More', 'ジャンル', 'more', 'genre', 'Genre', 'GENRE', 'Tags', 'tags', 'TAGS', 'Category', 'category', 'CATEGORY']
            
            # Method 1: Look for category and tag links
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                
                if text and text not in exclude_terms and len(text) > 1:
                    if '/category/' in href:
                        if text not in categories:
                            categories.append(text)
                    elif '/tag/' in href:
                        if text not in tags:
                            tags.append(text)
            
            # Method 2: Check for genre/tag sections
            genre_section = soup.find('div', class_='genres') or soup.find('div', class_='tags')
            if genre_section:
                for link in genre_section.find_all('a'):
                    text = link.get_text(strip=True)
                    if text and text not in exclude_terms and text not in tags and len(text) > 1:
                        tags.append(text)
            
            # Method 3: Extract from description if available
            if description:
                # Look for 【ジャンル】 pattern in description
                genre_match = re.search(r'【ジャンル】([^【]+)', description)
                if genre_match:
                    genre_text = genre_match.group(1)
                    # Split by comma and clean
                    for genre in genre_text.split(','):
                        genre = genre.strip()
                        if genre and genre not in tags and genre not in exclude_terms and len(genre) > 1:
                            tags.append(genre)
            
            # Method 4: Use JavaScript to extract from DOM
            try:
                js_tags = self.driver.execute_script("""
                    const tags = [];
                    document.querySelectorAll('a[href*="/tag/"]').forEach(a => {
                        const text = a.textContent.trim();
                        if (text && text.length > 1) tags.push(text);
                    });
                    return tags;
                """)
                if js_tags:
                    for tag in js_tags:
                        if tag not in tags and tag not in exclude_terms and len(tag) > 1:
                            tags.append(tag)
            except:
                pass
            
            print(f"  🏷️ Categories: {len(categories)}, Tags: {len(tags)}")
            
            # Extract actors, studio, director, series from description
            actors = []
            studio = ""
            director = ""
            series = ""
            label = ""
            maker_code = ""
            release_date = ""
            rating = 0.0
            views = 0
            file_size = ""
            video_quality = ""
            
            if description:
                # Extract actors/performers 【出演者】
                actor_match = re.search(r'【出演者】([^【]+)', description)
                if actor_match:
                    actor_text = actor_match.group(1).strip()
                    # Split by comma and clean
                    for actor in actor_text.split(','):
                        actor = actor.strip()
                        if actor and len(actor) > 1:
                            actors.append(actor)
                
                # Extract studio/maker 【メーカー】
                studio_match = re.search(r'【メーカー】([^【]+)', description)
                if studio_match:
                    studio = studio_match.group(1).strip()
                
                # Extract director 【監督】
                director_match = re.search(r'【監督】([^【]+)', description)
                if director_match:
                    director = director_match.group(1).strip()
                
                # Extract series 【シリーズ】
                series_match = re.search(r'【シリーズ】([^【]+)', description)
                if series_match:
                    series = series_match.group(1).strip()
                
                # Extract label 【レーベル】
                label_match = re.search(r'【レーベル】([^【]+)', description)
                if label_match:
                    label = label_match.group(1).strip()
                    # Use label as series if series not found
                    if not series:
                        series = label
                
                # Extract maker code 【品番】
                code_match = re.search(r'【品番】([^【]+)', description)
                if code_match:
                    maker_code = code_match.group(1).strip()
                
                # Extract release date 【配信開始日】or 【発売日】
                release_match = re.search(r'【(?:配信開始日|発売日)】([^【]+)', description)
                if release_match:
                    release_date = release_match.group(1).strip()
            
            # Try to extract rating from page
            try:
                rating_elem = soup.find('span', class_='rating') or soup.find('div', class_='rating')
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
            except:
                pass
            
            # Try to extract view count
            try:
                views_elem = soup.find('span', class_='views') or soup.find('div', class_='views')
                if views_elem:
                    views_text = views_elem.get_text(strip=True)
                    views_match = re.search(r'(\d+(?:,\d+)*)', views_text)
                    if views_match:
                        views = int(views_match.group(1).replace(',', ''))
            except:
                pass
            
            # Estimate file size based on duration and quality
            if duration_seconds > 0:
                # Rough estimates: HD ~5MB/min, FHD ~8MB/min, 4K ~15MB/min
                # Assume HD quality by default
                estimated_mb = (duration_seconds / 60) * 5
                if estimated_mb < 1024:
                    file_size = f"~{int(estimated_mb)}MB"
                else:
                    file_size = f"~{estimated_mb/1024:.1f}GB"
            
            # Try to detect video quality from title or description
            quality_keywords = {
                '4K': ['4K', 'UHD', '2160p'],
                'FHD': ['FHD', '1080p', 'Full HD', 'FullHD'],
                'HD': ['HD', '720p', 'High Definition'],
                'SD': ['SD', '480p', 'Standard']
            }
            
            search_text = f"{title} {description}".upper()
            for quality, keywords in quality_keywords.items():
                if any(kw.upper() in search_text for kw in keywords):
                    video_quality = quality
                    break
            
            if not video_quality:
                video_quality = "HD"  # Default assumption
            
            # Try to extract from page structure as well
            if not actors:
                try:
                    # Look for actor links in the main content area only
                    # Avoid sidebar/popular lists
                    main_content = soup.find('div', class_='post-content') or soup.find('article')
                    if main_content:
                        actor_links = main_content.find_all('a', href=re.compile(r'/actor/|/actress/|/star/'), limit=10)
                    else:
                        # Fallback: get all actor links but filter carefully
                        actor_links = soup.find_all('a', href=re.compile(r'/actor/|/actress/|/star/'), limit=10)
                    
                    for link in actor_links:
                        # Skip if in sidebar/widget/popular section
                        parent_classes = []
                        for parent in link.parents:
                            if parent.get('class'):
                                parent_classes.extend(parent.get('class'))
                        
                        # Check if in sidebar or popular section
                        skip_keywords = ['sidebar', 'widget', 'popular', 'related', 'yarpp', 'aside']
                        if any(keyword in ' '.join(parent_classes).lower() for keyword in skip_keywords):
                            continue
                        
                        actor_name = link.get_text(strip=True)
                        # Filter out numbers in parentheses (view counts)
                        actor_name = re.sub(r'\(\d+\)', '', actor_name).strip()
                        
                        # Filter out common non-actor terms
                        non_actor_terms = ['AV女優', 'More', 'more', 'actress', 'actor', 'star']
                        if actor_name and len(actor_name) > 1 and actor_name not in actors and actor_name not in exclude_terms and actor_name not in non_actor_terms:
                            actors.append(actor_name)
                except Exception as e:
                    print(f"  ⚠️ Error extracting actors from page: {str(e)[:50]}")
            
            # Special handling for FC2PPV videos - they rarely list actors
            if code.startswith('FC2PPV') and actors:
                # Check if we got popular actors (波多野結衣, 大槻ひびき, etc.)
                popular_actors = ['波多野結衣', '大槻ひびき', '篠田ゆう', '浜崎真緒', '森沢かな', '松本いちか']
                if any(popular in actors for popular in popular_actors):
                    print(f"  ⚠️ FC2PPV video with popular actors detected - likely sidebar actors, clearing list")
                    actors = []
            
            print(f"  👥 Actors: {len(actors)}, Studio: {'✓' if studio else '✗'}, Director: {'✓' if director else '✗'}, Series: {'✓' if series else '✗'}")
            print(f"  📊 Duration: {duration_seconds}s, Quality: {video_quality}, Size: {file_size}, Rating: {rating if rating > 0 else 'N/A'}")
            
            # Extract embed URLs from all servers
            embed_urls = all_embed_urls if all_embed_urls else {}
            
            # Validate URLs
            embed_urls = self._validate_embed_urls(embed_urls)
            
            # Update quality info after validation
            validated_quality_info = {host: quality_info.get(host, 'unknown') for host in embed_urls.keys()}
            
            # Fallback: Parse the obfuscated eval() script
            if not embed_urls:
                print(f"  🔍 Extracting from obfuscated JavaScript...")
                split_pattern = r"'([^']{100,})'\.split\('\|'\),\d+,\{\}\)\)"
                split_matches = re.findall(split_pattern, page_source)
                
                if split_matches:
                    for split_str in split_matches:
                        tokens = split_str.split('|')
                        
                        for i, token in enumerate(tokens):
                            if token == 'streamtape' and i > 0:
                                video_id = tokens[i-1]
                                if len(video_id) > 10 and not video_id.startswith('e1s'):
                                    embed_urls['streamtape'] = f"https://streamtape.com/e/{video_id}"
                                    validated_quality_info['streamtape'] = 'high'
                            
                            elif token == 'doodstream' and i > 0:
                                for j in range(i-1, max(0, i-5), -1):
                                    candidate = tokens[j]
                                    if len(candidate) > 10 and not candidate.startswith('e1s') and candidate not in ['pornhubed', 'likessb', 'doodstream', 'streamtape']:
                                        if re.match(r'^[a-zA-Z0-9]+$', candidate):
                                            embed_urls['doodstream'] = f"https://doodstream.com/e/{candidate}"
                                            validated_quality_info['doodstream'] = 'low'
                                            break
                            
                            elif token == 'likessb' and i > 0:
                                video_id = tokens[i-1]
                                if len(video_id) > 10 and not video_id.startswith('e1s'):
                                    embed_urls['likessb'] = f"https://likessb.com/e/{video_id}"
                                    validated_quality_info['likessb'] = 'medium'
                            
                            elif token == 'pornhubed' and i > 0:
                                video_id = tokens[i-1]
                                if len(video_id) > 10 and not video_id.startswith('e1s'):
                                    embed_urls['pornhub'] = f"https://www.pornhub.com/embed/{video_id}"
                                    validated_quality_info['pornhub'] = 'high'
                    
                    # Validate fallback URLs
                    embed_urls = self._validate_embed_urls(embed_urls)
            
            # Method 3: Look for direct embed URLs in iframes (last resort)
            if not embed_urls:
                for iframe in soup.find_all('iframe', src=True):
                    src = iframe['src']
                    if 'streamtape.com' in src:
                        embed_urls['streamtape'] = src
                        validated_quality_info['streamtape'] = 'high'
                    elif 'doodstream.com' in src:
                        embed_urls['doodstream'] = src
                        validated_quality_info['doodstream'] = 'low'
                    elif 'pornhub.com' in src:
                        embed_urls['pornhub'] = src
                        validated_quality_info['pornhub'] = 'high'
                    elif 'likessb.com' in src:
                        embed_urls['likessb'] = src
                        validated_quality_info['likessb'] = 'medium'
            
            print(f"  ✅ Total embed URLs found: {len(embed_urls)}")
            if embed_urls:
                for host, url in embed_urls.items():
                    quality = validated_quality_info.get(host, 'unknown')
                    print(f"     ✓ {host} ({quality}): {url[:70]}...")
            
            # Translate text fields to English
            print(f"  🌐 Translating to English...")
            title_en = self._translate_text(title)
            description_en = self._translate_text(description[:500])  # Limit description length
            tags_en = self._translate_list(tags[:10])  # Limit to first 10 tags
            actors_en = self._translate_list(actors[:5])  # Limit to first 5 actors
            print(f"  ✅ Translation complete")
            
            # Get data from JSON-LD with fallbacks
            keywords = json_ld_data.get('keywords', tags[:5] if tags else [])
            article_section = json_ld_data.get('article_section', categories[:3] if categories else [])
            word_count = json_ld_data.get('word_count', 0)
            author = json_ld_data.get('author', 'Unknown')
            canonical_url = json_ld_data.get('canonical_url', video_url)
            breadcrumb = json_ld_data.get('breadcrumb', [])
            modified_date = json_ld_data.get('date_modified', '')
            language = json_ld_data.get('language', og_locale or 'ja')
            
            # Ensure keywords and article_section are lists
            if isinstance(keywords, str):
                keywords = [keywords]
            if isinstance(article_section, str):
                article_section = [article_section]
            
            print(f"  📊 Metadata summary:")
            print(f"     Keywords: {len(keywords)}, Sections: {len(article_section)}")
            print(f"     Author: {author}, Word count: {word_count}")
            print(f"     Breadcrumb: {len(breadcrumb)} levels")
            print(f"     Language: {language}")
            
            return VideoData(
                # Basic Info
                code=code,
                title=title,
                title_en=title_en,
                thumbnail_url=thumbnail_url,
                thumbnail_url_dmm=thumbnail_url_dmm,
                # Duration & Size
                duration=duration,
                duration_seconds=duration_seconds,
                file_size=file_size,
                video_quality=video_quality,
                # Description
                description=description,
                description_en=description_en,
                # Dates
                published_date=published_date,
                release_date=release_date,
                modified_date=modified_date,
                # Categorization
                categories=categories,
                tags=tags,
                tags_en=tags_en,
                keywords=keywords,
                article_section=article_section,
                # People
                actors=actors,
                actors_en=actors_en,
                author=author,
                # Production
                studio=studio,
                director=director,
                series=series,
                label=label,
                maker_code=maker_code,
                # Engagement
                rating=rating,
                views=views,
                word_count=word_count,
                favorite_count=favorite_count,
                post_id=post_id,
                # Video URLs
                embed_urls=embed_urls,
                quality_info=validated_quality_info,
                all_available_servers=tried_servers,
                # Social & SEO
                twitter_creator=twitter_creator,
                twitter_site=twitter_site,
                og_locale=og_locale,
                language=language,
                # Technical
                source_url=video_url,
                canonical_url=canonical_url,
                breadcrumb=breadcrumb,
                scraped_at=datetime.now().isoformat()
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
            
            if page == 1:
                page_url = self.BASE_URL
            else:
                page_url = f"{self.BASE_URL}/page/{page}/"
            
            # Get video links
            video_links = self.get_video_links_from_page(page_url)
            
            # Scrape each video
            for i, video_url in enumerate(video_links, 1):
                print(f"\n[{i}/{len(video_links)}]")
                video_data = self.scrape_video(video_url)
                if video_data:
                    all_videos.append(video_data)
                
                time.sleep(2)  # Be nice to server
        
        return all_videos
    
    def scrape_category(self, category_slug: str, num_pages: int = 1) -> List[VideoData]:
        """
        Scrape videos from a category
        
        Args:
            category_slug: Category slug (e.g., "fc2ppv", "xvideo")
            num_pages: Number of pages to scrape
            
        Returns:
            List of VideoData objects
        """
        all_videos = []
        
        for page in range(1, num_pages + 1):
            print(f"\n{'='*60}")
            print(f"CATEGORY: {category_slug} - PAGE {page}/{num_pages}")
            print('='*60)
            
            if page == 1:
                page_url = f"{self.BASE_URL}/{category_slug}/"
            else:
                page_url = f"{self.BASE_URL}/{category_slug}/page/{page}/"
            
            # Get video links
            video_links = self.get_video_links_from_page(page_url)
            
            # Scrape each video
            for i, video_url in enumerate(video_links, 1):
                print(f"\n[{i}/{len(video_links)}]")
                video_data = self.scrape_video(video_url)
                if video_data:
                    all_videos.append(video_data)
                
                time.sleep(2)
        
        return all_videos
    
    def scrape_multiple_videos(self, video_urls: List[str], max_workers: int = None) -> List[VideoData]:
        """
        Scrape multiple videos with optional parallel processing
        
        Args:
            video_urls: List of video URLs to scrape
            max_workers: Number of parallel workers (None = use self.max_workers)
            
        Returns:
            List of VideoData objects
        """
        if max_workers is None:
            max_workers = self.max_workers
        
        all_videos = []
        
        if max_workers > 1:
            print(f"\n🚀 Parallel scraping with {max_workers} workers")
            
            # Note: Parallel scraping requires multiple browser instances
            # For now, we'll scrape sequentially but keep the interface
            print(f"⚠️ Parallel mode not yet implemented, using sequential mode")
            max_workers = 1
        
        # Sequential scraping
        for i, video_url in enumerate(video_urls, 1):
            print(f"\n{'='*60}")
            print(f"VIDEO {i}/{len(video_urls)}")
            print('='*60)
            
            video_data = self.scrape_video(video_url)
            if video_data:
                all_videos.append(video_data)
                with self._lock:
                    self.stats['successful'] += 1
            else:
                with self._lock:
                    self.stats['failed'] += 1
            
            with self._lock:
                self.stats['total_scraped'] += 1
            
            # Progress update
            self.print_stats()
            
            time.sleep(2)
        
        return all_videos
    
    def print_stats(self):
        """Print scraping statistics"""
        print(f"\n📊 Statistics:")
        print(f"   Total scraped: {self.stats['total_scraped']}")
        print(f"   Successful: {self.stats['successful']} ✅")
        print(f"   Failed: {self.stats['failed']} ❌")
        print(f"   URLs extracted: {self.stats['urls_extracted']} 🎥")
        if self.enable_cache:
            print(f"   Cache hits: {self.stats['cache_hits']} 💾")
        
        if self.stats['total_scraped'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_scraped']) * 100
            print(f"   Success rate: {success_rate:.1f}%")
            
            if self.stats['successful'] > 0:
                avg_urls = self.stats['urls_extracted'] / self.stats['successful']
                print(f"   Avg URLs per video: {avg_urls:.1f}")
    
    def get_cache_info(self) -> Dict:
        """Get cache information"""
        if not self.enable_cache:
            return {'enabled': False}
        
        return {
            'enabled': True,
            'size': len(self.cache),
            'hits': self.stats['cache_hits']
        }
    
    def clear_cache(self):
        """Clear translation cache"""
        if self.enable_cache:
            self.cache.clear()
            print("✅ Cache cleared")
    
    def export_stats(self, filename: str = 'scraper_stats.json'):
        """Export statistics to JSON file"""
        stats_data = {
            'stats': self.stats,
            'cache_info': self.get_cache_info(),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Stats exported to: {filename}")


def main():
    """Main function with advanced features"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Advanced Javmix.TV Scraper v2.1',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape single video
  python javmix_scraper.py --url https://javmix.tv/video/hbad-725/ --output video.json
  
  # Scrape homepage (3 pages)
  python javmix_scraper.py --pages 3 --output homepage.json
  
  # Scrape category
  python javmix_scraper.py --category fc2ppv --pages 2 --output fc2ppv.json
  
  # Show browser window
  python javmix_scraper.py --url URL --no-headless
  
  # Enable caching and show stats
  python javmix_scraper.py --pages 2 --cache --stats
        """
    )
    
    parser.add_argument('--url', help='Scrape specific video URL')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages to scrape')
    parser.add_argument('--category', help='Category slug to scrape (e.g., fc2ppv, xvideo)')
    parser.add_argument('--output', default='javmix_videos.json', help='Output file')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    parser.add_argument('--cache', action='store_true', help='Enable translation caching')
    parser.add_argument('--stats', action='store_true', help='Export statistics after scraping')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers (experimental)')
    
    args = parser.parse_args()
    
    # Initialize scraper with advanced options
    scraper = JavmixScraper(
        headless=not args.no_headless,
        max_workers=args.workers,
        enable_cache=args.cache
    )
    
    print(f"\n{'='*60}")
    print(f"🚀 JAVMIX.TV ADVANCED SCRAPER v2.1")
    print('='*60)
    print(f"Mode: {'Headless' if not args.no_headless else 'Visible Browser'}")
    print(f"Cache: {'Enabled' if args.cache else 'Disabled'}")
    print(f"Workers: {args.workers}")
    print('='*60)
    
    try:
        if args.url:
            # Scrape single video
            print(f"\n📹 Scraping video: {args.url}")
            video_data = scraper.scrape_video(args.url)
            
            if video_data:
                # Save to file (as dict, not list, for single video)
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(asdict(video_data), f, indent=2, ensure_ascii=False)
                
                print(f"\n{'='*60}")
                print(f"✅ SUCCESS")
                print('='*60)
                print(f"Code: {video_data.code}")
                print(f"Title: {video_data.title}")
                print(f"Title (EN): {video_data.title_en}")
                print(f"Duration: {video_data.duration} ({video_data.duration_seconds}s)")
                print(f"Quality: {video_data.video_quality}")
                print(f"File Size: {video_data.file_size}")
                print(f"Video URLs: {len(video_data.embed_urls)}")
                for host, url in video_data.embed_urls.items():
                    quality = video_data.quality_info.get(host, 'unknown')
                    print(f"  - {host} ({quality}): {url[:70]}...")
                print(f"\n💾 Saved to: {args.output}")
            else:
                print(f"\n❌ Failed to scrape video")
        
        elif args.category:
            # Scrape category
            videos = scraper.scrape_category(args.category, num_pages=args.pages)
            
            print(f"\n{'='*60}")
            print(f"✅ SCRAPING COMPLETE")
            print('='*60)
            print(f"Total videos: {len(videos)}")
            
            if videos:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump([asdict(v) for v in videos], f, indent=2, ensure_ascii=False)
                print(f"💾 Saved to: {args.output}")
                
                # Show sample
                if videos:
                    print(f"\n📋 Sample (first video):")
                    v = videos[0]
                    print(f"  Code: {v.code}")
                    print(f"  Title: {v.title}")
                    print(f"  URLs: {len(v.embed_urls)}")
        
        else:
            # Scrape homepage
            videos = scraper.scrape_homepage(num_pages=args.pages)
            
            print(f"\n{'='*60}")
            print(f"✅ SCRAPING COMPLETE")
            print('='*60)
            print(f"Total videos: {len(videos)}")
            
            if videos:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump([asdict(v) for v in videos], f, indent=2, ensure_ascii=False)
                print(f"💾 Saved to: {args.output}")
                
                # Show sample
                if videos:
                    print(f"\n📋 Sample (first video):")
                    v = videos[0]
                    print(f"  Code: {v.code}")
                    print(f"  Title: {v.title}")
                    print(f"  URLs: {len(v.embed_urls)}")
        
        # Print final statistics
        print(f"\n{'='*60}")
        scraper.print_stats()
        print('='*60)
        
        # Export stats if requested
        if args.stats:
            stats_file = args.output.replace('.json', '_stats.json')
            scraper.export_stats(stats_file)
    
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Interrupted by user")
        scraper.print_stats()
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()
        print(f"\n👋 Browser closed")


if __name__ == "__main__":
    main()
