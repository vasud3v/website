#!/usr/bin/env python3
"""Test URL normalization"""

def normalize_url(url: str) -> str:
    """
    Normalize URL for comparison to prevent duplicates.
    
    Rules:
    - Convert to lowercase
    - Use https:// protocol
    - Remove www. prefix
    - Remove trailing slashes
    - Remove query parameters (?key=value)
    - Remove fragments (#section)
    """
    if not url:
        return ""
    
    url = url.lower().strip()
    
    # Normalize protocol
    url = url.replace('http://', 'https://')
    
    # Remove www prefix
    url = url.replace('https://www.', 'https://')
    
    # Remove query parameters
    if '?' in url:
        url = url.split('?')[0]
    
    # Remove fragments
    if '#' in url:
        url = url.split('#')[0]
    
    # Remove trailing slash (after removing query/fragment)
    url = url.rstrip('/')
    
    return url


def test_url_normalization():
    """Test that URL normalization handles all edge cases"""
    test_cases = [
        # (input_url, expected_normalized)
        ("http://example.com", "https://example.com"),
        ("https://example.com", "https://example.com"),
        ("http://www.example.com", "https://example.com"),
        ("https://www.example.com", "https://example.com"),
        ("https://example.com/", "https://example.com"),
        ("https://example.com/path", "https://example.com/path"),
        ("https://example.com/path/", "https://example.com/path"),
        ("https://example.com?query=value", "https://example.com"),
        ("https://example.com#fragment", "https://example.com"),
        ("https://example.com/path?query=value#fragment", "https://example.com/path"),
        ("HTTP://WWW.EXAMPLE.COM/PATH/?QUERY=VALUE#FRAGMENT", "https://example.com/path"),
    ]
    
    print("Testing URL normalization...")
    print()
    
    all_passed = True
    
    for input_url, expected in test_cases:
        result = normalize_url(input_url)
        passed = result == expected
        
        status = "✓" if passed else "✗"
        print(f"{status} {input_url}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        
        if not passed:
            all_passed = False
            print(f"  FAILED!")
        
        print()
    
    # Test consistency: same URLs should normalize to same value
    print("Testing consistency...")
    variants = [
        "http://example.com/video/123",
        "https://example.com/video/123",
        "http://www.example.com/video/123",
        "https://www.example.com/video/123",
        "https://example.com/video/123/",
        "https://example.com/video/123?ref=home",
        "https://example.com/video/123#comments",
    ]
    
    normalized_variants = [normalize_url(url) for url in variants]
    unique_normalized = set(normalized_variants)
    
    if len(unique_normalized) == 1:
        print(f"✓ All {len(variants)} variants normalized to same URL")
        print(f"  Normalized: {normalized_variants[0]}")
    else:
        print(f"✗ FAILED: {len(variants)} variants produced {len(unique_normalized)} different normalized URLs")
        for url in unique_normalized:
            print(f"  - {url}")
        all_passed = False
    
    print()
    
    if all_passed:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed! ✗")
        return 1


if __name__ == "__main__":
    exit(test_url_normalization())
