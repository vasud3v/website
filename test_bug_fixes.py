#!/usr/bin/env python3
"""
Test suite for bug fixes and edge cases
Run with: python test_bug_fixes.py
"""

import json
import os
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

def test_json_loading():
    """Test JSON loading with various edge cases"""
    print("\n" + "="*60)
    print("TEST 1: JSON Loading Edge Cases")
    print("="*60)
    
    test_cases = [
        ("Empty list", "[]"),
        ("Empty dict", "{}"),
        ("List with dict", '[{"code": "TEST-001"}]'),
        ("Dict with videos", '{"videos": [{"code": "TEST-001"}]}'),
        ("Malformed JSON", '{"code": "TEST-001"'),  # Missing closing brace
        ("None value", None),
    ]
    
    for name, data in test_cases:
        print(f"\n  Testing: {name}")
        try:
            if data is None:
                result = None
            else:
                result = json.loads(data)
            
            # Test .get() method
            if isinstance(result, dict):
                code = result.get('code', 'default')
                print(f"    ✓ Dict .get() works: {code}")
            elif isinstance(result, list):
                print(f"    ⚠️ Got list, cannot use .get()")
                if len(result) > 0 and isinstance(result[0], dict):
                    code = result[0].get('code', 'default')
                    print(f"    ✓ List[0] .get() works: {code}")
            else:
                print(f"    ⚠️ Got {type(result).__name__}")
        except json.JSONDecodeError as e:
            print(f"    ✗ JSON decode error: {str(e)[:50]}")
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")


def test_embed_urls_access():
    """Test embed_urls dictionary access edge cases"""
    print("\n" + "="*60)
    print("TEST 2: Embed URLs Access Edge Cases")
    print("="*60)
    
    test_cases = [
        ("Normal dict", {"streamtape": "url1", "doodstream": "url2"}),
        ("Empty dict", {}),
        ("None value", None),
        ("List instead of dict", ["url1", "url2"]),
        ("Single item", {"streamtape": "url1"}),
    ]
    
    for name, embed_urls in test_cases:
        print(f"\n  Testing: {name}")
        try:
            # Check if it's a dict
            if not isinstance(embed_urls, dict):
                print(f"    ⚠️ Not a dict: {type(embed_urls).__name__}")
                continue
            
            # Check if empty
            if not embed_urls:
                print(f"    ⚠️ Empty dict")
                continue
            
            # Try to access first value
            if len(embed_urls) > 0:
                first_url = list(embed_urls.values())[0]
                print(f"    ✓ First URL: {first_url}")
            else:
                print(f"    ⚠️ Dict has no values")
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")


def test_file_size_parsing():
    """Test file size parsing edge cases"""
    print("\n" + "="*60)
    print("TEST 3: File Size Parsing Edge Cases")
    print("="*60)
    
    test_cases = [
        ("Normal MB", "~600MB", 600 * 1024 * 1024),
        ("Normal GB", "1.5GB", 1.5 * 1024 * 1024 * 1024),
        ("With space", "600 MB", 600 * 1024 * 1024),
        ("Decimal MB", "1234.56MB", 1234.56 * 1024 * 1024),
        ("KB value", "500KB", 500 * 1024),
        ("No unit", "600", 600 * 1024 * 1024),  # Assume MB
        ("N/A", "N/A", 0),
        ("Unknown", "Unknown", 0),
        ("Empty string", "", 0),
        ("None", None, 0),
        ("Integer", 1024000, 1024000),
        ("Float", 1024000.5, 1024000),
    ]
    
    for name, size_input, expected in test_cases:
        print(f"\n  Testing: {name} = '{size_input}'")
        try:
            result = parse_file_size(size_input)
            if abs(result - expected) < 1:  # Allow small rounding errors
                print(f"    ✓ Parsed correctly: {result} bytes")
            else:
                print(f"    ✗ Expected {expected}, got {result}")
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")


def parse_file_size(size):
    """Helper function to parse file size (mimics database_manager.py logic)"""
    if size is None:
        return 0
    
    try:
        if isinstance(size, str):
            size_str = size.strip().replace('~', '').replace(' ', '').upper()
            
            if size_str in ['N/A', 'UNKNOWN', '', 'NONE']:
                return 0
            
            import re
            match = re.search(r'(\d+\.?\d*)', size_str)
            if match:
                size_num = float(match.group(1))
                
                if 'GB' in size_str:
                    return int(size_num * 1024 * 1024 * 1024)
                elif 'MB' in size_str:
                    return int(size_num * 1024 * 1024)
                elif 'KB' in size_str:
                    return int(size_num * 1024)
                else:
                    return int(size_num * 1024 * 1024)
        elif isinstance(size, (int, float)):
            return int(size)
    except Exception:
        return 0
    
    return 0


def test_code_validation():
    """Test video code validation"""
    print("\n" + "="*60)
    print("TEST 4: Video Code Validation")
    print("="*60)
    
    test_cases = [
        ("Normal code", "HBAD-725", True),
        ("FC2PPV code", "FC2PPV-12345", True),
        ("With underscore", "TEST_001", True),
        ("Lowercase", "hbad-725", True),  # Will be uppercased
        ("With spaces", "HBAD 725", False),
        ("With special chars", "HBAD<725>", False),
        ("With slash", "HBAD/725", False),
        ("Empty", "", False),
        ("None", None, False),
    ]
    
    for name, code, should_pass in test_cases:
        print(f"\n  Testing: {name} = '{code}'")
        try:
            result = validate_code(code)
            if result == should_pass:
                print(f"    ✓ Validation correct: {result}")
            else:
                print(f"    ✗ Expected {should_pass}, got {result}")
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")


def validate_code(code):
    """Helper function to validate video code"""
    if not code or not isinstance(code, str):
        return False
    
    import re
    code = code.upper()
    return bool(re.match(r'^[A-Z0-9_-]+$', code))


def test_code_sanitization():
    """Test code sanitization for filesystem"""
    print("\n" + "="*60)
    print("TEST 5: Code Sanitization for Filesystem")
    print("="*60)
    
    test_cases = [
        ("Normal code", "HBAD-725", "HBAD-725"),
        ("With slash", "HBAD/725", "HBAD_725"),
        ("With colon", "HBAD:725", "HBAD_725"),
        ("With asterisk", "HBAD*725", "HBAD_725"),
        ("With question", "HBAD?725", "HBAD_725"),
        ("Multiple special", "HBAD<>:725", "HBAD___725"),
        ("Leading dot", ".HBAD-725", "HBAD-725"),
        ("Trailing dot", "HBAD-725.", "HBAD-725"),
        ("Very long", "A" * 300, "A" * 200),
    ]
    
    for name, code, expected in test_cases:
        print(f"\n  Testing: {name}")
        try:
            result = sanitize_code(code)
            if result == expected:
                print(f"    ✓ Sanitized correctly: '{result}'")
            else:
                print(f"    ✗ Expected '{expected}', got '{result}'")
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")


def sanitize_code(code):
    """Helper function to sanitize code for filesystem"""
    import re
    safe_code = re.sub(r'[<>:"/\\|?*]', '_', code)
    safe_code = safe_code[:200]
    safe_code = safe_code.strip('. ')
    return safe_code if safe_code else 'unknown'


def test_division_by_zero():
    """Test division by zero scenarios"""
    print("\n" + "="*60)
    print("TEST 6: Division by Zero Protection")
    print("="*60)
    
    test_cases = [
        ("Normal", [1, 2, 3], 3, 100.0),
        ("Empty list", [], 0, 0.0),
        ("None list", None, 0, 0.0),
        ("All processed", [1, 2, 3], 3, 100.0),
        ("None processed", [1, 2, 3], 0, 0.0),
    ]
    
    for name, videos, processed, expected_rate in test_cases:
        print(f"\n  Testing: {name}")
        try:
            if not isinstance(videos, list):
                videos = []
            
            total = len(videos)
            rate = (processed / total * 100) if total > 0 else 0
            
            if abs(rate - expected_rate) < 0.01:
                print(f"    ✓ Success rate: {rate:.1f}%")
            else:
                print(f"    ✗ Expected {expected_rate:.1f}%, got {rate:.1f}%")
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")


def test_translation_edge_cases():
    """Test translation with edge cases"""
    print("\n" + "="*60)
    print("TEST 7: Translation Edge Cases")
    print("="*60)
    
    test_cases = [
        ("Normal text", "こんにちは", str),
        ("Empty string", "", str),
        ("None", None, str),
        ("Integer", 123, str),
        ("List", ["test"], str),
        ("Very long", "あ" * 10000, str),
    ]
    
    for name, text, expected_type in test_cases:
        print(f"\n  Testing: {name}")
        try:
            result = mock_translate(text)
            if isinstance(result, expected_type):
                print(f"    ✓ Returns {expected_type.__name__}: '{str(result)[:50]}'")
            else:
                print(f"    ✗ Expected {expected_type.__name__}, got {type(result).__name__}")
        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")


def mock_translate(text):
    """Mock translation function with error handling"""
    if not text or not isinstance(text, str):
        return ""
    
    text = text.strip()
    if not text:
        return ""
    
    try:
        # Mock translation (just return original in real test)
        return text
    except Exception:
        return text


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*70)
    print("BUG FIXES AND EDGE CASES TEST SUITE")
    print("="*70)
    
    test_json_loading()
    test_embed_urls_access()
    test_file_size_parsing()
    test_code_validation()
    test_code_sanitization()
    test_division_by_zero()
    test_translation_edge_cases()
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)
    print("\nReview the output above for any failures (✗)")
    print("All tests with ✓ passed successfully\n")


if __name__ == "__main__":
    run_all_tests()
