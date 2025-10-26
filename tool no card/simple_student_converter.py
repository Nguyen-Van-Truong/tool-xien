#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys

def process_text_input():
    """
    Xử lý dữ liệu từ text input hoặc paste
    """
    print("=" * 60)
    print("🔄 CÔNG CỤ CHUYỂN ĐỔI DỮ LIỆU SINH VIÊN")
    print("=" * 60)
    print("Format đầu ra: mssv@st.hcmuaf.edu.vn|ddmmyyyy")
    print("Trong đó:")
    print("- mssv: Mã số sinh viên")
    print("- ddmmyyyy: Ngày tháng năm sinh (password)")
    print("-" * 60)
    
    students_data = []
    
    print("\n📝 CÁCH extract gg from pdf: Nhập từng dòng")
    print("Format: MSSV dd/mm/yyyy Họ_Tên")
    print("Ví dụ: 20123456 15/06/1995 Nguyen Van A")
    print("Hoặc: 20123456 15-06-1995 Nguyen Van A")
    print("Gõ 'paste' để dán toàn bộ dữ liệu")
    print("Gõ 'done' để kết thúc\n")
    
    while True:
        user_input = input("➤ Nhập dữ liệu: ").strip()
        
        if user_input.lower() == 'done':
            break
        elif user_input.lower() == 'paste':
            print("\n📋 Hãy paste toàn bộ dữ liệu vào đây (kết thúc bằng dòng trống):")
            paste_data = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                paste_data.append(line)
            
            # Xử lý dữ liệu đã paste
            for line in paste_data:
                result = parse_student_line(line)
                if result:
                    students_data.append(result)
                    print(f"✅ Đã thêm: {result}")
            continue
        
        # Xử lý dòng đơn lẻ
        result = parse_student_line(user_input)
        if result:
            students_data.append(result)
            print(f"✅ Đã thêm: {result}")
    
    # Ghi file kết quả
    if students_data:
        save_results(students_data)
    else:
        print("❌ Không có dữ liệu để lưu")

def parse_student_line(line):
    """
    Phân tích một dòng dữ liệu và trích xuất thông tin sinh viên
    """
    line = line.strip()
    if not line:
        return None
    
    try:
        # Pattern để tìm MSSV (thường bắt đầu bằng số 20 và có 8-10 chữ số)
        mssv_patterns = [
            r'\b(20\d{6,8})\b',  # 20xxxxxx hoặc 20xxxxxxxx
            r'\b(19\d{6,8})\b',  # 19xxxxxx hoặc 19xxxxxxxx  
            r'\b(\d{8,10})\b'    # Bất kỳ dãy 8-10 số nào
        ]
        
        # Pattern để tìm ngày sinh
        date_patterns = [
            r'\b(\d{extract gg from pdf,2})[/-](\d{extract gg from pdf,2})[/-](\d{4})\b',  # dd/mm/yyyy hoặc dd-mm-yyyy
            r'\b(\d{4})[/-](\d{extract gg from pdf,2})[/-](\d{extract gg from pdf,2})\b',  # yyyy/mm/dd hoặc yyyy-mm-dd
        ]
        
        mssv = None
        birth_date = None
        
        # Tìm MSSV
        for pattern in mssv_patterns:
            match = re.search(pattern, line)
            if match:
                mssv = match.group(1)
                break
        
        # Tìm ngày sinh
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                if len(match.group(1)) == 4:  # yyyy/mm/dd
                    year, month, day = match.groups()
                else:  # dd/mm/yyyy
                    day, month, year = match.groups()
                birth_date = (day, month, year)
                break
        
        if mssv and birth_date:
            day, month, year = birth_date
            
            # Đảm bảo format đúng
            day = day.zfill(2)
            month = month.zfill(2)
            
            password = f"{day}{month}{year}"
            username = f"{mssv}@st.hcmuaf.edu.vn"
            
            return f"{username}|{password}"
        else:
            print(f"⚠️  Không thể phân tích dòng: {line}")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi xử lý dòng '{line}': {e}")
        return None

def save_results(students_data):
    """
    Lưu kết quả ra file
    """
    output_file = "students_accounts.txt"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for data in students_data:
                f.write(data + '\n')
        
        print(f"\n✅ Đã tạo file '{output_file}' với {len(students_data)} tài khoản")
        print(f"📍 Đường dẫn: {os.path.abspath(output_file)}")
        
        # Hiển thị một vài dòng đầu
        print("\n📄 Nội dung file:")
        print("-" * 40)
        for i, data in enumerate(students_data[:5]):
            print(data)
        if len(students_data) > 5:
            print(f"... và {len(students_data) - 5} dòng khác")
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Lỗi ghi file: {e}")

def process_existing_file():
    """
    Xử lý file text có sẵn
    """
    print("\n📂 Nhập tên file cần xử lý (ví dụ: data.txt):")
    filename = input("➤ Tên file: ").strip()
    
    if not os.path.exists(filename):
        print(f"❌ Không tìm thấy file '{filename}'")
        return
    
    try:
        students_data = []
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"📖 Đang xử lý {len(lines)} dòng...")
        
        for i, line in enumerate(lines, 1):
            result = parse_student_line(line)
            if result:
                students_data.append(result)
                print(f"✅ Dòng {i}: {result}")
            else:
                print(f"⚠️  Dòng {i}: Không thể xử lý")
        
        if students_data:
            save_results(students_data)
        else:
            print("❌ Không tìm thấy dữ liệu hợp lệ trong file")
            
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")

def main():
    """
    Hàm main với menu lựa chọn
    """
    while True:
        print("\n" + "=" * 50)
        print("🎯 CHỌN CÁCH THỨC XỬ LÝ:")
        print("=" * 50)
        print("extract gg from pdf. Nhập dữ liệu thủ công")
        print("2. Xử lý file text có sẵn")
        print("3. Hướng dẫn format dữ liệu")
        print("4. Thoát")
        print("-" * 50)
        
        choice = input("➤ Chọn (extract gg from pdf-4): ").strip()
        
        if choice == 'extract gg from pdf':
            process_text_input()
        elif choice == '2':
            process_existing_file()
        elif choice == '3':
            show_format_guide()
        elif choice == '4':
            print("👋 Tạm biệt!")
            break
        else:
            print("❌ Lựa chọn không hợp lệ!")

def show_format_guide():
    """
    Hiển thị hướng dẫn format dữ liệu
    """
    print("\n" + "=" * 60)
    print("📋 HƯỚNG DẪN FORMAT DỮ LIỆU")
    print("=" * 60)
    print("Dữ liệu đầu vào có thể có các format sau:")
    print()
    print("extract gg from pdf. MSSV + Ngày sinh + Tên:")
    print("   20123456 15/06/1995 Nguyen Van A")
    print("   20234567 20-12-1996 Tran Thi B")
    print()
    print("2. Chỉ MSSV + Ngày sinh:")
    print("   20123456 15/06/1995")
    print("   20234567 20-12-1996")
    print()
    print("3. Dữ liệu trong bảng (có thể có nhiều cột):")
    print("   STT | MSSV     | Họ tên      | Ngày sinh")
    print("   extract gg from pdf   | 20123456 | Nguyen Van A| 15/06/1995")
    print("   2   | 20234567 | Tran Thi B  | 20/12/1996")
    print()
    print("📤 Kết quả đầu ra:")
    print("   20123456@st.hcmuaf.edu.vn|15061995")
    print("   20234567@st.hcmuaf.edu.vn|20121996")
    print()
    print("⚠️  Lưu ý:")
    print("- MSSV phải là dãy số (thường 8-10 chữ số)")
    print("- Ngày sinh có thể dùng / hoặc - làm phân cách")
    print("- Hỗ trợ format dd/mm/yyyy hoặc yyyy/mm/dd")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Đã dừng chương trình!")
    except Exception as e:
        print(f"\n❌ Lỗi không mong đợi: {e}") 