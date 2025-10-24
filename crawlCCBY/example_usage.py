#!/usr/bin/env python3
"""
Example usage of the copyright checking system
"""

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import our functions
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the module with a different name
import importlib.util
spec = importlib.util.spec_from_file_location("video_checker", "2_videoID2Detail2CheckNoCopyWrite.py")
video_checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video_checker)

# Now use the functions
checkVideoCopyrightAndReturnID = video_checker.checkVideoCopyrightAndReturnID
processMultipleVideos = video_checker.processMultipleVideos
getVideoDetails = video_checker.getVideoDetails
getDescription = video_checker.getDescription
getVideoLicense = video_checker.getVideoLicense

def example_single_video():
    """
    Example: Check a single video for copyright
    """
    print("🎬 EXAMPLE 1: Single Video Copyright Check")
    print("=" * 50)
    
    video_id = "4MhK5C37_fI"  # Example video from your curl request
    
    # Check if video is safe
    safe_video_id = checkVideoCopyrightAndReturnID(video_id)
    
    if safe_video_id:
        print(f"✅ Video {safe_video_id} is safe to use!")
        return safe_video_id
    else:
        print(f"❌ Video {video_id} has copyright restrictions")
        return None

def example_multiple_videos():
    """
    Example: Check multiple videos for copyright
    """
    print("\n🎬 EXAMPLE 2: Multiple Videos Copyright Check")
    print("=" * 50)
    
    # List of video IDs to check
    video_ids = [
        "4MhK5C37_fI",  # Your example video
        "gwLej8heN5c",  # Another example
        # Add more video IDs here
    ]
    
    # Process all videos
    safe_videos = processMultipleVideos(video_ids)
    
    return safe_videos

def example_get_video_details():
    """
    Example: Get detailed video information
    """
    print("\n🎬 EXAMPLE 3: Get Video Details")
    print("=" * 50)
    
    video_id = "4MhK5C37_fI"
    
    try:
        # Get full video details
        video_details = getVideoDetails(video_id)
        if video_details:
            snippet = video_details.get('snippet', {})
            status = video_details.get('status', {})
            
            print(f"📺 Title: {snippet.get('title', 'N/A')}")
            print(f"📝 Description: {snippet.get('description', 'N/A')[:200]}...")
            print(f"🏷️  License: {status.get('license', 'N/A')}")
            print(f"🔒 Privacy: {status.get('privacyStatus', 'N/A')}")
            print(f"📅 Published: {snippet.get('publishedAt', 'N/A')}")
            print(f"📺 Channel: {snippet.get('channelTitle', 'N/A')}")
            
            # Check copyright
            description = getDescription(video_id)
            license_info = getVideoLicense(video_id)
            
            print(f"\n🔍 Copyright Analysis:")
            print(f"   License: {license_info}")
            print(f"   Description length: {len(description)} characters")
            
            if license_info == 'creativeCommon':
                print("   ✅ Has Creative Commons license")
            else:
                print("   ❌ Does not have Creative Commons license")
                
        else:
            print("❌ Could not retrieve video details")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 YouTube Copyright Checker Examples")
    print("=" * 60)
    
    # Check if API keys are set
    youtube_key = os.getenv('YOUTUBE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not youtube_key:
        print("❌ YOUTUBE_API_KEY not found in .env file")
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in .env file")
    
    if youtube_key and openai_key:
        # Run examples
        example_single_video()
        example_multiple_videos()
        example_get_video_details()
    else:
        print("\n⚠️  Please set your API keys in the .env file first!")
        print("   Copy .env.example to .env and add your keys")
