"""
Minimal test for Uploady upload to debug the issue
"""
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "6160543vvrw42zvj8g8kx"

# Get upload server
print("Getting upload server...")
r = requests.get(
    "https://uploady.io/api/upload/server",
    params={'key': API_KEY},
    verify=False
)
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")

if r.status_code == 200:
    data = r.json()
    upload_url = data['result']
    sess_id = data['sess_id']
    
    print(f"\nUpload URL: {upload_url}")
    print(f"Session ID: {sess_id}")
    
    # Try minimal upload
    print("\nTrying minimal upload...")
    
    with open("../test.mp4", 'rb') as f:
        files = {'file': ('test.mp4', f, 'video/mp4')}
        
        # Try with just key
        print("\n1. Upload with just 'key' parameter...")
        response = requests.post(
            upload_url,
            files={'file': ('test.mp4', open('../test.mp4', 'rb'), 'video/mp4')},
            data={'key': API_KEY},
            verify=False,
            timeout=300
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        # Try with sess_id
        print("\n2. Upload with 'sess_id' parameter...")
        response = requests.post(
            upload_url,
            files={'file': ('test.mp4', open('../test.mp4', 'rb'), 'video/mp4')},
            data={'sess_id': sess_id},
            verify=False,
            timeout=300
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        # Try with both
        print("\n3. Upload with both 'key' and 'sess_id'...")
        response = requests.post(
            upload_url,
            files={'file': ('test.mp4', open('../test.mp4', 'rb'), 'video/mp4')},
            data={'key': API_KEY, 'sess_id': sess_id},
            verify=False,
            timeout=300
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
