"""
YouTube Video Analysis API

Mô tả:
    REST API để phân tích video YouTube từ keyword đến kinh nghiệm.
    Sử dụng FastAPI để tạo API endpoints.

Endpoints:
    POST /analyze - Phân tích video từ keyword
    GET /health - Kiểm tra trạng thái API

Input: JSON với keyword và max_results
Output: JSON array chứa danh sách video với video_id, transcription, summary_of_experience

Tác giả: AI Assistant
Ngày tạo: 2025
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json
import os
from dotenv import load_dotenv

# Import pipeline chính
import importlib.util
spec = importlib.util.spec_from_file_location("def_main", "def_main.py")
def_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(def_main)
keyword2VideoAnalysis = def_main.keyword2VideoAnalysis

# Load environment variables
load_dotenv()

# Tạo FastAPI app
app = FastAPI(
    title="YouTube Video Analysis API",
    description="API để phân tích video YouTube từ keyword đến kinh nghiệm",
    version="1.0.0"
)

# Pydantic models
class AnalysisRequest(BaseModel):
    keyword: str
    max_results: Optional[int] = 3

class VideoResult(BaseModel):
    video_id: str
    title: str
    description: str
    transcription: str
    summary_of_experience: str

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    data: List[VideoResult]
    total_videos: int
    total_transcription_length: int

# API Endpoints
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "YouTube Video Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze": "Phân tích video từ keyword",
            "GET /health": "Kiểm tra trạng thái API"
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    # Kiểm tra API keys
    youtube_key = os.getenv('YOUTUBE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    status = "healthy"
    issues = []
    
    if not youtube_key:
        issues.append("YOUTUBE_API_KEY not found")
        status = "unhealthy"
    
    if not openai_key:
        issues.append("OPENAI_API_KEY not found")
        status = "unhealthy"
    
    return {
        "status": status,
        "issues": issues,
        "api_keys_configured": len(issues) == 0
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_videos(request: AnalysisRequest):
    """
    Phân tích video từ keyword
    
    Args:
        request: AnalysisRequest với keyword và max_results
        
    Returns:
        AnalysisResponse với kết quả phân tích
    """
    try:
        print(f"🔍 API Request: keyword='{request.keyword}', max_results={request.max_results}")
        
        # Chạy pipeline
        results = keyword2VideoAnalysis(request.keyword, request.max_results)
        
        if not results:
            return AnalysisResponse(
                success=False,
                message="Không tìm thấy video nào để phân tích",
                data=[],
                total_videos=0,
                total_transcription_length=0
            )
        
        # Chuyển đổi kết quả sang format API
        video_results = []
        total_transcription_length = 0
        
        for result in results:
            video_result = VideoResult(
                video_id=result["video_id"],
                title=result["title"],
                description=result["description"],
                transcription=result["transcription"],
                summary_of_experience=result["summary_of_experience"]
            )
            video_results.append(video_result)
            total_transcription_length += len(result["transcription"])
        
        return AnalysisResponse(
            success=True,
            message=f"Phân tích thành công {len(video_results)} video",
            data=video_results,
            total_videos=len(video_results),
            total_transcription_length=total_transcription_length
        )
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi phân tích video: {str(e)}"
        )

# @app.get("/analyze/{keyword}")
# async def analyze_videos_get(keyword: str, max_results: int = 3):
#     """
#     Phân tích video từ keyword (GET method)
    
#     Args:
#         keyword: Từ khóa tìm kiếm
#         max_results: Số lượng video tối đa (default: 3)
        
#     Returns:
#         JSON với kết quả phân tích
#     """
#     try:
#         print(f"🔍 GET Request: keyword='{keyword}', max_results={max_results}")
        
#         # Chạy pipeline
#         results = keyword2VideoAnalysis(keyword, max_results)
        
#         if not results:
#             return {
#                 "success": False,
#                 "message": "Không tìm thấy video nào để phân tích",
#                 "data": [],
#                 "total_videos": 0
#             }
        
#         return {
#             "success": True,
#             "message": f"Phân tích thành công {len(results)} video",
#             "data": results,
#             "total_videos": len(results),
#             "total_transcription_length": sum(len(r["transcription"]) for r in results)
#         }
        
#     except Exception as e:
#         print(f"❌ API Error: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Lỗi khi phân tích video: {str(e)}"
#         )

if __name__ == "__main__":
    # Chạy server
    print("🚀 Starting YouTube Video Analysis API...")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("📊 Analyze Endpoint: http://localhost:8000/analyze")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
