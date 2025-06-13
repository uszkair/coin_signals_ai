#!/usr/bin/env python3
"""
Test the settings API endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/settings"

def test_settings_api():
    """Test all settings API endpoints"""
    print("Testing Settings API...")
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test 1: Get all settings
        print("\n1️⃣ Testing GET /api/settings")
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Got settings: {len(settings)} fields")
            print(f"   - Auto trading enabled: {settings.get('auto_trading_enabled', 'N/A')}")
            print(f"   - Testnet mode: {settings.get('testnet_mode', 'N/A')}")
            print(f"   - Technical indicator weights: {bool(settings.get('technical_indicator_weights'))}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
        
        # Test 2: Get defaults
        print("\n2️⃣ Testing GET /api/settings/defaults")
        response = requests.get(f"{BASE_URL}/defaults")
        if response.status_code == 200:
            defaults = response.json()
            print(f"✅ Got defaults: {len(defaults)} fields")
            print(f"   - Default RSI period: {defaults.get('rsi_settings', {}).get('period', 'N/A')}")
            print(f"   - Default MACD fast: {defaults.get('macd_settings', {}).get('fast_period', 'N/A')}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
        
        # Test 3: Get specific category
        print("\n3️⃣ Testing GET /api/settings/category/technical_analysis")
        response = requests.get(f"{BASE_URL}/category/technical_analysis")
        if response.status_code == 200:
            tech_settings = response.json()
            print(f"✅ Got technical analysis settings: {len(tech_settings)} fields")
            for key in tech_settings:
                print(f"   - {key}: {bool(tech_settings[key])}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
        
        # Test 4: Update a setting
        print("\n4️⃣ Testing PUT /api/settings/category/technical_analysis")
        update_data = {
            "rsi_settings": {
                "period": 21,  # Change from default 14 to 21
                "overbought": 75,
                "oversold": 25
            }
        }
        response = requests.put(f"{BASE_URL}/category/technical_analysis", json=update_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Updated settings successfully")
            print(f"   - Message: {result.get('message', 'N/A')}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
        
        # Test 5: Verify the update
        print("\n5️⃣ Testing verification of update")
        response = requests.get(f"{BASE_URL}/category/technical_analysis")
        if response.status_code == 200:
            tech_settings = response.json()
            rsi_period = tech_settings.get('rsi_settings', {}).get('period')
            if rsi_period == 21:
                print(f"✅ Update verified: RSI period is now {rsi_period}")
            else:
                print(f"❌ Update failed: RSI period is {rsi_period}, expected 21")
                return False
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
        
        print("\n🎉 All tests passed! Settings API is working correctly.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_settings_api()
    if not success:
        exit(1)