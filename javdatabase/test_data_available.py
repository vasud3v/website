"""Test what data is actually available on JAVDatabase pages"""
from seleniumbase import Driver
from bs4 import BeautifulSoup
import time

def test_movie_page():
    driver = Driver(uc=True, headless=False)
    
    try:
        # Test movie page
        url = "https://www.javdatabase.com/movies/mida-486/"
        print(f"Loading: {url}\n")
        driver.get(url)
        time.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        print("="*60)
        print("MOVIE PAGE - ALL TEXT CONTENT")
        print("="*60)
        
        # Get all text
        text = soup.get_text()
        
        # Print relevant sections
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in [
                'genre', 'director', 'studio', 'release', 'runtime', 
                'duration', 'label', 'series', 'description', 'plot'
            ]):
                print(f"{i}: {line}")
        
        print("\n" + "="*60)
        print("ACTRESS PROFILE PAGE")
        print("="*60)
        
        # Visit actress profile
        actress_url = "https://www.javdatabase.com/idols/ruru-ukawa/"
        print(f"\nLoading: {actress_url}\n")
        driver.get(actress_url)
        time.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text = soup.get_text()
        
        # Print all text
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and len(line) > 2:
                print(f"{i}: {line}")
        
    finally:
        input("\nPress Enter to close...")
        driver.quit()

if __name__ == "__main__":
    test_movie_page()
