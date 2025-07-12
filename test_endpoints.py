#!/usr/bin/env python3
"""
Test script to verify that the API endpoints work correctly.
This helps ensure the blueprint/router synchronization is working.
"""

import os
import sys

sys.path.append("src")

from fastapi.testclient import TestClient
from src.api.v1.main import app

# Create a test client
client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    print(f"Health check status: {response.status_code}")
    print(f"Health check response: {response.json()}")
    return response.status_code == 200


def test_courses_endpoint():
    """Test the courses endpoint"""
    response = client.get("/courses/")
    print(f"Courses endpoint status: {response.status_code}")
    if response.status_code == 200:
        print(f"Courses found: {len(response.json())}")
        return True
    else:
        print(f"Error: {response.json()}")
        return False


def test_docs_endpoint():
    """Test that the API docs are accessible"""
    response = client.get("/docs")
    print(f"API docs status: {response.status_code}")
    return response.status_code == 200


def main():
    print("Testing API endpoints...")
    print("=" * 40)

    tests = [
        ("Health Check", test_health_endpoint),
        ("Courses Endpoint", test_courses_endpoint),
        ("API Docs", test_docs_endpoint),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n🧪 Testing {name}...")
        try:
            result = test_func()
            results.append((name, result))
            print(f"✅ {name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            results.append((name, False))

    print("\n" + "=" * 40)
    print("SUMMARY:")
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")


if __name__ == "__main__":
    main()
