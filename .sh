python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python vnstock_full_report.py -s TCB -o ./reports
# hoặc nhiều mã:
python vnstock_full_report.py --symbols TCB,HPG,CTD --start 2024-01-01 --end 2025-10-10 --out ./reports


---
python api.py --host 0.0.0.0 --port 8000
# prod:
nohup python api.py --host 0.0.0.0 --port 8000 > server.log 2>&1 &
