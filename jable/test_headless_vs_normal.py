#!/usr/bin/env python3
"""
Test headless vs non-headless mode to see the difference
"""
import time
from jable_scraper import JableScraper
from bs4 import BeautifulSoup

def test_mode(headless, mode_name):
    """Test a specific mode"""
    print(f"\n{'='*70}")
    print(f"TESTING {mode_name} MODE")
    print('='*70)
    
    scraper = JableScraper(headless=headless)
    
    try:
        scraper._ensure_driver()
        
        # Load page
        url = "https://jable.tv/new/?lang=en"
        print(f"Loading: {url}")
        
        # Use threading timeout
        import threading
        
        load_success = False
        def load_page():
            nonlocal load_success
            try:
                scraper.driver.get(url)
                load_success = True
            except:
                pass
        
        load_thread = threading.Thread(target=load_page)
        load_thread.daemon = True
        load_thread.start()
        load_thread.join(timeout=20)
        
        print(f"Load success: {load_success}")
        
        # Stop page load
        time.sleep(2)
        try:
            scraper.driver.execute_script("window.stop();")
        except:
            pass
        
        # Wait for content
        time.sleep(8)
        
        # Get page source
        page_source = scraper.driver.page_source
        print(f"Page source length: {len(page_source)}")
        
        # Parse
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Check for video containers
        video_containers = soup.find_all('div', class_='video-img-box')
        print(f"Video containers: {len(video_containers)}")
        
        # Check for video links
        video_links = soup.find_all('a', href=lambda x: x and '/videos/' in x)
        print(f"Video links: {len(video_links)}")
        
        # Check page title
        title = scraper.driver.title
        print(f"Page title: {title}")
        
        # Save page source
        filename = f"jable_page_{mode_name.lower().replace(' ', '_')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"Saved to: {filename}")
        
        # Check for specific elements
        body = soup.find('body')
        if body:
            body_classes = body.get('class', [])
            print(f"Body classes: {body_classes}")
        
        # Check for JavaScript errors or blocks
        if 'challenge' in page_source.lower():
            print("⚠️ Challenge detected in page")
        if 'javascript' in page_source.lower() and 'enable' in page_source.lower():
            print("⚠️ JavaScript enable message detected")
        
        return len(video_containers)
        
    finally:
        scraper.close()

if __name__ == "__main__":
    print("="*70)
    print("HEADLESS VS NON-HEADLESS COMPARISON")
    print("="*70)
    
    # Test non-headless
    normal_count = test_mode(False, "NON-HEADLESS")
    
    time.sleep(3)
    
    # Test headless
    headless_count = test_mode(True, "HEADLESS")
    
    # Compare
    print(f"\n{'='*70}")
    print("COMPARISON")
    print('='*70)
    print(f"Non-headless: {normal_count} video containers")
    print(f"Headless:     {headless_count} video containers")
    print(f"Difference:   {normal_count - headless_count}")
    
    if headless_count == 0 and normal_count > 0:
        print("\n❌ ISSUE: Headless mode is not working!")
        print("The site is likely detecting headless mode.")
    elif headless_count == normal_count:
        print("\n✓ Both modes work equally well!")
    else:
        print(f"\n⚠️ Headless mode found fewer videos")
