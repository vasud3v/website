#!/usr/bin/env python3
"""
Quick diagnostic to check Jable.tv page structure
"""
from seleniumbase import Driver
from bs4 import BeautifulSoup
import time

print("Initializing browser...")
driver = Driver(uc=True, headless=True)

try:
    url = "https://jable.tv/new/?lang=en"
    print(f"Loading: {url}")
    
    driver.get(url)
    time.sleep(5)
    
    # Stop any ongoing loads
    driver.execute_script("window.stop();")
    
    # Scroll
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    print(f"\nPage source length: {len(driver.page_source)}")
    print(f"\nChecking for video elements:")
    print(f"  - div.video-img-box: {len(soup.find_all('div', class_='video-img-box'))}")
    print(f"  - div.video-item: {len(soup.find_all('div', class_='video-item'))}")
    print(f"  - a[href*='/videos/']: {len(soup.find_all('a', href=lambda x: x and '/videos/' in x))}")
    print(f"  - div[class*='video']: {len(soup.find_all('div', class_=lambda x: x and 'video' in str(x).lower()))}")
    
    # Find all divs with class containing 'video'
    video_divs = soup.find_all('div', class_=lambda x: x and 'video' in str(x).lower())
    if video_divs:
        print(f"\nFound {len(video_divs)} divs with 'video' in class:")
        for div in video_divs[:5]:
            print(f"  - {div.get('class')}")
    
    # Find all links
    all_links = soup.find_all('a', href=True)
    video_links = [a['href'] for a in all_links if '/videos/' in a['href']]
    print(f"\nTotal links: {len(all_links)}")
    print(f"Video links: {len(video_links)}")
    if video_links:
        print(f"Sample video links:")
        for link in video_links[:5]:
            print(f"  - {link}")
    
    # Save page source for inspection
    with open('page_source.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"\n✓ Page source saved to page_source.html")
    
finally:
    driver.quit()
    print("\n✓ Browser closed")
