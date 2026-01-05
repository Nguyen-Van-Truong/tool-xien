"""
Filter Veterans by Birth Year - IN PLACE
Lọc giữ lại các veterans có năm sinh trong khoảng chỉ định
Ghi đè trực tiếp vào file gốc (không tạo file mới)
Format: FIRST|LAST|Branch|Month|Day|Year
"""

import sys
import os
import glob

def filter_veterans_by_year(input_file, year_from=1946, year_to=1987, in_place=True):
    """Lọc veterans có năm sinh từ year_from đến year_to"""
    
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
    
    # Ghi đè file gốc
    output_file = input_file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered_lines))
    
    removed = total_lines - len(filtered_lines)
    print(f"📄 {os.path.basename(input_file)}: {total_lines} → {len(filtered_lines)} (loại {removed})")
    
    return len(filtered_lines), removed

def filter_all_txt_files(directory, year_from=1946, year_to=1987):
    """Lọc tất cả file .txt trong thư mục (trừ file script)"""
    
    txt_files = glob.glob(os.path.join(directory, '*.txt'))
    
    total_kept = 0
    total_removed = 0
    file_count = 0
    
    print(f"🔍 Tìm thấy {len(txt_files)} file .txt trong thư mục")
    print(f"📅 Lọc năm sinh: {year_from} - {year_to}")
    print("=" * 60)
    
    for txt_file in txt_files:
        # Bỏ qua file cmd run.txt
        if 'cmd run' in txt_file.lower():
            print(f"⏭️  Bỏ qua: {os.path.basename(txt_file)}")
            continue
            
        kept, removed = filter_veterans_by_year(txt_file, year_from, year_to)
        total_kept += kept
        total_removed += removed
        file_count += 1
    
    print("=" * 60)
    print(f"✅ Đã xử lý: {file_count} file")
    print(f"📊 Tổng giữ lại: {total_kept}")
    print(f"❌ Tổng loại bỏ: {total_removed}")

if __name__ == '__main__':
    # Mặc định
    year_from = 1946
    year_to = 1987
    
    # Lấy từ command line
    if len(sys.argv) > 1:
        year_from = int(sys.argv[1])
    if len(sys.argv) > 2:
        year_to = int(sys.argv[2])
    
    # Lấy thư mục hiện tại
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"\n🔄 Lọc TẤT CẢ file .txt trong thư mục...")
    print(f"📂 {current_dir}\n")
    
    filter_all_txt_files(current_dir, year_from, year_to)
    
    print("\n✅ Hoàn thành!")
