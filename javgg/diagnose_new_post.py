#!/usr/bin/env python3
"""
Diagnose JavaGG /new-post/ page to see what's actually there
"""

import time
from seleniumbase import Driver
from bs4 import BeautifulSoup

def diagnose_new_post_page():
    """Check what's on the new-post page"""
    
    print("="*70)
    print("DIAGNOSING JAVGG /NEW-POST/ PAGE")
    print("="*70)
    
    driver = Driver(uc=True, headless=False, incognito=True)
    
    try:
        url = "https://javgg.net/new-post/"
        print(f"\n🌐 Loading: {url}")
        driver.get(url)
        
        print("⏳ Waiting 5 seconds for page to load...")
        time.sleep(5)
        
        # Scroll to trigger lazy loading
        print("📜 Scrolling down...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Save page source
        print("\n💾 Saving page source...")
        with open('javgg/new_post_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("  ✅ Saved to: javgg/new_post_page_source.html")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Check for various link patterns
        print("\n" + "="*70)
        print("ANALYZING PAGE STRUCTURE")
        print("="*70)
        
        # 1. Links with /jav/ in href
        jav_links = soup.find_all('a', href=lambda x: x and '/jav/' in x)
        print(f"\n1. Links with '/jav/' in href: {len(jav_links)}")
        if jav_links:
            print("   Sample links:")
            for link in jav_links[:5]:
                print(f"   - {link.get('href')}")
        
        # 2. All links
        all_links = soup.find_all('a', href=True)
        print(f"\n2. Total links on page: {len(all_links)}")
        
        # 3. Links that look like video pages
        video_patterns = ['/jav/', '/video/', '/watch/', '/v/']
        for pattern in video_patterns:
            links = [a for a in all_links if pattern in a.get('href', '')]
            print(f"   - Links with '{pattern}': {len(links)}")
            if links:
                print(f"     Sample: {links[0].get('href')}")
        
        # 4. Check for article/post containers
        print(f"\n3. Looking for post containers...")
        
        # Common container classes
        containers = [
            soup.find_all('article'),
            soup.find_all('div', class_=lambda x: x and 'post' in str(x).lower()),
            soup.find_all('div', class_=lambda x: x and 'item' in str(x).lower()),
            soup.find_all('div', class_=lambda x: x and 'card' in str(x).lower()),
            soup.find_all('div', class_=lambda x: x and 'video' in str(x).lower()),
        ]
        
        for i, container_list in enumerate(containers):
            container_type = ['article', 'post div', 'item div', 'card div', 'video div'][i]
            print(f"   - {container_type}: {len(container_list)}")
            if container_list:
                # Show first container's structure
                first = container_list[0]
                print(f"     Classes: {first.get('class', [])}")
                links_in_container = first.find_all('a', href=True)
                if links_in_container:
                    print(f"     Links in first container: {len(links_in_container)}")
                    print(f"     First link: {links_in_container[0].get('href')}")
        
        # 5. Check for images (thumbnails)
        images = soup.find_all('img')
        print(f"\n4. Images on page: {len(images)}")
        if images:
            print(f"   Sample image src: {images[0].get('src', 'N/A')[:80]}")
        
        # 6. Look for specific classes that might contain videos
        print(f"\n5. Searching for common video listing classes...")
        common_classes = ['post', 'item', 'entry', 'content', 'video', 'thumb', 'card']
        for cls in common_classes:
            elements = soup.find_all(class_=lambda x: x and cls in str(x).lower())
            if elements:
                print(f"   - Elements with '{cls}' in class: {len(elements)}")
        
        # 7. Check page title
        title = soup.find('title')
        print(f"\n6. Page title: {title.text if title else 'N/A'}")
        
        # 8. Check if there's a "no results" or error message
        print(f"\n7. Checking for error messages...")
        error_indicators = ['no results', 'not found', 'error', 'empty']
        page_text = soup.get_text().lower()
        for indicator in error_indicators:
            if indicator in page_text:
                print(f"   ⚠️ Found '{indicator}' in page text")
        
        print("\n" + "="*70)
        print("✅ Diagnosis complete!")
        print("="*70)
        print("\nNext steps:")
        print("1. Check new_post_page_source.html to see the actual HTML")
        print("2. Look for the correct selector pattern")
        print("3. Update complete_workflow.py with the correct selector")
        
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()


if __name__ == '__main__':
    diagnose_new_post_page()
