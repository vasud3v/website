"""
Test Upload18 and Uploady uploaders
Diagnose any issues with these hosts
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()


def test_upload18_api():
    """Test Upload18 API connectivity and authentication"""
    print("="*80)
    print("TESTING UPLOAD18")
    print("="*80)
    
    api_key = os.getenv("UPLOAD18_API_KEY")
    email = os.getenv("UPLOAD18_EMAIL")
    username = os.getenv("UPLOAD18_USERNAME")
    
    if not api_key:
        print("✗ UPLOAD18_API_KEY not found in .env")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...")
    print(f"✓ Email: {email}")
    print(f"✓ Username: {username}")
    
    # Test API connectivity
    print("\n📡 Testing API connectivity...")
    
    try:
        # Test getting video list
        response = requests.get(
            "https://upload18.com/api/myvideo",
            params={'apikey': api_key, 'per_page': 5},
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            },
            timeout=30
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data}")
            
            if data.get('status') == 'success':
                print("  ✓ API authentication successful")
                videos = data.get('data', [])
                print(f"  ✓ Found {len(videos)} video(s)")
                return True
            else:
                print(f"  ✗ API error: {data.get('msg', 'Unknown error')}")
                return False
        else:
            print(f"  ✗ HTTP error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ✗ Connection error: {str(e)}")
        return False


def test_uploady_api():
    """Test Uploady API connectivity and authentication"""
    print("\n" + "="*80)
    print("TESTING UPLOADY")
    print("="*80)
    
    api_key = os.getenv("UPLOADY_API_KEY")
    email = os.getenv("UPLOADY_EMAIL")
    username = os.getenv("UPLOADY_USERNAME")
    
    if not api_key:
        print("✗ UPLOADY_API_KEY not found in .env")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...")
    print(f"✓ Email: {email}")
    print(f"✓ Username: {username}")
    
    # Test API connectivity
    print("\n📡 Testing API connectivity...")
    
    try:
        # Test getting upload server
        response = requests.get(
            "https://uploady.io/api/upload/server",
            params={'key': api_key},
            timeout=30,
            verify=False
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data}")
            
            if data.get('status') == 200:
                print("  ✓ API authentication successful")
                upload_url = data.get('result')
                print(f"  ✓ Upload server: {upload_url}")
                return True
            else:
                print(f"  ✗ API error: {data.get('msg', 'Unknown error')}")
                return False
        else:
            print(f"  ✗ HTTP error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ✗ Connection error: {str(e)}")
        return False


def test_host_accessibility():
    """Test if hosts are accessible"""
    print("\n" + "="*80)
    print("TESTING HOST ACCESSIBILITY")
    print("="*80)
    
    hosts = {
        'Upload18': 'https://upload18.com',
        'Uploady': 'https://uploady.io'
    }
    
    results = {}
    
    for name, url in hosts.items():
        print(f"\n[{name}]")
        print(f"  URL: {url}")
        
        try:
            response = requests.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=15,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                print(f"  ✓ Accessible (HTTP {response.status_code})")
                results[name] = True
            else:
                print(f"  ⚠ HTTP {response.status_code}")
                results[name] = False
                
        except requests.exceptions.Timeout:
            print(f"  ✗ Timeout")
            results[name] = False
        except requests.exceptions.ConnectionError:
            print(f"  ✗ Connection error")
            results[name] = False
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")
            results[name] = False
    
    return results


def provide_recommendations(upload18_ok, uploady_ok, accessibility):
    """Provide recommendations based on test results"""
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if upload18_ok and uploady_ok:
        print("\n✓ Both Upload18 and Uploady are working!")
        print("\nYou can use both hosts for uploading.")
        print("\nUsage:")
        print("  python upload_pipeline/upload18_uploader.py <video_file>")
        print("  python upload_pipeline/uploady_uploader.py <video_file>")
        return
    
    if not upload18_ok:
        print("\n⚠ Upload18 Issues:")
        if not accessibility.get('Upload18'):
            print("  - Host not accessible (blocked or down)")
            print("  - Try using VPN")
        else:
            print("  - API authentication failed")
            print("  - Check API key in .env file")
            print("  - Verify account is active")
    
    if not uploady_ok:
        print("\n⚠ Uploady Issues:")
        if not accessibility.get('Uploady'):
            print("  - Host not accessible (blocked or down)")
            print("  - Try using VPN")
        else:
            print("  - API authentication failed")
            print("  - Check API key in .env file")
            print("  - Verify account is active")
    
    print("\n" + "-"*80)
    print("ALTERNATIVE HOSTS (Recommended):")
    print("-"*80)
    
    print("\n✓ StreamWish - Most popular on JAV sites")
    print("  Sign up: https://streamwish.com/")
    print("  Uploader: upload_pipeline/streamwish_uploader.py")
    
    print("\n✓ Turboviplay - Fast and reliable")
    print("  Already configured")
    
    print("\n✓ MixDrop - Good alternative")
    print("  Sign up: https://mixdrop.ag/")
    print("  Uploader: upload_pipeline/mixdrop_uploader.py")


def main():
    print("\n" + "#"*80)
    print("UPLOAD18 & UPLOADY DIAGNOSTIC TEST")
    print("#"*80 + "\n")
    
    # Test accessibility first
    accessibility = test_host_accessibility()
    
    # Test APIs
    upload18_ok = test_upload18_api()
    uploady_ok = test_uploady_api()
    
    # Provide recommendations
    provide_recommendations(upload18_ok, uploady_ok, accessibility)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"\nUpload18: {'✓ Working' if upload18_ok else '✗ Not working'}")
    print(f"Uploady: {'✓ Working' if uploady_ok else '✗ Not working'}")
    
    if upload18_ok or uploady_ok:
        print("\n✓ At least one host is working")
    else:
        print("\n⚠ Neither host is working - use alternative hosts")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
