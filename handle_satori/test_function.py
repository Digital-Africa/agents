#!/usr/bin/env python3
"""
Test script to verify the handle_satori_input function signature
"""

from main import handle_satori_input

# Test with dict format (what Gen2 Cloud Functions typically pass)
test_event = {
    "name": "test_startups.csv",
    "bucket": "fuze-subscriptions",
    "contentType": "text/csv",
    "size": "1024"
}

print("Testing function with dict format...")
try:
    # This should not raise a TypeError about argument count
    handle_satori_input(test_event)
    print("✅ Function signature test passed!")
except TypeError as e:
    print(f"❌ Function signature test failed: {e}")
except Exception as e:
    print(f"⚠️  Function ran but encountered other error: {e}")
    print("This is expected since we don't have the actual dependencies set up for testing") 
    