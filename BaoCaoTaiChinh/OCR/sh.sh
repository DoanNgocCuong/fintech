python run_layout_ocr.py /home/ubuntu/cuong_dn/fintech/OCR/data/test-orrrr.pdf --out /home/ubuntu/cuong_dn/fintech/OCR/data/test-orrrr.md

watch -n 1 nvidia-smi

python3.11 -m venv .venv311


nohup python main_parallel_run_nganh_bao_hiem.py > output.log 2>&1 &
ps aux | grep main_parallel_run_nganh_bao_hiem.py
kill -9 PID


---


```bash
echo "kill -9 1646062" | at now + 4 hours
```



```bash
1d/1& [ubuntu@mgc-dev2-3090:~/fintech/OCR]└3 <.venv311> main(+10344/-7234,-6)* ± echo "kill -9 1646062" | at now + 4 hours
warning: commands will be executed using /bin/sh
job 1 at Tue Nov  4 06:21:00 2025
1d/1& [ubuntu@mgc-dev2-3090:~/fintech/OCR]└3 <.venv311> main(+10370/-7234,-6)* ±
```


---
```bash
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

```




**Hoàn toàn có thể!**  
Trong 4 giờ, nếu script của bạn **bị lỗi, tự dừng, hoặc hoàn thành xong và thoát**, thì với giải pháp “watchdog/run lại liên tục” vừa hướng dẫn bên trên, nó sẽ **tự động restart bao nhiêu lần cũng được**—miễn là mỗi lần kiểm tra thấy không còn tiến trình đang chạy.

Ví dụ:  
- Nếu chương trình cứ mỗi 1 giờ lại tự kết thúc (hoặc lỗi crash), watchdog sẽ restart ngay lập tức—trong 4 tiếng có thể chạy lại 4-5 lần hoặc nhiều hơn.
- Nếu chương trình chạy ổn từ đầu tới cuối 4 tiếng, thì chỉ chạy 1 lần duy nhất rồi bị kill khi hết thời gian.

**Điều kiện:**  
- Mỗi lần script bị dừng, watchdog sẽ phát hiện ra (nhờ dòng kiểm tra pgrep) và thực thi lệnh khởi động lại script.  
- Không có giới hạn số lần restart, miễn là trong 4 tiếng, script ngừng thì sẽ được bật lại ngay.

**Tóm lại:**  
- Bạn hoàn toàn có thể để script được restart 4-5 lần (hoặc nhiều hơn/ít hơn) trong 4 tiếng, tùy thuộc vào việc script bị dừng bao nhiêu lần.  
- Sau đúng 4 giờ, script và cả watchdog sẽ kết thúc, không restart nữa.

Nếu cần sửa đổi hoặc làm theo yêu cầu đặc biệt (ví dụ log số lần restart), chỉ cần chỉnh script như ý là được.


---

nohup bash sh_auto_restart_main.sh > auto_restart.log 2>&1 &
