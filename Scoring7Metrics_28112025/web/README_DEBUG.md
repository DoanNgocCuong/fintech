# Hướng dẫn Debug - Frontend Backend Connection

## Logic hoạt động

### Local Development
- **Frontend**: Chạy trên bất kỳ port nào (ví dụ: 5500, 8080, 30016)
- **Backend**: Chạy trên port **30015**
- **Frontend → Backend**: Luôn gọi `http://localhost:30015/api/*`

### Production
- **Frontend**: Chạy trên server
- **Backend**: Chạy trên port **30015** hoặc port từ `.env`
- **Frontend → Backend**: Gọi `API_PRODUCTION_URL` từ `.env` (ví dụ: `http://103.253.20.30:30015`)

## Kiểm tra Backend đang chạy

### 1. Test Backend trực tiếp

```bash
# Test health endpoint
curl http://localhost:30015/api/health

# Test config endpoint
curl http://localhost:30015/api/config
```

**Kết quả mong đợi:**
```json
{
  "status": "ok",
  "message": "API is running"
}
```

### 2. Kiểm tra port đang được sử dụng

```bash
# Linux/Mac
sudo lsof -i :30015

# Windows
netstat -ano | findstr :30015
```

### 3. Start Backend nếu chưa chạy

```bash
cd Scoring7Metrics_28112025/web
python app.py --host 0.0.0.0 --port 30015
```

## Debug Frontend

### 1. Mở Browser Console (F12)

Kiểm tra các log:
- `🔵 Local mode: calling http://localhost:30015/api/config`
- `✅ Local API URL: http://localhost:30015/api`
- Hoặc error messages

### 2. Kiểm tra Network Tab

1. Mở DevTools → Network tab
2. Refresh page
3. Tìm request `config`
4. Kiểm tra:
   - **Request URL**: Phải là `http://localhost:30015/api/config` (local)
   - **Status**: Phải là `200 OK`
   - **Response**: Phải có `success: true`

### 3. Common Issues

#### Issue 1: CORS Error
**Error**: `Access to fetch at 'http://localhost:30015/api/config' from origin 'http://127.0.0.1:5500' has been blocked by CORS policy`

**Giải pháp**: 
- Backend đã có CORS middleware với `allow_origins=["*"]`
- Nếu vẫn lỗi, kiểm tra backend có đang chạy không

#### Issue 2: Connection Refused
**Error**: `Failed to fetch` hoặc `ERR_CONNECTION_REFUSED`

**Giải pháp**:
- Backend chưa chạy → Start backend
- Backend chạy sai port → Kiểm tra port trong `.env` và command line

#### Issue 3: 404 Not Found
**Error**: `404 File not found`

**Giải pháp**:
- Backend đang chạy nhưng không có endpoint `/api/config`
- Kiểm tra `app.py` có endpoint này không

#### Issue 4: Wrong Port
**Error**: Frontend gọi sai port

**Giải pháp**:
- Kiểm tra meta tag: `<meta name="api-backend-port" content="30015">`
- Hoặc backend port trong `.env`: `Scoring7Metrics_API_PORT=30015` (hoặc `API_PORT=30015` cho backward compatibility)

## Test Flow

### Step 1: Start Backend
```bash
cd Scoring7Metrics_28112025/web
python app.py --host 0.0.0.0 --port 30015
```

**Expected output:**
```
Starting server on http://0.0.0.0:30015
```

### Step 2: Test Backend API
```bash
curl http://localhost:30015/api/health
curl http://localhost:30015/api/config
```

### Step 3: Start Frontend
- Mở `index.html` trong browser
- Hoặc serve qua web server:
  ```bash
  python -m http.server 8080
  # Truy cập: http://localhost:8080/index.html
  ```

### Step 4: Check Console
- Mở DevTools (F12)
- Kiểm tra Console và Network tabs
- Phải thấy:
  - `🔵 Local mode: calling http://localhost:30015/api/config`
  - `✅ Local API URL: http://localhost:30015/api`
  - Request `config` với status `200 OK`

## Production Setup

### 1. Config `.env`
```env
API_HOST=0.0.0.0
Scoring7Metrics_API_PORT=30015
API_PRODUCTION_URL=http://103.253.20.30:30015
```

### 2. Frontend sẽ tự động:
- Detect không phải localhost
- Gọi `/api/config` để lấy `API_PRODUCTION_URL`
- Dùng `API_PRODUCTION_URL` cho tất cả API calls

## Quick Fix Checklist

- [ ] Backend đang chạy trên port 30015
- [ ] Test `curl http://localhost:30015/api/health` → OK
- [ ] Test `curl http://localhost:30015/api/config` → OK
- [ ] Frontend mở trong browser
- [ ] Console không có error
- [ ] Network tab: request `config` → 200 OK
- [ ] CORS headers có trong response

