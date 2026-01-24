
import requests
import json
import base64

BASE_URL = "http://127.0.0.1:5000"

def test_login():
    print("Testing Login...")
    payload = {
        "username": "admin",
        "password": "admin123",
        "cf_token": "XXXX" # Turnstile is stubbed in auth_routes for this secret
    }
    # Note: Cloudflare verification will pass because of the testing secret used in auth_routes.py
    # But we need to pass SOMETHING as cf_token.
    try:
        res = requests.post(f"{BASE_URL}/api/login", json=payload)
        data = res.json()
        if res.status_code == 200 and data.get("success"):
            print("✅ Login Successful")
            return data.get("access_token")
        else:
            print(f"❌ Login Failed: {data}")
    except Exception as e:
        print(f"❌ Login Request Failed: {e}")
    return None

def test_dashboard():
    print("Testing Dashboard Stats...")
    try:
        res = requests.get(f"{BASE_URL}/api/dashboard/stats")
        data = res.json()
        if res.status_code == 200 and "total_cases" in data:
            print(f"✅ Dashboard Stats: {data}")
        else:
            print(f"❌ Dashboard Stats Failed: {data}")
    except Exception as e:
        print(f"❌ Dashboard Request Failed: {e}")

def test_citizen_search():
    print("Testing Citizen Search...")
    # Using a case number from cases.json: CS/1460/1938
    # Title: KANAILAL DUTTA & ORS. Vs DEBENDRA CH. DUTTA & ORS.
    case_num = "CS/1460/1938"
    try:
        res = requests.get(f"{BASE_URL}/api/public/search", params={"caseNumber": case_num})
        data = res.json()
        if res.status_code == 200:
            print(f"✅ Citizen Search Successful: {data}")
            if data.get("plaintiff") != "Unknown" and data.get("defendant") != "Unknown":
                print("✅ Name Extraction Successful")
            else:
                print("❌ Name Extraction Failed")
        else:
            print(f"❌ Citizen Search Failed: {data}")
    except Exception as e:
        print(f"❌ Citizen Search Request Failed: {e}")

if __name__ == "__main__":
    # Wait for server to be up
    import time
    time.sleep(2)
    
    token = test_login()
    test_dashboard()
    test_citizen_search()
