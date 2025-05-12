#!/usr/bin/env python3

import requests
import json
import sys

"""
Comprehensive test suite for the County Health Rankings API
This test script verifies that the API meets all requirements from the assignment.
"""

# Get the API URL from link.txt
try:
    with open('link.txt', 'r') as f:
        API_URL = f.read().strip()
        print(f"Testing API at: {API_URL}")
except FileNotFoundError:
    print("Error: link.txt file not found")
    sys.exit(1)

# API key for authentication
API_KEY = "cs1060-hw4-apikey"

# Test helper function
def test_api(description, data, expected_status, check_fn=None):
    print(f"\nTest: {description}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    # If API_URL already ends with /county_data, don't append it again
    endpoint = API_URL
    if not endpoint.endswith('/county_data'):
        endpoint = f"{endpoint}/county_data"
    
    print(f"Sending request to: {endpoint}")
    
    try:
        response = requests.post(
            endpoint, 
            json=data,
            headers={"Content-Type": "application/json", "X-API-Key": API_KEY}
        )
        
        print(f"Status code: {response.status_code} (Expected: {expected_status})")
        
        try:
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)[:300]}...")
        except json.JSONDecodeError:
            print(f"Response text: {response.text}")
            
        # Check status code
        status_ok = response.status_code == expected_status
        
        # Run additional checks if provided
        check_result = True
        if check_fn and status_ok:
            check_result = check_fn(response)
            
        if status_ok and check_result:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("❌ FAIL")
        return False

def check_valid_data(response):
    """Check if response contains valid county health data"""
    data = response.json()
    if not isinstance(data, list) or len(data) == 0:
        print("Data should be a non-empty list")
        return False
        
    required_fields = ["county", "state", "measure_name", "raw_value", "year_span"]
    for field in required_fields:
        if field not in data[0]:
            print(f"Missing required field: {field}")
            return False
    
    return True

def check_sample_data(response):
    """Check if response contains sample data"""
    data = response.json()
    return "note" in data and "data" in data

# Tests
tests = [
    # Test 1: Valid request with existing data
    {
        "description": "Valid request with existing data",
        "data": {"zip": "00801", "measure_name": "Premature Death"},
        "expected_status": 200,
        "check_fn": check_valid_data
    },
    
    # Test 2: Authentication failure test
    {
        "description": "Authentication failure (send with wrong API key in actual test)",
        "data": {"zip": "00801", "measure_name": "Premature Death"},
        "expected_status": 401  # We'll use a different headers in the actual request
    },
    
    # Test 3: Invalid measure name
    {
        "description": "Invalid measure name",
        "data": {"zip": "00801", "measure_name": "Invalid Measure"},
        "expected_status": 400
    },
    
    # Test 4: Missing parameters
    {
        "description": "Missing required parameters",
        "data": {"zip": "00801"},
        "expected_status": 400
    },
    
    # Test 5: Teapot Easter egg
    {
        "description": "Teapot Easter egg",
        "data": {"zip": "00801", "measure_name": "Premature Death", "coffee": "teapot"},
        "expected_status": 418
    },
    
    # Test 6: Sample mode
    {
        "description": "Sample mode for non-existent data",
        "data": {"zip": "02138", "measure_name": "Physical inactivity", "sample_mode": True},
        "expected_status": 200,
        "check_fn": check_sample_data
    }
]

# Run the authentication failure test separately with a wrong API key
def test_auth_failure():
    print("\nTest: Authentication failure")
    # If API_URL already ends with /county_data, don't append it again
    endpoint = API_URL
    if not endpoint.endswith('/county_data'):
        endpoint = f"{endpoint}/county_data"
    
    print(f"Sending request to: {endpoint}")
    
    try:
        response = requests.post(
            endpoint, 
            json={"zip": "00801", "measure_name": "Premature Death"},
            headers={"Content-Type": "application/json", "X-API-Key": "wrong-key"}
        )
        
        print(f"Status code: {response.status_code} (Expected: 401)")
        
        if response.status_code == 401:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("❌ FAIL")
        return False

# Run all tests
def run_tests():
    results = []
    
    # Run standard tests
    for test in tests:
        if test["description"] != "Authentication failure (send with wrong API key in actual test)":
            result = test_api(
                test["description"], 
                test["data"], 
                test["expected_status"],
                test.get("check_fn")
            )
            results.append(result)
    
    # Run auth failure test
    results.append(test_auth_failure())
    
    # Print summary
    passed = results.count(True)
    total = len(results)
    print(f"\n----- TEST SUMMARY -----")
    print(f"Passed: {passed}/{total} tests ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("✅ All tests passed! Your API meets all requirements.")
    else:
        print("❌ Some tests failed. Review the output above for details.")

if __name__ == "__main__":
    run_tests()
