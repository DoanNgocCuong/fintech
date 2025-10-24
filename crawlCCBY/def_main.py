"""
YouTube Video Analysis Pipeline - Main Orchestrator

Mô tả:
    Công cụ chính kết hợp 3 bước xử lý để tạo pipeline hoàn chỉnh:
    Keyword → Video IDs → Copyright Check → Transcription & Experience Analysis
    
Luồng hoạt động:
    1. Tìm kiếm video Creative Commons từ keyword
    2. Kiểm tra copyright cho từng video
    3. Phân tích transcription và trích xuất kinh nghiệm cho video an toàn
    
Input: keyword (từ khóa tìm kiếm)
Output: JSON array chứa danh sách video với video_id, transcription, summary_of_experience

Tác giả: AI Assistant
Ngày tạo: 2025
"""

import os
import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Import các module từ 3 file
import importlib.util

# Import module 1
spec1 = importlib.util.spec_from_file_location("module1", "1_keywordAndCCBY2VideoID.py")
module1 = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(module1)
get_creative_commons_videos = module1.get_creative_commons_videos

# Import module 2
spec2 = importlib.util.spec_from_file_location("module2", "2_videoID2Detail2CheckNoCopyWrite.py")
module2 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(module2)
checkVideoCopyrightAndReturnID = module2.checkVideoCopyrightAndReturnID

# Import module 3
spec3 = importlib.util.spec_from_file_location("module3", "3_videoIDNoCopyWirte2Transcription2Experience.py")
module3 = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(module3)
videoID2Transcription2Experience = module3.videoID2Transcription2Experience

# Load environment variables
load_dotenv()

def getVideoTitleAndDescription(video_id):
    """
    Lấy title và description của video từ YouTube API
    """
    try:
        # Sử dụng module2 đã import
        video_details = module2.getVideoDetails(video_id)
        if video_details and 'snippet' in video_details:
            snippet = video_details['snippet']
            return {
                'title': snippet.get('title', ''),
                'description': snippet.get('description', '')
            }
        return {'title': '', 'description': ''}
    except Exception as e:
        print(f"❌ Lỗi khi lấy thông tin video {video_id}: {e}")
        return {'title': '', 'description': ''}

def process_single_video(video_id):
    """
    Xử lý một video: check copyright + transcription + experience analysis
    """
    print(f"🔍 Xử lý video: {video_id}")
    
    # Bước 1: Kiểm tra copyright
    safe_video_id = checkVideoCopyrightAndReturnID(video_id)
    if not safe_video_id:
        print(f"❌ Video {video_id} không an toàn")
        return None
    
    # Bước 2: Lấy thông tin video (title, description)
    video_info = getVideoTitleAndDescription(safe_video_id)
    
    # Bước 3: Phân tích transcription và kinh nghiệm
    try:
        analysis_result = videoID2Transcription2Experience(safe_video_id)
        if analysis_result:
            # Tạo JSON object cho video này
            video_data = {
                "video_id": analysis_result['video_id'],
                "title": video_info['title'],
                "description": video_info['description'],
                "transcription": analysis_result['transcription'],
                "summary_of_experience": analysis_result['experience']
            }
            print(f"✅ Hoàn thành video {video_id}")
            return video_data
        else:
            print(f"❌ Không thể phân tích video {video_id}")
            return None
    except Exception as e:
        print(f"❌ Lỗi khi phân tích video {video_id}: {e}")
        return None

def keyword2VideoAnalysis(keyword, max_results=3):
    """
    Pipeline chính: Keyword → Video Analysis
    
    Args:
        keyword (str): Từ khóa tìm kiếm
        max_results (int): Số lượng video tối đa để xử lý
        
    Returns:
        list: Danh sách JSON chứa video_id, transcription, summary_of_experience
    """
    print(f"🔍 Bắt đầu pipeline với keyword: '{keyword}'")
    print("=" * 60)
    
    # Bước 1: Tìm kiếm video Creative Commons
    print("📝 Bước 1: Tìm kiếm video Creative Commons...")
    search_results = get_creative_commons_videos(keyword, max_results=max_results)
    
    if not search_results or 'items' not in search_results:
        print("❌ Không tìm thấy video nào")
        return []
    
    video_ids = [item['id']['videoId'] for item in search_results['items']]
    print(f"✅ Tìm thấy {len(video_ids)} video: {video_ids}")
    
    # Bước 2 & 3: Xử lý song song tất cả video
    print(f"\n🚀 Bước 2 & 3: Xử lý song song {len(video_ids)} video...")
    print("   (Kiểm tra copyright + Phân tích transcription + Kinh nghiệm)")
    
    results = []
    
    # Sử dụng ThreadPoolExecutor để xử lý song song
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit tất cả video để xử lý song song
        future_to_video = {
            executor.submit(process_single_video, video_id): video_id 
            for video_id in video_ids
        }
        
        # Thu thập kết quả khi hoàn thành
        for future in as_completed(future_to_video):
            video_id = future_to_video[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    print(f"✅ Video {video_id} hoàn thành")
                else:
                    print(f"❌ Video {video_id} không thể xử lý")
            except Exception as e:
                print(f"❌ Lỗi xử lý video {video_id}: {e}")
    
    print(f"\n🎉 Pipeline hoàn thành: {len(results)}/{len(video_ids)} video đã được phân tích")
    return results

def main():
    """
    Main function để xử lý command line arguments
    """
    parser = argparse.ArgumentParser(
        description='YouTube Video Analysis Pipeline - Từ keyword đến phân tích kinh nghiệm',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python def_main.py --keyword "chứng khoán|đầu tư"
  python def_main.py --keyword "stock trading" --max-results 5
  python def_main.py --keyword "crypto" --output results.json
        """
    )
    
    parser.add_argument(
        '--keyword', 
        required=True,
        help='Từ khóa tìm kiếm video (có thể dùng "|" để phân cách nhiều từ khóa)'
    )
    
    parser.add_argument(
        '--max-results', 
        type=int,
        default=3,
        help='Số lượng video tối đa để xử lý (default: 3)'
    )
    
    parser.add_argument(
        '--output', 
        help='File để lưu kết quả JSON'
    )
    
    args = parser.parse_args()
    
    # Kiểm tra API keys
    youtube_key = os.getenv('YOUTUBE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not youtube_key:
        print("❌ Error: YOUTUBE_API_KEY not found in environment variables")
        return 1
    
    if not openai_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        return 1
    
    try:
        # Chạy pipeline
        results = keyword2VideoAnalysis(args.keyword, args.max_results)
        
        if results:
            print("\n" + "=" * 60)
            print("📊 KẾT QUẢ CUỐI CÙNG")
            print("=" * 60)
            print(f"🔍 Keyword: {args.keyword}")
            print(f"📹 Số video đã phân tích: {len(results)}")
            print(f"📝 Tổng transcription length: {sum(len(r['transcription']) for r in results)} characters")
            
            # Hiển thị tóm tắt từng video
            for i, result in enumerate(results, 1):
                print(f"\n📹 Video {i}: {result['video_id']}")
                print(f"   📺 Title: {result['title'][:100]}...")
                print(f"   📝 Description: {result['description'][:100]}...")
                print(f"   📝 Transcription: {len(result['transcription'])} characters")
                print(f"   🧠 Experience: {len(result['summary_of_experience'])} characters")
            
            # Lưu kết quả vào file nếu được yêu cầu
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"\n📝 Kết quả đã được lưu vào: {args.output}")
            
            # Hiển thị JSON mẫu
            print(f"\n📋 JSON Output (mẫu):")
            print(json.dumps(results[0], ensure_ascii=False, indent=2)[:500] + "...")
            
            return 0
        else:
            print("❌ Không có kết quả nào")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    # Chạy main function với command line arguments
    exit_code = main()
    sys.exit(exit_code)