#!/bin/bash
# Test time extraction edge cases

echo "Testing time extraction with arithmetic expansion..."
echo ""

# Test cases
test_cases=(
    "00:00:midnight"
    "00:30:half_past_midnight"
    "01:00:top_of_hour"
    "09:00:single_digit_hour"
    "12:00:noon"
    "23:59:end_of_day"
)

for test_case in "${test_cases[@]}"; do
    IFS=':' read -r hour minute label <<< "$test_case"
    
    echo "Test: $label (${hour}:${minute})"
    
    # Simulate the extraction
    CURRENT_MINUTE=$((10#$minute))
    CURRENT_HOUR=$((10#$hour))
    
    echo "  Hour: $CURRENT_HOUR (expected: ${hour#0})"
    echo "  Minute: $CURRENT_MINUTE (expected: ${minute#0})"
    
    # Verify it's numeric
    if [[ "$CURRENT_HOUR" =~ ^[0-9]+$ ]] && [[ "$CURRENT_MINUTE" =~ ^[0-9]+$ ]]; then
        echo "  ✓ Valid numeric values"
    else
        echo "  ✗ FAILED: Not numeric!"
        exit 1
    fi
    
    # Verify not empty
    if [ -n "$CURRENT_HOUR" ] && [ -n "$CURRENT_MINUTE" ]; then
        echo "  ✓ Not empty"
    else
        echo "  ✗ FAILED: Empty value!"
        exit 1
    fi
    
    echo ""
done

echo "All tests passed! ✓"
