import os
import requests
from dotenv import load_dotenv

load_dotenv('.env')

api_key = os.getenv('LULUSTREAM_API_KEY')
file_path = '../video.mp4'  # Using full video instead of preview

print("Getting server...")
r = requests.get('https://lulustream.com/api/upload/server', params={'key': api_key}, timeout=30)
server = r.json()['result']
print(f"Server: {server}")

file_size = os.path.getsize(file_path)
print(f"File size: {file_size:,} bytes ({file_size/(1024**3):.2f} GB)")

print("\nUploading (this will take several minutes)...")
with open(file_path, 'rb') as f:
    response = requests.post(
        server,
        files={'file': ('video.mp4', f, 'video/mp4')},
        data={
            'key': api_key,
            'title': 'TEST-VIDEO - Full Video Test',
            'fld_id': 'TEST_UPLOADS'
        },
        timeout=3600  # 1 hour for large file
    )

print(f"\nStatus: {response.status_code}")
print(f"Response length: {len(response.text)}")

try:
    result = response.json()
    print(f"JSON Response: {result}")
except:
    print(f"HTML Response (first 1000 chars):")
    print(response.text[:1000])
    
    # Try to find file code
    import re
    match = re.search(r'file_code["\']?\s*[:=>]\s*["\']?([a-zA-Z0-9]+)', response.text)
    if match:
        code = match.group(1)
        print(f"\nFOUND FILE CODE: {code}")
        print(f"URL: https://lulustream.com/e/{code}")
