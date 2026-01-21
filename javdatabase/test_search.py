"""Test if JAVDatabase search works with video codes"""
from seleniumbase import Driver
from bs4 import BeautifulSoup
import time

def test_search(code):
    print(f"\nTesting search for: {code}")
    
    driver = Driver(uc=True, headless=False)
    
    try:
        # Try different search methods
        
        # Method 1: Search page
        url1 = f"https://www.javdatabase.com/movies/?q={code}"
        print(f"\n1. Search page: {url1}")
        driver.get(url1)
        time.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for movie cards or results
        movie_links = soup.find_all('a', href=lambda x: x and '/movies/' in x and code.lower() in x.lower())
        print(f"   Found {len(movie_links)} matching links")
        for link in movie_links[:3]:
            print(f"   - {link.get('href')}")
        
        # Method 2: Direct URL with code
        url2 = f"https://www.javdatabase.com/movies/{code.lower()}/"
        print(f"\n2. Direct URL: {url2}")
        driver.get(url2)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
            print(f"   Title: {title}")
            if '404' in title or 'not found' in title.lower():
                print("   XX Not found (404)")
            else:
                print("   >> Found!")
                
                # Get actresses
                actress_links = soup.find_all('a', href=lambda x: x and '/idols/' in x)
                print(f"   Actresses: {len(actress_links)}")
                for link in actress_links[:5]:
                    name = link.get_text(strip=True)
                    if name and len(name) > 2:
                        print(f"     - {name}")
        
        # Method 3: Try with hyphen removed
        code_no_hyphen = code.replace('-', '')
        url3 = f"https://www.javdatabase.com/movies/{code_no_hyphen.lower()}/"
        print(f"\n3. No hyphen: {url3}")
        driver.get(url3)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
            print(f"   Title: {title}")
            if '404' not in title and 'not found' not in title.lower():
                print("   >> Found!")
        
    finally:
        input("\nPress Enter to close...")
        driver.quit()

if __name__ == "__main__":
    # Test with codes from your Jable database
    test_codes = ["MIDA-486", "MIDA-334", "VRKM-01747"]
    
    for code in test_codes:
        test_search(code)
        print("\n" + "="*60)
