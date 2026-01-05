"""
Filter Veterans by Birth Year
Lọc giữ lại các veterans có năm sinh trong khoảng chỉ định
Format: FIRST|LAST|Branch|Month|Day|Year
"""

import sys
import os

def filter_veterans_by_year(input_file, output_file=None, year_from=1941, year_to=1985):
    """Lọc veterans có năm sinh từ year_from đến year_to"""
    
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_filtered_{year_from}-{year_to}{ext}"
    
    # Đọc file
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    filtered_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Format: FIRST|LAST|Branch|Month|Day|Year
        parts = line.split('|')
        if len(parts) >= 6:
            try:
                year = int(parts[5].strip())
                if year_from <= year <= year_to:
                    filtered_lines.append(line)
            except ValueError:
                # Nếu không parse được năm, bỏ qua dòng đó
                continue
    
    # Ghi file kết quả
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered_lines))
    
    print(f"📊 Tổng số dòng ban đầu: {total_lines}")
    print(f"✅ Số dòng giữ lại (năm {year_from}-{year_to}): {len(filtered_lines)}")
    print(f"❌ Số dòng bị loại: {total_lines - len(filtered_lines)}")
    print(f"💾 Đã lưu vào: {output_file}")
    
    return len(filtered_lines)

if __name__ == '__main__':
    # Mặc định
    input_file = 'all_veterans.txt'
    year_from = 1941
    year_to = 1985
    
    # Lấy từ command line
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        year_from = int(sys.argv[2])
    if len(sys.argv) > 3:
        year_to = int(sys.argv[3])
    
    print(f"🔍 Đang lọc veterans từ năm {year_from} đến {year_to}...\n")
    filter_veterans_by_year(input_file, year_from=year_from, year_to=year_to)
    print("\n✅ Hoàn thành!")
