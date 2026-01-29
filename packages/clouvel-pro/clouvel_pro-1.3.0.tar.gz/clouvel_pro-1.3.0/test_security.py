# -*- coding: utf-8 -*-
"""Clouvel Pro Security System Test (Week 1-3)"""

import requests
import json
import time

BASE_URL = "https://clouvel-license-webhook.vnddns999.workers.dev"
TEST_LICENSE = "CLOUVEL-PRO-TEST123"
ADMIN_KEY = "clouvel-admin-739bcbbacf47f56d90071bea65832ff1"

def test_health():
    """Week 1: Health Check"""
    print("\n=== Week 1: Health Check ===")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_content_protection():
    """Week 1: Content Protection (no license)"""
    print("\n=== Week 1: Content Protection ===")
    try:
        r = requests.post(f"{BASE_URL}/content/bundle", json={
            "license_key": "FAKE-KEY",
            "activated_at": "2025-01-01",
            "machine_id": "test-machine"
        }, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        return r.status_code in [401, 403, 404]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_heartbeat():
    """Week 2: Heartbeat System"""
    print("\n=== Week 2: Heartbeat ===")
    try:
        r = requests.post(f"{BASE_URL}/heartbeat", json={
            "license_key": TEST_LICENSE,
            "machine_id": "test-machine-001"
        }, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        return r.status_code in [200, 401, 403]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_rate_limit_stats():
    """Week 2: Rate Limit Stats"""
    print("\n=== Week 2: Rate Limit Stats ===")
    try:
        r = requests.get(f"{BASE_URL}/stats/rate-limits", timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_audit_stats():
    """Week 2: Audit Stats"""
    print("\n=== Week 2: Audit Stats ===")
    try:
        r = requests.get(f"{BASE_URL}/stats/audit",
                        headers={"Authorization": f"Bearer {ADMIN_KEY}"}, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_anomaly_stats():
    """Week 3: Anomaly Stats"""
    print("\n=== Week 3: Anomaly Stats ===")
    try:
        r = requests.get(f"{BASE_URL}/stats/anomaly",
                        headers={"Authorization": f"Bearer {ADMIN_KEY}"}, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_license_status():
    """Week 3: License Status"""
    print("\n=== Week 3: License Status ===")
    try:
        r = requests.post(f"{BASE_URL}/license/status", json={
            "license_key": TEST_LICENSE
        }, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        # 403: Invalid license (expected for test key)
        return r.status_code in [200, 403, 404]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_token_issue():
    """Week 3: Token Issue"""
    print("\n=== Week 3: Token Issue ===")
    try:
        r = requests.post(f"{BASE_URL}/token/issue", json={
            "license_key": TEST_LICENSE,
            "machine_id": "test-machine-001"
        }, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        return r.status_code in [200, 401, 403]
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_admin_dashboard():
    """Week 3: Admin Dashboard"""
    print("\n=== Week 3: Admin Dashboard ===")
    try:
        r = requests.get(f"{BASE_URL}/admin/dashboard",
                        headers={"Authorization": f"Bearer {ADMIN_KEY}"}, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:300]}")
        return r.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_admin_no_auth():
    """Week 3: Admin without auth (should fail)"""
    print("\n=== Week 3: Admin No Auth ===")
    try:
        r = requests.get(f"{BASE_URL}/admin/dashboard", timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
        return r.status_code == 401
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Clouvel Pro Security System Test")
    print("=" * 60)

    results = []

    # Week 1 Tests
    results.append(("Health Check", test_health()))
    results.append(("Content Protection", test_content_protection()))

    # Week 2 Tests
    results.append(("Heartbeat", test_heartbeat()))
    results.append(("Rate Limit Stats", test_rate_limit_stats()))
    results.append(("Audit Stats", test_audit_stats()))

    # Week 3 Tests
    results.append(("Anomaly Stats", test_anomaly_stats()))
    results.append(("License Status", test_license_status()))
    results.append(("Token Issue", test_token_issue()))
    results.append(("Admin Dashboard", test_admin_dashboard()))
    results.append(("Admin No Auth", test_admin_no_auth()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "[OK]" if result else "[X]"
        print(f"{symbol} {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "-" * 60)
    print(f"Total: {passed}/{len(results)} passed")

    if failed == 0:
        print("\nAll tests PASSED!")
    else:
        print(f"\n{failed} test(s) FAILED")

if __name__ == "__main__":
    main()
