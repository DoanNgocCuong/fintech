#!/usr/bin/env python3
"""
Quick test cho API
"""

import requests
import json
import time

def quick_test():
    """
    Test nhanh API
    """
    base_url = "http://localhost:8000"
    
    print("🧪 Quick API Test")
    print("=" * 30)
    
    # Đợi API khởi động
    print("⏳ Waiting for API...")
    time.sleep(5)
    
    try:
        # Test health
        print("1️⃣ Health check...")
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test analyze
        print("\n2️⃣ Testing analyze...")
        payload = {"keyword": "crypto", "max_results": 1}
        response = requests.post(f"{base_url}/analyze", json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data['success']}")
            print(f"Total videos: {data['total_videos']}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()

