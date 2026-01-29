"""
Test Upload18 only
"""
import os
import sys
from dotenv import load_dotenv
from upload18_uploader import Upload18Uploader

load_dotenv()

if len(sys.argv) < 2:
    print("Usage: python test_upload18_only.py <video_path>")
    sys.exit(1)

video_path = sys.argv[1]

if not os.path.exists(video_path):
    print(f"✗ Video not found: {video_path}")
    sys.exit(1)

print(f"\n{'='*80}")
print("TESTING UPLOAD18")
print(f"{'='*80}")
print(f"Video: {video_path}")
print(f"Size: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
print(f"{'='*80}\n")

uploader = Upload18Uploader(
    email=os.getenv("UPLOAD18_EMAIL"),
    username=os.getenv("UPLOAD18_USERNAME"),
    password=os.getenv("UPLOAD18_PASSWORD"),
    api_key=os.getenv("UPLOAD18_API_KEY")
)

result = uploader.upload(video_path)

print(f"\n{'='*80}")
print("RESULT")
print(f"{'='*80}")

if result.get('success'):
    print(f"✓ Upload successful!")
    print(f"  VID: {result.get('vid')}")
    print(f"  DID: {result.get('did')}")
    print(f"  URL: {result.get('url')}")
    print(f"  Embed: {result.get('embed_url')}")
else:
    print(f"✗ Upload failed: {result.get('error')}")

print(f"{'='*80}\n")
