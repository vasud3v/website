import requests
import os
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

api_key = os.getenv("UPLOAD18_API_KEY")

print("Checking Upload18 video status...")
print(f"API Key: {api_key[:10]}...")

# Get my videos
response = requests.get(
    "https://upload18.com/api/myvideo",
    params={'apikey': api_key, 'per_page': 10},
    verify=False,
    timeout=30
)

print(f"\nStatus Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResponse: {data}")
    
    if data.get('status') == 'success':
        videos = data.get('data', [])
        print(f"\nFound {len(videos)} video(s):")
        
        for video in videos:
            vid = video.get('vid', 'N/A')
            did = video.get('did', 'N/A')
            name = video.get('name', 'N/A')
            status = video.get('zt', 0)  # 0=pending, 1=transcoding, 2=done
            status_text = {0: 'Pending', 1: 'Transcoding', 2: 'Done'}.get(status, 'Unknown')
            
            print(f"\n  VID: {vid}")
            print(f"  DID: {did}")
            print(f"  Name: {name}")
            print(f"  Status: {status_text} (zt={status})")
            print(f"  URL: https://upload18.com/{vid}")
            print(f"  Embed: https://upload18.com/embed-{vid}.html")
    else:
        print(f"Error: {data.get('msg', 'Unknown')}")
else:
    print(f"HTTP Error: {response.text[:500]}")
