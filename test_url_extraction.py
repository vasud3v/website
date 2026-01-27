#!/usr/bin/env python3
"""
Test URL code extraction with real examples from the log
"""

import re
from urllib.parse import unquote

def extract_code_from_url(url):
    """Extract video code from URL with validation and URL decoding"""
    match = re.search(r'/(video|fc2ppv|xvideo)/([^/]+)', url)
    if match:
        raw_code = match.group(2)
        
        # URL decode to handle encoded characters
        decoded = unquote(raw_code)
        
        # For FC2PPV, extract just the code part (FC2PPV-XXXXXX)
        # Pattern: FC2PPV-digits, optionally followed by title
        fc2_match = re.match(r'(FC2PPV-\d+)', decoded, re.IGNORECASE)
        if fc2_match:
            code = fc2_match.group(1).upper()
            return code
        
        # For regular codes, take the part before any special characters or spaces
        # Split on common separators and take first part
        code_part = re.split(r'[%\s【\u3000]', decoded)[0]
        code = code_part.upper()
        
        # Validate code format (alphanumeric, hyphens, underscores only)
        if re.match(r'^[A-Z0-9_-]+$', code) and len(code) > 0:
            return code
        else:
            # If validation fails, try to extract any alphanumeric-hyphen sequence
            clean_match = re.search(r'^([A-Z0-9_-]+)', code, re.IGNORECASE)
            if clean_match:
                return clean_match.group(1).upper()
            
            print(f"⚠️ Could not extract valid code from: {raw_code[:50]}")
            return 'unknown'
    
    return 'unknown'


# Test cases from the log
test_urls = [
    ("https://javmix.tv/fc2ppv/FC2PPV-1154407-%E3%80%90%E7%84%A1%E3%80%91%E3%81%8A%E6%B3%8A%E3%82%8A%E3%81%A7%E8%8A%B1%E7%81%AB%E5%A4%A7%E4%BC%9A%E3%81%AB%E4%B8%80%E7%B7%92%E3%81%AB%E8%A1%8C%E3%81%A3%E3%81%9F%E5%BD%BC%E5%A5%B3", "FC2PPV-1154407"),
    ("https://javmix.tv/fc2ppv/FC2PPV-1771205-%E3%80%90%E5%80%8B%E4%BA%BA%E6%92%AE%E5%BD%B1%E3%80%91%E3%82%AA%E3%83%A4%E3%82%B8%E3%81%AE%E3%83%81%E3%80%87%E3%83%9D%E3%81%AB%E8%88%88%E5%91%B3%E3%82%92%E6%8C%81%E3%81%A3%E3%81%9FOL", "FC2PPV-1771205"),
    ("https://javmix.tv/fc2ppv/FC2PPV-1836727-%E5%80%8B%E6%95%B0%E9%99%90%E5%AE%9A%E3%80%90%E7%84%A1%E4%BF%AE%E6%AD%A3%E3%80%91%E3%80%8C%E7%A7%81%E3%81%A8%E3%81%AF%E3%81%97%E3%81%AA%E3%81%84%E3%81%AE%EF%BC%9F%E3%80%8D%E5%8F%8B", "FC2PPV-1836727"),
    ("https://javmix.tv/video/%E3%82%B9%E3%83%AC%E3%83%B3%E3%83%80%E3%83%BC%E7%BE%8E%E5%A5%B3%E3%81%AE%E7%B8%A6%E6%92%AE%E3%82%8A%E9%A8%8E%E4%B9%97%E4%BD%8D%EF%BC%8FSHO", "unknown"),  # No code, just title
    ("https://javmix.tv/fc2ppv/FC2PPV-2129074-%E3%80%90%E6%96%B0%E4%BD%9C%E3%83%BB%E5%8D%8A%E9%A1%8D%EF%BC%81%E3%80%91%E2%99%80%EF%BC%93%EF%BC%92%EF%BC%94%E5%A5%B3%E5%AD%90%E5%A4%A7%E7%94%9F%E3%82%8A%E2%97%AF%E3%81%A1%E3%82%83", "FC2PPV-2129074"),
    ("https://javmix.tv/fc2ppv/FC2PPV-2044547-%E3%80%90%E5%80%8B%E6%92%AE%E7%84%A1%E3%83%BB%E7%9B%AE%E3%81%AE%E5%89%8D%E3%81%A7%E4%BB%96%E4%BA%BA%E6%A3%92%E3%82%92%E4%BD%BF%E3%81%84%E5%BC%B7%E5%88%B6%EF%BD%8E%EF%BD%94%EF%BD%92", "FC2PPV-2044547"),
    ("https://javmix.tv/video/HBAD-725/", "HBAD-725"),
    ("https://javmix.tv/video/AUKG-603/", "AUKG-603"),
]

print("\n" + "="*80)
print("URL CODE EXTRACTION TEST")
print("="*80)

passed = 0
failed = 0

for url, expected in test_urls:
    result = extract_code_from_url(url)
    status = "✓" if result == expected else "✗"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    # Decode URL for display
    decoded_url = unquote(url)
    
    print(f"\n{status} URL: {decoded_url[:80]}...")
    print(f"  Expected: {expected}")
    print(f"  Got:      {result}")

print("\n" + "="*80)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*80)
