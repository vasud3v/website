#!/usr/bin/env python3
"""Test exponential backoff calculation"""


def calculate_backoff(attempt: int) -> int:
    """Calculate exponential backoff time in seconds"""
    return 2 ** attempt


def test_backoff_calculation():
    """Test that exponential backoff calculates correctly"""
    test_cases = [
        # (attempt, expected_seconds, description)
        (1, 2, "First retry: 2 seconds"),
        (2, 4, "Second retry: 4 seconds"),
        (3, 8, "Third retry: 8 seconds"),
        (4, 16, "Fourth retry: 16 seconds"),
        (5, 32, "Fifth retry: 32 seconds"),
    ]
    
    print("Testing exponential backoff calculation...")
    print()
    
    all_passed = True
    
    for attempt, expected, description in test_cases:
        result = calculate_backoff(attempt)
        passed = result == expected
        
        status = "✓" if passed else "✗"
        print(f"{status} {description}")
        print(f"  Attempt: {attempt}")
        print(f"  Expected: {expected}s")
        print(f"  Got: {result}s")
        
        if not passed:
            all_passed = False
            print(f"  FAILED!")
        
        print()
    
    # Test the sequence used in the implementation
    print("Testing actual retry sequence (3 attempts)...")
    max_retries = 3
    expected_sequence = [2, 4, 8]  # 2^1, 2^2, 2^3
    
    for attempt in range(1, max_retries + 1):
        wait_time = calculate_backoff(attempt)
        expected_time = expected_sequence[attempt - 1]
        
        if wait_time == expected_time:
            print(f"✓ Attempt {attempt}: {wait_time}s")
        else:
            print(f"✗ Attempt {attempt}: Expected {expected_time}s, got {wait_time}s")
            all_passed = False
    
    print()
    
    # Test total wait time
    total_wait = sum(calculate_backoff(i) for i in range(1, max_retries + 1))
    expected_total = 2 + 4 + 8  # 14 seconds
    
    if total_wait == expected_total:
        print(f"✓ Total wait time for 3 retries: {total_wait}s")
    else:
        print(f"✗ Total wait time: Expected {expected_total}s, got {total_wait}s")
        all_passed = False
    
    print()
    
    if all_passed:
        print("All tests passed! ✓")
        return 0
    else:
        print("Some tests failed! ✗")
        return 1


if __name__ == "__main__":
    exit(test_backoff_calculation())
