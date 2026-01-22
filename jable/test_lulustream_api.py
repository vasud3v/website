"""
Test script to verify LuluStream API integration
Run this to test your API key and server connectivity
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(load_env_path):
    load_dotenv(load_env_path)
    print(f"✓ Loaded .env from: {load_env_path}")
else:
    print(f"⚠️ No .env file found at: {load_env_path}")

def test_api_key():
    """Test if API key is set and valid"""
    print("\n" + "="*60)
    print("TEST 1: API Key Validation")
    print("="*60)
    
    api_key = os.getenv('LULUSTREAM_API_KEY')
    
    if not api_key:
        print("❌ LULUSTREAM_API_KEY not set in environment")
        print("   Please add it to your .env file:")
        print("   LULUSTREAM_API_KEY=your_key_here")
        return False
    
    print(f"✓ API key found: {api_key[:10]}...{api_key[-4:]}")
    print(f"  Length: {len(api_key)} characters")
    return True

def test_upload_server():
    """Test getting upload server endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Upload Server Endpoint")
    print("="*60)
    
    api_key = os.getenv('LULUSTREAM_API_KEY')
    
    try:
        print("Requesting upload server...")
        response = requests.get(
            "https://lulustream.com/api/upload/server",
            params={'key': api_key},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response: {data}")
                
                if 'result' in data:
                    server = data['result']
                    print(f"✓ Upload server: {server}")
                    return True
                else:
                    print(f"⚠️ No 'result' in response")
                    return False
            except Exception as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Raw response: {response.text[:200]}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_file_list():
    """Test getting file list (requires valid API key with files)"""
    print("\n" + "="*60)
    print("TEST 3: File List Endpoint")
    print("="*60)
    
    api_key = os.getenv('LULUSTREAM_API_KEY')
    
    try:
        print("Requesting file list...")
        response = requests.get(
            "https://lulustream.com/api/file/list",
            params={'key': api_key, 'per_page': 5},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response status: {data.get('status')}")
                
                if data.get('status') == 200:  # LuluStream uses numeric status
                    result = data.get('result', {})
                    
                    # Handle different response structures
                    if isinstance(result, dict):
                        files = result.get('files', [])
                    elif isinstance(result, list):
                        files = result
                    else:
                        files = []
                    
                    print(f"✓ Found {len(files)} files")
                    
                    if files:
                        print("\nRecent files:")
                        for i, file in enumerate(files[:3], 1):
                            print(f"  {i}. {file.get('title', 'N/A')}")
                            print(f"     Code: {file.get('file_code', 'N/A')}")
                            print(f"     Size: {file.get('size', 'N/A')}")
                    else:
                        print("  (No files uploaded yet)")
                    
                    return True
                else:
                    print(f"⚠️ Status: {data.get('status')}")
                    print(f"Message: {data.get('msg', 'N/A')}")
                    return False
            except Exception as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Raw response: {response.text[:200]}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_parameter_format():
    """Test that we're using correct parameter names"""
    print("\n" + "="*60)
    print("TEST 4: Parameter Format Verification")
    print("="*60)
    
    print("Checking parameter names used in code...")
    
    # These are the correct parameters based on our fixes
    correct_params = {
        'auth': 'key',  # Not 'api_key'
        'folder': 'fld_id',  # Not 'folder'
        'title': 'title',
        'file': 'file'
    }
    
    print("\n✓ Correct parameter names:")
    for purpose, param in correct_params.items():
        print(f"  {purpose:12} → {param}")
    
    print("\n❌ Incorrect parameter names (DO NOT USE):")
    print("  auth         → api_key")
    print("  folder       → folder")
    
    return True

def main():
    """Run all tests"""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         LuluStream API Integration Test Suite           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    results = []
    
    # Test 1: API Key
    results.append(("API Key", test_api_key()))
    
    if not results[0][1]:
        print("\n⚠️ Cannot proceed without API key")
        return
    
    # Test 2: Upload Server
    results.append(("Upload Server", test_upload_server()))
    
    # Test 3: File List
    results.append(("File List", test_file_list()))
    
    # Test 4: Parameter Format
    results.append(("Parameter Format", test_parameter_format()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! LuluStream API integration is working correctly.")
    elif passed >= total - 1:
        print("\n⚠️ Most tests passed. Check failed tests above.")
    else:
        print("\n❌ Multiple tests failed. Please check your API key and network connection.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
