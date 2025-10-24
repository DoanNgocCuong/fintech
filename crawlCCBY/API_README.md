# YouTube Video Analysis API

REST API để phân tích video YouTube từ keyword đến kinh nghiệm sử dụng AI.

## 🚀 Quick Start

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Cấu hình API keys
Tạo file `.env`:
```
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Khởi động API
```bash
# Cách 1: Sử dụng script khởi động (khuyến nghị)
python start_api.py

# Cách 2: Chạy trực tiếp
python main.py
```

### 4. Truy cập API
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Analyze Endpoint**: http://localhost:8000/analyze

## 📡 API Endpoints

### GET /
Thông tin API cơ bản
```json
{
  "message": "YouTube Video Analysis API",
  "version": "1.0.0",
  "endpoints": {
    "POST /analyze": "Phân tích video từ keyword",
    "GET /health": "Kiểm tra trạng thái API"
  }
}
```

### GET /health
Kiểm tra trạng thái API và API keys
```json
{
  "status": "healthy",
  "issues": [],
  "api_keys_configured": true
}
```

### POST /analyze
Phân tích video từ keyword

**Request Body:**
```json
{
  "keyword": "stock trading",
  "max_results": 3
}
```

**Response:**
```json
{
  "success": true,
  "message": "Phân tích thành công 2 video",
  "data": [
    {
      "video_id": "SSphmUezzFo",
      "transcription": "if you were going long here...",
      "summary_of_experience": "## KINH NGHIỆM CHÍNH\n- Sử dụng stop orders..."
    }
  ],
  "total_videos": 2,
  "total_transcription_length": 1228
}
```

### GET /analyze/{keyword}
Phân tích video từ keyword (GET method)

**URL Parameters:**
- `keyword`: Từ khóa tìm kiếm
- `max_results`: Số lượng video tối đa (default: 3)

**Example:**
```
GET /analyze/stock%20trading?max_results=2
```

## 🧪 Testing

### Test API với script
```bash
python test_api.py
```

### Test với curl
```bash
# Health check
curl http://localhost:8000/health

# POST analyze
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "stock trading", "max_results": 2}'

# GET analyze
curl "http://localhost:8000/analyze/stock%20trading?max_results=2"
```

### Test với Python requests
```python
import requests

# POST request
response = requests.post(
    "http://localhost:8000/analyze",
    json={"keyword": "crypto trading", "max_results": 3}
)
print(response.json())

# GET request
response = requests.get(
    "http://localhost:8000/analyze/crypto%20trading?max_results=2"
)
print(response.json())
```

## 🔧 Configuration

### Environment Variables
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `OPENAI_API_KEY`: OpenAI API key

### API Settings
- **Host**: 0.0.0.0 (all interfaces)
- **Port**: 8000
- **Reload**: True (auto-reload on code changes)
- **Log Level**: info

## 📊 Response Format

### Success Response
```json
{
  "success": true,
  "message": "Phân tích thành công X video",
  "data": [
    {
      "video_id": "string",
      "transcription": "string",
      "summary_of_experience": "string"
    }
  ],
  "total_videos": 2,
  "total_transcription_length": 1228
}
```

### Error Response
```json
{
  "detail": "Lỗi khi phân tích video: error message"
}
```

## 🚀 Deployment

### Production với Gunicorn
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

## 📝 Notes

- API sử dụng xử lý song song để tăng tốc độ
- Tự động lọc video Creative Commons và kiểm tra copyright
- Hỗ trợ cả POST và GET methods
- Có documentation tự động tại `/docs`
- Health check để kiểm tra trạng thái API keys

