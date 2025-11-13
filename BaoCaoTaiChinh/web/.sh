python .\app.py --host 0.0.0.0 --reload 
uvicorn app:app --host 0.0.0.0 --reload

nohup python app.py --host 0.0.0.0 --port 30011 --reload > output.log 2>&1 &
nohup python -m http.server 30012 > output_index.log 2>&1 &

