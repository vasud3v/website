#!/usr/bin/env python3
"""
Diagnostic script for Jable scraper issues
Helps identify why video containers aren't being found
"""

import time
from seleniumbase import Driver
from bs4 import BeautifulSoup

def diagnose_jable():
    """Diagnose Jable.tv scraping issues"""
    
    print("="*70)
    print("JABLE.TV DIAGNOSTIC TOOL")
    print("="*70)
    
    # Initialize browser
    print("\n[1/5] Initializing browser...")
    driver = None
    try:
        driver = Driver(
            uc=True,
            headless=False,  # Use visible browser for diagnosis
            page_load_strategy='eager'
        )
        driver.set_page_load_timeout(30)
        print("✓ Browser initialized")
    except Exception as e:
        print(f"✗ Failed to initialize browser: {e}")
        return
    
    try:
        # Load page
        url = "https://jable.tv/new/?lang=en"
        print(f"\n[2/5] Loading page: {url}")
        
        try:
            driver.get(url)
            time.sleep(5)
            print("✓ Page loaded")
        except Exception as e:
            print(f"⚠ Page load timeout (normal): {e}")
        
        # Stop page load
        try:
            driver.execute_script("window.stop();")
            print("✓ Stopped page load")
        except:
            pass
        
        time.sleep(3)
        
        # Check page title
        print(f"\n[3/5] Checking page content...")
        try:
            title = driver.title
            print(f"✓ Page title: {title}")
        except Exception as e:
            print(f"✗ Could not get title: {e}")
        
        # Get page source
        page_source = driver.page_source
        print(f"✓ Page source length: {len(page_source)} characters")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Check for various elements
        print(f"\n[4/5] Analyzing page structure...")
        
        # Check for video containers
        video_containers = soup.find_all('div', class_='video-img-box')
        print(f"  • video-img-box divs: {len(video_containers)}")
        
        # Check for alternative container classes
        alt_containers = [
            ('div', 'video-item'),
            ('div', 'item'),
            ('div', 'video'),
            ('article', None),
            ('div', 'col'),
        ]
        
        for tag, class_name in alt_containers:
            if class_name:
                elements = soup.find_all(tag, class_=class_name)
                print(f"  • {tag}.{class_name}: {len(elements)}")
            else:
                elements = soup.find_all(tag)
                print(f"  • {tag} tags: {len(elements)}")
        
        # Check for video links
        video_links = soup.find_all('a', href=lambda x: x and '/videos/' in x)
        print(f"  • Links with /videos/: {len(video_links)}")
        
        # Check for cloudflare challenge
        if 'challenge' in page_source.lower() or 'cloudflare' in page_source.lower():
            print(f"\n⚠ WARNING: Cloudflare challenge detected!")
            print(f"  The site may be blocking automated access.")
        
        # Check for JavaScript requirements
        if 'javascript' in page_source.lower() and 'enable' in page_source.lower():
            print(f"\n⚠ WARNING: JavaScript requirement detected!")
        
        # Save page source for inspection
        print(f"\n[5/5] Saving page source for inspection...")
        with open('jable/jable_page_source.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"✓ Saved to: jable/jable_page_source.html")
        
        # Print first 1000 characters of body
        body = soup.find('body')
        if body:
            body_text = body.get_text()[:1000]
            print(f"\n[DEBUG] First 1000 chars of body:")
            print("-" * 70)
            print(body_text)
            print("-" * 70)
        
        # Check for specific Jable elements
        print(f"\n[DEBUG] Looking for Jable-specific elements...")
        
        # Check for main content area
        main_content = soup.find('div', id='list-videos')
        if main_content:
            print(f"✓ Found #list-videos div")
            videos_in_main = main_content.find_all('a', href=lambda x: x and '/videos/' in x)
            print(f"  • Video links inside: {len(videos_in_main)}")
        else:
            print(f"✗ No #list-videos div found")
        
        # Check for section elements
        sections = soup.find_all('section')
        print(f"  • Section tags: {len(sections)}")
        for i, section in enumerate(sections[:3]):
            section_class = section.get('class', [])
            print(f"    - Section {i+1}: {section_class}")
        
        # Final recommendations
        print(f"\n" + "="*70)
        print("DIAGNOSIS COMPLETE")
        print("="*70)
        
        if len(video_containers) == 0 and len(video_links) == 0:
            print("\n❌ PROBLEM: No video content found")
            print("\nPossible causes:")
            print("  1. Cloudflare/anti-bot protection")
            print("  2. Site structure changed")
            print("  3. JavaScript not fully loaded")
            print("  4. IP/region blocking")
            print("\nRecommended actions:")
            print("  1. Check jable_page_source.html manually")
            print("  2. Try with longer wait times")
            print("  3. Try with different user agent")
            print("  4. Try from different IP/VPN")
        else:
            print(f"\n✓ Found {len(video_links)} video links")
            print("\nThe scraper should work. If it's not, try:")
            print("  1. Increase wait times in scraper")
            print("  2. Add more scrolling")
            print("  3. Check for lazy loading")
        
    finally:
        print(f"\n[CLEANUP] Closing browser...")
        if driver:
            try:
                driver.quit()
                print("✓ Browser closed")
            except:
                pass

if __name__ == "__main__":
    diagnose_jable()
