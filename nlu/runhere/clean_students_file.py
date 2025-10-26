#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def clean_students_file():
    """Xóa tất cả tài khoản trong accounts_to_remove.txt khỏi students_accounts.txt"""
    
    print("TOOL DON DEP FILE STUDENTS_ACCOUNTS.TXT")
    print("="*60)
    
    try:
        # Đọc danh sách tài khoản cần xóa
        print("Doc danh sach tai khoan can xoa...")
        accounts_to_remove = set()
        
        try:
            with open("accounts_to_remove.txt", 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                # Bỏ qua comment và dòng trống
                if line and not line.startswith('#'):
                    if '|' in line:
                        # Có password - lấy email
                        username = line.split('|')[0].strip()
                        accounts_to_remove.add(username)
                    else:
                        # Chỉ có email
                        accounts_to_remove.add(line.strip())
            
            print(f"[OK] Da doc {len(accounts_to_remove)} tai khoan can xoa")
            
        except Exception as e:
            print(f"[ERROR] Loi doc accounts_to_remove.txt: {e}")
            return
        
        # Đọc file students_accounts.txt
        print("Doc file students_accounts.txt...")
        
        try:
            with open("students_accounts.txt", 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            print(f"[OK] Da doc {len(all_lines)} dong tu students_accounts.txt")
            
        except Exception as e:
            print(f"[ERROR] Loi doc students_accounts.txt: {e}")
            return
        
        # Backup file gốc
        import shutil
        from datetime import datetime
        backup_filename = f"students_accounts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        shutil.copy("students_accounts.txt", backup_filename)
        print(f"[OK] Da backup file goc: {backup_filename}")
        
        # Lọc bỏ các tài khoản trong danh sách xóa
        print("Loc bo cac tai khoan...")
        
        remaining_lines = []
        removed_count = 0
        
        for line in all_lines:
            line_stripped = line.strip()
            if '|' in line_stripped:
                username = line_stripped.split('|')[0].strip()
                
                if username in accounts_to_remove:
                    removed_count += 1
                    print(f"[XOA] {username}")
                else:
                    remaining_lines.append(line)
            else:
                # Giữ lại các dòng không phải tài khoản
                remaining_lines.append(line)
        
        print(f"[OK] Da xoa {removed_count} tai khoan")
        print(f"[OK] Con lai {len(remaining_lines)} dong")
        
        # Ghi file mới
        print("Ghi file students_accounts.txt moi...")
        
        with open("students_accounts.txt", 'w', encoding='utf-8') as f:
            f.writelines(remaining_lines)
        
        # Tạo file báo cáo
        with open("cleaning_report.txt", 'w', encoding='utf-8') as f:
            f.write("# BAO CAO DON DEP FILE STUDENTS_ACCOUNTS.TXT\n")
            f.write(f"# Thoi gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## THONG KE:\n")
            f.write(f"- Tai khoan goc: {len(all_lines)}\n")
            f.write(f"- Da xoa: {removed_count}\n")
            f.write(f"- Con lai: {len(remaining_lines)}\n")
            f.write(f"- File backup: {backup_filename}\n\n")
            f.write(f"## DANH SACH DA XOA:\n")
            for username in accounts_to_remove:
                if any(username in line for line in all_lines):
                    f.write(f"- {username}\n")
        
        print("[OK] HOAN THANH DON DEP!")
        print(f"KET QUA:")
        print(f"   - Tai khoan goc: {len(all_lines)}")
        print(f"   - Da xoa: {removed_count}")
        print(f"   - Con lai: {len(remaining_lines)}")
        print(f"   - File backup: {backup_filename}")
        print(f"   - Bao cao: cleaning_report.txt")
        
        print(f"\n[OK] FILE STUDENTS_ACCOUNTS.TXT DA SACH!")
        print(f"[OK] CO THE CHAY TOOL VOI {len(remaining_lines)} TAI KHOAN MOI!")
        
    except Exception as e:
        print(f"[ERROR] Loi tong quat: {e}")

if __name__ == "__main__":
    clean_students_file()
    input("\nNhan Enter de thoat...")