"""
YouTube Video Transcription to Experience Analysis Tool

Mô tả:
    Công cụ lấy transcription từ video YouTube và phân tích để trích xuất kinh nghiệm, tri thức.
    Sử dụng YouTube Transcript API để lấy phụ đề và OpenAI để phân tích nội dung.

Chức năng:
    - Lấy transcription từ video YouTube bằng video ID
    - Phân tích transcription bằng AI để trích xuất kinh nghiệm
    - Tổng hợp kiến thức và insights từ nội dung video
    - Hỗ trợ command line arguments

Cách sử dụng:
    # Phân tích video cụ thể
    python 3_videoIDNoCopyWirte2Transcription2Experience.py --video-id "VIDEO_ID"
    
    # Sử dụng video mặc định
    python 3_videoIDNoCopyWirte2Transcription2Experience.py
    
    # Lưu kết quả vào file
    python 3_videoIDNoCopyWirte2Transcription2Experience.py --video-id "VIDEO_ID" --output experience.txt

Yêu cầu:
    - OPENAI_API_KEY trong file .env
    - Thư viện: youtube-transcript-api, python-dotenv, openai

Quy trình:
    1. Lấy transcription từ video YouTube
    2. Phân tích nội dung bằng AI để trích xuất kinh nghiệm
    3. Tổng hợp insights và kiến thức
    4. Trả về báo cáo kinh nghiệm chi tiết

Tác giả: AI Assistant
Ngày tạo: 2025
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import openai

# Load environment variables from .env file
load_dotenv()

def getTranscription(video_id):
    """
    Lấy transcription từ video YouTube
    """
    try:
        print(f"📝 Đang lấy transcription cho video: {video_id}")
        
        # Thử lấy transcript với các ngôn ngữ khác nhau
        try:
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id, languages=['vi', 'en'])
        except:
            # Nếu không có transcript, thử lấy transcript mặc định
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id)
        
        # Kết hợp tất cả các đoạn transcript thành một văn bản
        full_text = ' '.join([segment.text for segment in transcript])
        print(f"✅ Đã lấy transcription thành công ({len(full_text)} ký tự)")
        return full_text
    except Exception as e:
        print(f"❌ Lỗi khi lấy transcription: {e}")
        print("💡 Gợi ý: Video có thể không có phụ đề hoặc không hỗ trợ transcript")
        return None

def transcription2Experience(transcription):
    """
    Phân tích transcription để trích xuất kinh nghiệm và tri thức
    """
    if not transcription:
        return "Không có transcription để phân tích"
    
    prompt = f"""
Bạn là một chuyên gia phân tích nội dung video để trích xuất kinh nghiệm và tri thức.

Nhiệm vụ: Phân tích transcription video sau và trích xuất:
1. **Kinh nghiệm chính** (3-5 điểm quan trọng nhất)
2. **Kiến thức chuyên môn** (thông tin kỹ thuật, phương pháp)
3. **Bài học rút ra** (insights, tips, lời khuyên)
4. **Ứng dụng thực tế** (cách áp dụng vào cuộc sống/công việc)
5. **Tóm tắt ngắn gọn** (1-2 câu tóm tắt nội dung chính)

Format trả về:
## KINH NGHIỆM CHÍNH
- [Điểm 1]
- [Điểm 2]
- [Điểm 3]

## KIẾN THỨC CHUYÊN MÔN
- [Kiến thức 1]
- [Kiến thức 2]

## BÀI HỌC RÚT RA
- [Bài học 1]
- [Bài học 2]

## ỨNG DỤNG THỰC TẾ
- [Ứng dụng 1]
- [Ứng dụng 2]

## TÓM TẮT
[Tóm tắt ngắn gọn]

Transcription:
{transcription}
"""

    try:
        print("🤖 Đang phân tích transcription bằng AI...")
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {'role': 'system', 'content': 'Bạn là một chuyên gia phân tích nội dung video để trích xuất kinh nghiệm và tri thức.'},
                {'role': 'user', 'content': prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        experience = response.choices[0].message.content.strip()
        print("✅ Phân tích hoàn thành")
        return experience
        
    except Exception as e:
        print(f"❌ Lỗi khi phân tích bằng AI: {e}")
        return f"Lỗi phân tích: {e}"

def videoID2Transcription2Experience(video_id):
    """
    Quy trình hoàn chỉnh: Video ID -> Transcription -> Experience
    """
    print(f"🎬 Bắt đầu phân tích video: {video_id}")
    print("=" * 60)
    
    # Bước 1: Lấy transcription
    transcription = getTranscription(video_id)
    if not transcription:
        return None
    
    # Bước 2: Phân tích để trích xuất kinh nghiệm
    experience = transcription2Experience(transcription)
    
    return {
        'video_id': video_id,
        'transcription': transcription,
        'experience': experience
    }

def main():
    """
    Main function để xử lý command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Phân tích video YouTube để trích xuất kinh nghiệm và tri thức',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 3_videoIDNoCopyWirte2Transcription2Experience.py --video-id "iaxoL4VMB_o"
  python 3_videoIDNoCopyWirte2Transcription2Experience.py  # Sử dụng video mặc định
  python 3_videoIDNoCopyWirte2Transcription2Experience.py --video-id "VIDEO_ID" --output experience.txt
        """
    )
    
    parser.add_argument(
        '--video-id', 
        help='YouTube video ID để phân tích'
    )
    
    parser.add_argument(
        '--output', 
        help='File để lưu kết quả phân tích'
    )
    
    args = parser.parse_args()
    
    # Kiểm tra API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("   Please set OPENAI_API_KEY in your .env file")
        return 1
    
    # Lấy video ID
    video_id = args.video_id if args.video_id else "iaxoL4VMB_o"
    
    try:
        # Thực hiện phân tích
        result = videoID2Transcription2Experience(video_id)
        
        if result:
            print("\n" + "=" * 60)
            print("📊 KẾT QUẢ PHÂN TÍCH")
            print("=" * 60)
            print(f"🎬 Video ID: {result['video_id']}")
            print(f"📝 Transcription length: {len(result['transcription'])} characters")
            print("\n🧠 KINH NGHIỆM VÀ TRI THỨC:")
            print("-" * 40)
            print(result['experience'])
            
            # Lưu kết quả vào file nếu được yêu cầu
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(f"Video ID: {result['video_id']}\n")
                    f.write(f"Transcription Length: {len(result['transcription'])} characters\n")
                    f.write(f"\nTranscription:\n{result['transcription']}\n")
                    f.write(f"\nExperience Analysis:\n{result['experience']}\n")
                print(f"\n📝 Kết quả đã được lưu vào: {args.output}")
            
            return 0
        else:
            print("❌ Không thể phân tích video")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    # Chạy main function với command line arguments
    exit_code = main()
    sys.exit(exit_code)