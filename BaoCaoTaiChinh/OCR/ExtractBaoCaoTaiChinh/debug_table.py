import re

with open('BIC_2024_1_5_1.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Tìm phần bảng cân đối
start = content.find('BẢNG CÂN ĐỐI KẾ TOÁN')
if start >= 0:
    section = content[start:start+2000]
    lines = section.split('\n')
    
    print(f"Found section, length: {len(section)}")
    print("\nFirst 30 lines:")
    for i, line in enumerate(lines[:30]):
        print(f"{i}: {repr(line[:100])}")

