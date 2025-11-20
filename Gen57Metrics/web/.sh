python .\app.py --host 0.0.0.0 --port 30013 --reload 
uvicorn app:app --host 0.0.0.0 --port 30013 --reload

nohup python app.py --host 0.0.0.0 --port 30013 --reload > output.log 2>&1 &
nohup python -m http.server 30014 > output_index.log 2>&1 &

Kiểm tra process nào đang sử dụng port 30005:**
```bash
	sudo lsof -i :30005
```
"Super User Do - List Open Files - Internet connections on port 30005" (Dùng quyền admin để liệt kê process nào đang sử dụng port 30005))
**6. Kill process theo PID (nếu có):**
```bash
sudo kill -9 <PID>
```
