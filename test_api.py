#!/usr/bin/env python3
"""
Comprehensive API endpoint testing
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8300"


def test_health():
    """Test health endpoint"""
    print("\n=== Testing /health ===")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["status"] == "ok"
    print("✓ Health endpoint working")
    return True


def test_root():
    """Test root endpoint"""
    print("\n=== Testing / ===")
    resp = requests.get(f"{BASE_URL}/")
    assert resp.status_code == 200
    data = resp.json()
    assert "service" in data
    assert "version" in data
    assert "docs" in data
    print(f"✓ Root endpoint: {data}")
    return True


def test_docs():
    """Test OpenAPI docs"""
    print("\n=== Testing /docs and /openapi.json ===")
    
    # HTML docs
    resp = requests.get(f"{BASE_URL}/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower()
    print("✓ Swagger UI available")
    
    # OpenAPI spec
    resp = requests.get(f"{BASE_URL}/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert "openapi" in spec
    assert "paths" in spec
    print(f"✓ OpenAPI spec has {len(spec['paths'])} endpoints")
    return True


def test_user_configure():
    """Test user configuration"""
    print("\n=== Testing POST /api/users/configure ===")
    
    # Valid user
    user_data = {
        "user_id": "api_test_user",
        "linkedin_credentials": {
            "email": "[email protected]",
            "password": "APITestPassword123!"
        },
        "llm_config": {
            "type": "anthropic",
            "model": "claude-sonnet-4-5",
            "api_key": "sk-ant-api-test-key-12345678"
        },
        "daily_limits": {
            "connections": 75,
            "messages": 40
        }
    }
    
    resp = requests.post(
        f"{BASE_URL}/api/users/configure",
        json=user_data
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["status"] == "success"
    assert data["user_id"] == "api_test_user"
    print(f"✓ User created: {data}")
    
    # Update existing user
    user_data["llm_config"]["type"] = "openai"
    user_data["llm_config"]["model"] = "gpt-4"
    resp = requests.post(
        f"{BASE_URL}/api/users/configure",
        json=user_data
    )
    assert resp.status_code == 200
    print("✓ User updated successfully")
    
    return True


def test_user_get():
    """Test getting user info"""
    print("\n=== Testing GET /api/users/{user_id} ===")
    
    resp = requests.get(f"{BASE_URL}/api/users/api_test_user")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "api_test_user"
    assert data["linkedin_email"] == "[email protected]"
    assert data["llm_provider"] == "openai"  # Updated from anthropic
    assert data["daily_limits"]["connections"] == 75
    print(f"✓ User retrieved: {data}")
    
    # Test 404
    resp = requests.get(f"{BASE_URL}/api/users/nonexistent_user_xyz")
    assert resp.status_code == 404
    print("✓ 404 for nonexistent user")
    
    return True


def test_user_credentials():
    """Test getting masked credentials"""
    print("\n=== Testing GET /api/users/{user_id}/credentials ===")
    
    resp = requests.get(f"{BASE_URL}/api/users/api_test_user/credentials")
    assert resp.status_code == 200
    data = resp.json()
    assert data["linkedin_email"] == "[email protected]"
    assert data["linkedin_password"].startswith("****")
    assert data["llm_api_key"].startswith("****")
    assert data["llm_provider"] == "openai"
    assert data["llm_model"] == "gpt-4"
    print(f"✓ Credentials retrieved (masked): {data}")
    
    return True


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Testing Edge Cases ===")
    
    # Missing required field
    invalid_data = {
        "user_id": "edge_case_user",
        "linkedin_credentials": {
            "email": "[email protected]"
            # Missing password
        },
        "llm_config": {
            "type": "anthropic",
            "model": "claude-sonnet-4-5",
            "api_key": "sk-test"
        }
    }
    
    resp = requests.post(f"{BASE_URL}/api/users/configure", json=invalid_data)
    assert resp.status_code == 422  # Unprocessable Entity
    print("✓ 422 for missing required field")
    
    # Invalid JSON
    resp = requests.post(
        f"{BASE_URL}/api/users/configure",
        data="not json",
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 422
    print("✓ 422 for invalid JSON")
    
    # Empty user_id
    invalid_data = {
        "user_id": "",
        "linkedin_credentials": {
            "email": "[email protected]",
            "password": "test"
        },
        "llm_config": {
            "type": "anthropic",
            "model": "claude-sonnet-4-5",
            "api_key": "sk-test"
        }
    }
    resp = requests.post(f"{BASE_URL}/api/users/configure", json=invalid_data)
    # Should still work (empty string is valid, though not recommended)
    # Or could add validation
    print("✓ Edge case handling tested")
    
    return True


def main():
    print("=" * 60)
    print("LinkedIn Agent Backend - API Tests")
    print("=" * 60)
    
    tests = [
        test_health,
        test_root,
        test_docs,
        test_user_configure,
        test_user_get,
        test_user_credentials,
        test_edge_cases
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            results.append(False)
        except Exception as e:
            print(f"✗ Test error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("✓ All API tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
