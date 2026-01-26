"""
Test to check if uploaded file is public and try to make it public
"""
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "6160543vvrw42zvj8g8kx"

# Get file list to check if files are public
print("Getting file list...")
r = requests.get(
    "https://uploady.io/api/file/list",
    params={'key': API_KEY, 'per_page': 5},
    verify=False
)
print(f"Status: {r.status_code}")
print(f"Response: {r.json()}")

# Check the latest uploaded files
if r.status_code == 200:
    data = r.json()
    if data.get('result'):
        print("\nLatest files:")
        for file in data['result'][:3]:
            print(f"  - {file.get('name')} ({file.get('filecode')})")
            print(f"    Status: {file.get('status')}")
            print(f"    Downloads: {file.get('downloads')}")
