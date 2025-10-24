"""
YouTube Video Copyright Checker Tool

Mô tả:
    Công cụ kiểm tra video YouTube có vi phạm bản quyền hay không.
    Sử dụng YouTube API để lấy thông tin video và OpenAI để phân tích mô tả.

Chức năng:
    - Lấy thông tin chi tiết video từ YouTube API (title, description, license)
    - Kiểm tra giấy phép Creative Commons
    - Sử dụng AI (OpenAI) để phân tích mô tả video tìm dấu hiệu vi phạm bản quyền
    - Trả về video ID nếu video an toàn để sử dụng
    - Hỗ trợ command line arguments

Cách sử dụng:
    # Kiểm tra video cụ thể
    python 2_videoID2Detail2CheckNoCopyWrite.py --video-id "VIDEO_ID"
    
    # Sử dụng video mặc định
    python 2_videoID2Detail2CheckNoCopyWrite.py
    
    # Lưu kết quả vào file
    python 2_videoID2Detail2CheckNoCopyWrite.py --video-id "VIDEO_ID" --output safe_video.txt

Yêu cầu:
    - YOUTUBE_API_KEY trong file .env
    - OPENAI_API_KEY trong file .env
    - Thư viện: requests, python-dotenv, openai

Quy trình kiểm tra:
    1. Lấy thông tin video từ YouTube API
    2. Kiểm tra license có phải Creative Commons không
    3. Phân tích mô tả video bằng AI để tìm dấu hiệu bản quyền
    4. Trả về video ID nếu an toàn, None nếu có vi phạm

Tác giả: AI Assistant
Ngày tạo: 2025
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

def getVideoDetails(video_id, api_key=None):
    """
    Get video details including description and status from YouTube API
    """
    if api_key is None:
        api_key = os.getenv('YOUTUBE_API_KEY')
        if api_key is None:
            raise ValueError("YouTube API key not found. Please set YOUTUBE_API_KEY in your .env file")
    
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "status,snippet",
        "id": video_id,
        "key": api_key
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['items']:
            return data['items'][0]
        else:
            return None
    else:
        print(f"Error getting video details: {response.status_code}")
        return None

def getDescription(video_id):
    """
    Get video description from YouTube API
    """
    video_details = getVideoDetails(video_id)
    if video_details and 'snippet' in video_details:
        return video_details['snippet'].get('description', '')
    return ''

def getVideoLicense(video_id):
    """
    Get video license information from YouTube API
    """
    video_details = getVideoDetails(video_id)
    if video_details and 'status' in video_details:
        return video_details['status'].get('license', '')
    return ''

def LLMcheckNoCopyWrite(input_description):
    """
    Use OpenAI to check if description has copyright violations
    Returns: True if no copyright violation, False if has copyright violation
    """
    prompt = (
        "You are an AI assistant.\n"
        "Your task: Analyze the following YouTube video description to determine if it contains any copyright violations or copyrighted content.\n"
        "Look for:\n"
        "- Copyright notices (©, Copyright, Bản quyền)\n"
        "- Claims of ownership by companies or individuals\n"
        "- Restrictions on copying or distribution\n"
        "- Trademarked content or brand names\n"
        "- Any statements indicating the content is copyrighted\n\n"
        "Return True if the description appears to be copyright-free or explicitly states it's free to use.\n"
        "Return False if the description contains copyright claims or restrictions.\n"
        "Only return 'True' or 'False', nothing else.\n\n"
        f"Description:\n{input_description}"
    )

    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {'role': 'system', 'content': 'Bạn là một trợ lý AI.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=5,
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        print(f"🤖 LLM Response: {content}")
        return content.lower().startswith("true")
    except Exception as e:
        print(f"❌ Error in LLM analysis: {e}")
        return False

def checkVideoCopyrightAndReturnID(video_id):
    """
    Check if video has no copyright violations and return video ID if safe
    Returns: video_id if safe, None if has copyright issues
    """
    print(f"\n🔍 Checking video ID: {video_id}")
    
    # Get video details
    description = getDescription(video_id)
    license_info = getVideoLicense(video_id)
    
    print(f"Video License: {license_info}")
    print(f"Description: {description[:200]}...")
    
    # Check if it's Creative Commons license
    if license_info == 'creativeCommon':
        print("✅ Video has Creative Commons license")
        # Check description for copyright claims
        is_safe = LLMcheckNoCopyWrite(description)
        
        if is_safe:
            print(f"✅ Video {video_id} is safe to use - no copyright violations detected")
            return video_id
        else:
            print(f"❌ Video {video_id} has copyright restrictions in description")
            return None
    else:
        print("❌ Video does not have Creative Commons license")
        return None

def main():
    """
    Main function to handle single video ID processing
    """
    parser = argparse.ArgumentParser(
        description='Check a single YouTube video for copyright restrictions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 2_videoID2Detail2CheckNoCopyWrite.py --video-id "4MhK5C37_fI"
  python 2_videoID2Detail2CheckNoCopyWrite.py  # Uses default video ID
        """
    )
    
    parser.add_argument(
        '--video-id', 
        help='YouTube video ID to check'
    )
    
    parser.add_argument(
        '--output', 
        help='Output file to save safe video ID'
    )
    
    args = parser.parse_args()
    
    # Check if API keys are available
    youtube_key = os.getenv('YOUTUBE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not youtube_key:
        print("❌ Error: YOUTUBE_API_KEY not found in environment variables")
        print("   Please set YOUTUBE_API_KEY in your .env file")
        return 1
    
    if not openai_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("   Please set OPENAI_API_KEY in your .env file")
        return 1
    
    # Get video ID
    video_id = args.video_id if args.video_id else "iaxoL4VMB_o"
    
    print(f"🎬 Processing video ID: {video_id}")
    print("=" * 50)
    
    try:
        safe_video_id = checkVideoCopyrightAndReturnID(video_id)
        
        if safe_video_id:
            print(f"✅ RESULT: Video {safe_video_id} is SAFE to use")
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(safe_video_id)
                print(f"📝 Safe video ID saved to: {args.output}")
            return 0
        else:
            print(f"❌ RESULT: Video {video_id} has COPYRIGHT restrictions")
            return 1
            
    except Exception as e:
        print(f"❌ Error processing video: {e}")
        return 1

if __name__ == "__main__":
    # Run the main function with command line arguments
    exit_code = main()
    sys.exit(exit_code)