"""
YouTube Creative Commons Video Search Tool

Mô tả:
    Công cụ tìm kiếm video YouTube có giấy phép Creative Commons dựa trên từ khóa.
    Chỉ trả về các video được cấp phép Creative Commons, an toàn để sử dụng.

Chức năng:
    - Tìm kiếm video YouTube theo từ khóa
    - Lọc chỉ video có giấy phép Creative Commons
    - Hỗ trợ tìm kiếm với nhiều từ khóa (dùng "|" để phân cách)
    - Sắp xếp kết quả theo viewCount, relevance, date, etc.

Cách sử dụng:
    python 1_keywordAndCCBY2VideoID.py

Yêu cầu:
    - YOUTUBE_API_KEY trong file .env
    - Thư viện: requests, python-dotenv

Tác giả: AI Assistant
Ngày tạo: 2025
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_creative_commons_videos(keywords, max_results=3, order='viewCount', api_key=None):
    """
    Search YouTube for Creative Commons videos matching some keywords.
    Args:
        keywords (str): keywords or query string (can use "|" for "or" queries)
        max_results (int): number of results to return
        order (str): order by which to sort (e.g., 'viewCount')
        api_key (str): YouTube API key
    Returns:
        dict: API response, or None if failed
        
    curl: 
    """
    if api_key is None:
        # Load API key from environment variables
        api_key = os.getenv('YOUTUBE_API_KEY')
        if api_key is None:
            raise ValueError("YouTube API key not found. Please set YOUTUBE_API_KEY in your .env file")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "type": "video",
        "q": keywords,
        "videoLicense": "creativeCommon",
        "videoCategoryId": "28",  # Science & Technology (example)
        "maxResults": max_results,
        "order": order,
        "key": api_key
    }
    headers = {
        "Accept": "application/json"
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

if __name__ == "__main__":
    # Example usage:
    keywords = "chứng khoán|stock trading|đầu tư"
    # API key will be loaded from .env file automatically
    results = get_creative_commons_videos(keywords, max_results=3)
    print(results)