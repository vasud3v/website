import os
import requests
from dotenv import load_dotenv

load_dotenv('.env')
api_key = os.getenv('LULUSTREAM_API_KEY')

print("Checking recent uploads...")
r = requests.get(
    'https://lulustream.com/api/file/list',
    params={'key': api_key, 'per_page': 5},
    timeout=10
)

data = r.json()
print(f"Status: {data.get('status')}")

if data.get('status') == 200:
    result = data.get('result', {})
    if isinstance(result, dict):
        files = result.get('files', [])
    elif isinstance(result, list):
        files = result
    else:
        files = []
    
    print(f"\nFound {len(files)} files:")
    for i, f in enumerate(files, 1):
        print(f"\n{i}. {f.get('title', 'N/A')}")
        print(f"   Code: {f.get('file_code', 'N/A')}")
        print(f"   URL: https://lulustream.com/e/{f.get('file_code', '')}")
        print(f"   Size: {f.get('size', 'N/A')}")
        print(f"   Created: {f.get('created', 'N/A')}")
