#!/usr/bin/env python3
"""Test credential masking"""
import re


def mask_credentials(text: str) -> str:
    """Mask sensitive credentials in log output"""
    # Simulate environment tokens
    tokens = {
        'GITHUB_TOKEN': 'ghp_1234567890abcdefghijklmnopqrstuvwxyz',
        'STREAMWISH_API_KEY': 'sw_abcdef123456',
        'LULUSTREAM_API_KEY': 'lulu_xyz789',
        'STREAMTAPE_API_KEY': 'st_qwerty456'
    }
    
    # Mask each token
    for token_name, token_value in tokens.items():
        if token_value and len(token_value) > 8:
            text = text.replace(token_value, '***TOKEN***')
    
    # Mask common patterns
    # Mask URLs with tokens: https://TOKEN@github.com
    text = re.sub(r'https://[^@\s]+@github\.com', 'https://***TOKEN***@github.com', text)
    
    # Mask API keys in URLs: ?key=TOKEN
    text = re.sub(r'[?&]key=[^&\s]+', '?key=***TOKEN***', text)
    
    # Mask API keys in URLs: &api_key=TOKEN
    text = re.sub(r'[?&]api_key=[^&\s]+', '&api_key=***TOKEN***', text)
    
    return text


def test_credential_masking():
    """Test that credentials are properly masked"""
    test_cases = [
        # (input, expected_output, description)
        (
            "Using token ghp_1234567890abcdefghijklmnopqrstuvwxyz",
            "Using token ***TOKEN***",
            "GitHub token masking"
        ),
        (
            "API key: sw_abcdef123456",
            "API key: ***TOKEN***",
            "StreamWish API key masking"
        ),
        (
            "https://ghp_1234567890abcdefghijklmnopqrstuvwxyz@github.com/repo.git",
            "https://***TOKEN***@github.com/repo.git",
            "Token in GitHub URL"
        ),
        (
            "https://api.example.com?key=secret123",
            "https://api.example.com?key=***TOKEN***",
            "API key in query parameter"
        ),
        (
            "https://api.example.com?param=value&api_key=secret456",
            "https://api.example.com?param=value&api_key=***TOKEN***",
            "API key in URL parameter"
        ),
        (
            "Multiple tokens: ghp_1234567890abcdefghijklmnopqrstuvwxyz and sw_abcdef123456",
            "Multiple tokens: ***TOKEN*** and ***TOKEN***",
            "Multiple tokens in same string"
        ),
    ]
    
    print("Testing credential masking...")
    print()
    
    all_passed = True
    
    for input_text, expected, description in test_cases:
        result = mask_credentials(input_text)
        passed = result == expected
        
        status = "✓" if passed else "✗"
        print(f"{status} {description}")
        print(f"  Input:    {input_text}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        
        if not passed:
            all_passed = False
            print(f"  FAILED!")
        
        print()
    
    # Test that non-sensitive data is not masked
    print("Testing that normal text is preserved...")
    normal_texts = [
        "This is a normal log message",
        "Processing video ABC-123",
        "https://example.com/video/123",
        "Error: Connection timeout",
    ]
    
    for text in normal_texts:
        result = mask_credentials(text)
        if result == text:
            print(f"✓ Preserved: {text}")
        else:
            print(f"✗ FAILED: Text was modified")
            print(f"  Original: {text}")
            print(f"  Result:   {result}")
            all_passed = False
    
    print()
    
    if all_passed:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed! ✗")
        return 1


if __name__ == "__main__":
    exit(test_credential_masking())
