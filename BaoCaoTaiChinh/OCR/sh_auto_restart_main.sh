#!/bin/bash

END_TIME=$(( $(date +%s) + 4*3600 ))  # Thời điểm dừng sau 4h

while [ $(date +%s) -lt $END_TIME ]
do
    # Kiểm tra tiến trình python có chạy không
    PID=$(pgrep -f main_parallel_run_nganh_bao_hiem.py)
    if [ -z "$PID" ]; then
        nohup python main_parallel_run_nganh_bao_hiem.py > output.log 2>&1 &
        PID=$!
        echo "Restarted process with PID $PID at $(date)"
    fi
    sleep 30  # kiểm tra mỗi 30 giây (tuỳ chỉnh)
done

# Sau 4h: kill tiến trình (nếu đang chạy)
PID=$(pgrep -f main_parallel_run_nganh_bao_hiem.py)
if [ ! -z "$PID" ]; then
    kill -9 $PID
    echo "Killed process $PID at $(date)"
fi
