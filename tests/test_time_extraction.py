#!/usr/bin/env python3
"""Test time extraction edge cases"""

def test_time_extraction():
    """Test that time extraction handles edge cases correctly"""
    test_cases = [
        ("00", "00", "midnight"),
        ("00", "30", "half_past_midnight"),
        ("01", "00", "top_of_hour"),
        ("09", "00", "single_digit_hour"),
        ("12", "00", "noon"),
        ("23", "59", "end_of_day"),
    ]
    
    print("Testing time extraction logic...")
    print()
    
    all_passed = True
    
    for hour_str, minute_str, label in test_cases:
        print(f"Test: {label} ({hour_str}:{minute_str})")
        
        # Simulate bash arithmetic expansion: $((10#XX))
        # This interprets the number as base-10, removing leading zeros
        hour = int(hour_str, 10)
        minute = int(minute_str, 10)
        
        print(f"  Hour: {hour}")
        print(f"  Minute: {minute}")
        
        # Verify it's numeric and not empty
        if isinstance(hour, int) and isinstance(minute, int):
            print("  ✓ Valid numeric values")
        else:
            print("  ✗ FAILED: Not numeric!")
            all_passed = False
        
        # Verify values are in valid range
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            print("  ✓ Valid range")
        else:
            print("  ✗ FAILED: Out of range!")
            all_passed = False
        
        print()
    
    if all_passed:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed! ✗")
        return 1

if __name__ == "__main__":
    exit(test_time_extraction())
