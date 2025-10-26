import PyPDF2
import pdfplumber
import re
import os
from datetime import datetime

def extract_student_data_from_pdf(pdf_path, output_txt_path):
    """
    Trích xuất thông tin sinh viên từ file PDF và tạo file txt với format:
    mssv@st.hcmuaf.edu.vn|ddmmyyyy
    """
    
    students_data = []
    
    try:
        # Thử với pdfplumber trước (tốt hơn cho việc trích xuất text)
        with pdfplumber.open(pdf_path) as pdf:
            all_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text += page_text + "\n"
        
        print("Nội dung file PDF:")
        print("-" * 50)
        print(all_text[:1000])  # In ra 1000 ký tự đầu để xem cấu trúc
        print("-" * 50)
        
        # Tìm các pattern có thể cho MSSV (thường là dãy số)
        # MSSV thường có format như: 20123456, 2012345678, etc.
        mssv_pattern = r'\b(20\d{6,8})\b'  # MSSV thường bắt đầu bằng 20
        
        # Tìm pattern cho ngày sinh (có thể có nhiều format)
        date_patterns = [
            r'\b(\d{extract gg from pdf,2})/(\d{extract gg from pdf,2})/(\d{4})\b',  # dd/mm/yyyy
            r'\b(\d{extract gg from pdf,2})-(\d{extract gg from pdf,2})-(\d{4})\b',  # dd-mm-yyyy
            r'\b(\d{4})/(\d{extract gg from pdf,2})/(\d{extract gg from pdf,2})\b',  # yyyy/mm/dd
            r'\b(\d{4})-(\d{extract gg from pdf,2})-(\d{extract gg from pdf,2})\b',  # yyyy-mm-dd
        ]
        
        # Tìm tất cả MSSV
        mssv_matches = re.findall(mssv_pattern, all_text)
        print(f"Tìm thấy {len(mssv_matches)} MSSV: {mssv_matches[:10]}")  # In ra 10 MSSV đầu
        
        # Tìm tất cả ngày sinh
        all_dates = []
        for pattern in date_patterns:
            dates = re.findall(pattern, all_text)
            all_dates.extend(dates)
        
        print(f"Tìm thấy {len(all_dates)} ngày tháng: {all_dates[:10]}")  # In ra 10 ngày đầu
        
        # Phân tích cấu trúc để ghép MSSV với ngày sinh
        lines = all_text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Tìm MSSV trong dòng này
            mssv_in_line = re.findall(mssv_pattern, line)
            
            if mssv_in_line:
                mssv = mssv_in_line[0]
                
                # Tìm ngày sinh trong dòng này hoặc dòng kế tiếp
                birth_date = None
                
                # Kiểm tra trong dòng hiện tại
                for pattern in date_patterns:
                    date_matches = re.findall(pattern, line)
                    if date_matches:
                        birth_date = date_matches[0]
                        break
                
                # Nếu không tìm thấy trong dòng hiện tại, kiểm tra dòng kế tiếp
                if not birth_date and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    for pattern in date_patterns:
                        date_matches = re.findall(pattern, next_line)
                        if date_matches:
                            birth_date = date_matches[0]
                            break
                
                if birth_date:
                    # Chuyển đổi ngày sinh về format ddmmyyyy
                    try:
                        if len(birth_date) == 3:  # (dd, mm, yyyy) hoặc (yyyy, mm, dd)
                            if len(birth_date[0]) == 4:  # yyyy, mm, dd
                                year, month, day = birth_date
                            else:  # dd, mm, yyyy
                                day, month, year = birth_date
                            
                            # Đảm bảo định dạng đúng
                            day = day.zfill(2)
                            month = month.zfill(2)
                            
                            password = f"{day}{month}{year}"
                            username = f"{mssv}@st.hcmuaf.edu.vn"
                            
                            students_data.append(f"{username}|{password}")
                            print(f"Đã tạo: {username}|{password}")
                    
                    except Exception as e:
                        print(f"Lỗi xử lý ngày sinh cho MSSV {mssv}: {e}")
        
        # Ghi kết quả ra file
        if students_data:
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                for data in students_data:
                    f.write(data + '\n')
            
            print(f"\n✅ Đã tạo file {output_txt_path} với {len(students_data)} tài khoản")
            return True
        else:
            print("❌ Không tìm thấy dữ liệu sinh viên phù hợp")
            return False
            
    except ImportError as e:
        print(f"❌ Thiếu thư viện: {e}")
        print("Cần cài đặt: pip install pdfplumber PyPDF2")
        return False
    except Exception as e:
        print(f"❌ Lỗi xử lý file PDF: {e}")
        return False

def manual_extraction():
    """
    Cho phép nhập dữ liệu thủ công nếu không thể tự động trích xuất
    """
    print("\n🔍 Không thể tự động trích xuất. Hãy nhập thông tin thủ công:")
    print("Format: MSSV dd/mm/yyyy")
    print("Ví dụ: 20123456 15/06/1995")
    print("Gõ 'done' để kết thúc")
    
    students_data = []
    
    while True:
        user_input = input("\nNhập MSSV và ngày sinh: ").strip()
        
        if user_input.lower() == 'done':
            break
            
        try:
            parts = user_input.split()
            if len(parts) >= 2:
                mssv = parts[0]
                date_str = parts[1]
                
                # Parse ngày sinh
                if '/' in date_str:
                    day, month, year = date_str.split('/')
                elif '-' in date_str:
                    day, month, year = date_str.split('-')
                else:
                    print("❌ Format ngày không đúng. Sử dụng dd/mm/yyyy hoặc dd-mm-yyyy")
                    continue
                
                # Tạo password ddmmyyyy
                day = day.zfill(2)
                month = month.zfill(2)
                password = f"{day}{month}{year}"
                username = f"{mssv}@st.hcmuaf.edu.vn"
                
                students_data.append(f"{username}|{password}")
                print(f"✅ Đã thêm: {username}|{password}")
            else:
                print("❌ Format không đúng. Nhập: MSSV dd/mm/yyyy")
                
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    # Ghi file
    if students_data:
        output_file = "students_accounts.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for data in students_data:
                f.write(data + '\n')
        
        print(f"\n✅ Đã tạo file {output_file} với {len(students_data)} tài khoản")
        return True
    
    return False

if __name__ == "__main__":
    pdf_file = "Ds thi SHCD co vi tri ngoi.pdf"
    output_file = "students_accounts.txt"
    
    print("🔄 Đang xử lý file PDF...")
    
    if os.path.exists(pdf_file):
        success = extract_student_data_from_pdf(pdf_file, output_file)
        
        if not success:
            print("\n⚠️  Tự động trích xuất không thành công.")
            choice = input("Bạn có muốn nhập dữ liệu thủ công không? (y/n): ")
            if choice.lower() == 'y':
                manual_extraction()
    else:
        print(f"❌ Không tìm thấy file {pdf_file}")
        manual_extraction() 