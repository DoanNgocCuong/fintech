#!/usr/bin/env python3
"""
Simple test cho API
"""

import requests
import time

def simple_test():
    """
    Test đơn giản API
    """
    base_url = "http://localhost:8000"
    
    print("🧪 Simple API Test")
    print("=" * 30)
    
    # Đợi API khởi động
    print("⏳ Waiting for API...")
    time.sleep(10)
    
    try:
        # Test health
        print("1️⃣ Health check...")
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"✅ Health Status: {response.status_code}")
        
        # Test analyze
        print("\n2️⃣ Testing analyze...")
        payload = {"keyword": "crypto", "max_results": 1}
        response = requests.post(f"{base_url}/analyze", json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['success']}")
            print(f"📊 Total videos: {data['total_videos']}")
            
            if data['data']:
                video = data['data'][0]
                print(f"\n📹 Video: {video['video_id']}")
                print(f"📺 Title: {video['title'][:80]}...")
                print(f"📝 Description: {video['description'][:80]}...")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    simple_test()


