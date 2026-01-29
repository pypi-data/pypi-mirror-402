# -*- coding: utf-8 -*-
"""동시 사용 제한 테스트"""

import requests
import json

BASE_URL = "https://clouvel-license-webhook.vnddns999.workers.dev"
TEST_LICENSE = "CLOUVEL-PRO-TEST123"

def test_license_status():
    """라이선스 상태 - 동시 사용 정보 확인"""
    print("\n=== License Status (동시 사용 정보) ===")
    try:
        r = requests.post(f"{BASE_URL}/license/status", json={
            "license_key": TEST_LICENSE
        }, timeout=10)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 동시 사용 정보 확인
        if "concurrent" in data:
            print("\n✅ 동시 사용 정보 포함됨!")
            print(f"  - active: {data['concurrent'].get('active')}")
            print(f"  - limit: {data['concurrent'].get('limit')}")
        else:
            print("\n⚠️ 동시 사용 정보 없음 (에러 응답일 수 있음)")

    except Exception as e:
        print(f"Error: {e}")

def test_list_machines():
    """머신 목록 - 활성 상태 확인"""
    print("\n=== List Machines (활성 상태) ===")
    try:
        r = requests.post(f"{BASE_URL}/license/machines", json={
            "license_key": TEST_LICENSE
        }, timeout=10)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))

        # 동시 사용 제한 정보 확인
        if "concurrent_limit" in data:
            print("\n✅ 동시 사용 제한 정보 포함됨!")
            print(f"  - total_registered: {data.get('total_registered')}")
            print(f"  - active_sessions: {data.get('active_sessions')}")
            print(f"  - concurrent_limit: {data.get('concurrent_limit')}")
        else:
            print("\n⚠️ 동시 사용 제한 정보 없음")

    except Exception as e:
        print(f"Error: {e}")

def test_health_check():
    """Health Check - 기능 목록 확인"""
    print("\n=== Health Check ===")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"Version: {data.get('version')}")
        print(f"Features: {json.dumps(data.get('features', {}), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("=" * 60)
    print("동시 사용 제한 테스트")
    print("=" * 60)

    test_health_check()
    test_license_status()
    test_list_machines()

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    main()
