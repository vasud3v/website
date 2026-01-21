"""Test JAVDatabase HTML structure"""
from seleniumbase import Driver
from bs4 import BeautifulSoup
import time

def test_movie_page():
    print("Testing JAVDatabase movie page structure...")
    
    driver = Driver(uc=True, headless=False)
    
    try:
        # Test with MIDA-486
        url = "https://www.javdatabase.com/movies/?q=MIDA-486"
        print(f"\nSearching: {url}")
        driver.get(url)
        time.sleep(5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all movie links
        print("\n=== Movie Links ===")
        movie_links = soup.find_all('a', href=True)
        for link in movie_links:
            href = link.get('href', '')
            if '/movies/' in href and '/movies/?_' not in href and href != '/movies/':
                text = link.get_text(strip=True)
                print(f"Link: {href}")
                print(f"Text: {text[:80]}")
                
                # Visit this movie page
                if not href.startswith('http'):
                    href = 'https://www.javdatabase.com' + href
                
                print(f"\nVisiting: {href}")
                driver.get(href)
                time.sleep(4)
                
                soup2 = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Get title
                print("\n=== Title ===")
                h1 = soup2.find('h1')
                if h1:
                    print(f"H1: {h1.get_text(strip=True)}")
                
                # Find all divs with classes
                print("\n=== Main Sections ===")
                divs = soup2.find_all('div', class_=True)
                seen_classes = set()
                for div in divs:
                    classes = ' '.join(div.get('class', []))
                    if classes and classes not in seen_classes:
                        if any(word in classes.lower() for word in ['movie', 'idol', 'cast', 'actor', 'info', 'detail']):
                            seen_classes.add(classes)
                            print(f"\nClass: {classes}")
                            print(f"Content preview: {div.get_text(strip=True)[:100]}")
                
                # Find actress/idol links
                print("\n=== Actress Links ===")
                idol_links = soup2.find_all('a', href=lambda x: x and '/idols/' in x)
                for link in idol_links[:5]:
                    print(f"Href: {link.get('href')}")
                    print(f"Text: {link.get_text(strip=True)}")
                    
                    # Check for images
                    img = link.find('img')
                    if img:
                        print(f"Image: {img.get('src', 'N/A')}")
                
                # Find all images
                print("\n=== All Images ===")
                images = soup2.find_all('img', src=True)
                for img in images[:10]:
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    classes = ' '.join(img.get('class', []))
                    if not any(x in src for x in ['logo', 'flag', 'icon']):
                        print(f"Src: {src[:80]}")
                        print(f"Alt: {alt[:50]}")
                        print(f"Class: {classes}")
                        print()
                
                break  # Only check first movie
                
    finally:
        input("\nPress Enter to close...")
        driver.quit()

if __name__ == "__main__":
    test_movie_page()
