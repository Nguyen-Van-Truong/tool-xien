#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def clean_students_file():
    """Xóa tất cả tài khoản trong accounts_to_remove.txt khỏi students_accounts.txt"""
    
    print("🧹 TOOL DỌN DẸP FILE STUDENTS_ACCOUNTS.TXT")
    print("="*60)
    
    try:
        # Đọc danh sách tài khoản cần xóa
        print("📖 Đọc danh sách tài khoản cần xóa...")
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
            
            print(f"✅ Đã đọc {len(accounts_to_remove)} tài khoản cần xóa")
            
        except Exception as e:
            print(f"❌ Lỗi đọc accounts_to_remove.txt: {e}")
            return
        
        # Đọc file students_accounts.txt
        print("📖 Đọc file students_accounts.txt...")
        
        try:
            with open("students_accounts.txt", 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            print(f"✅ Đã đọc {len(all_lines)} dòng từ students_accounts.txt")
            
        except Exception as e:
            print(f"❌ Lỗi đọc students_accounts.txt: {e}")
            return
        
        # Backup file gốc
        import shutil
        from datetime import datetime
        backup_filename = f"students_accounts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        shutil.copy("students_accounts.txt", backup_filename)
        print(f"💾 Đã backup file gốc: {backup_filename}")
        
        # Lọc bỏ các tài khoản trong danh sách xóa
        print("🔍 Lọc bỏ các tài khoản...")
        
        remaining_lines = []
        removed_count = 0
        
        for line in all_lines:
            line_stripped = line.strip()
            if '|' in line_stripped:
                username = line_stripped.split('|')[0].strip()
                
                if username in accounts_to_remove:
                    removed_count += 1
                    print(f"❌ Xóa: {username}")
                else:
                    remaining_lines.append(line)
            else:
                # Giữ lại các dòng không phải tài khoản
                remaining_lines.append(line)
        
        print(f"🗑️ Đã xóa {removed_count} tài khoản")
        print(f"📋 Còn lại {len(remaining_lines)} dòng")
        
        # Ghi file mới
        print("💾 Ghi file students_accounts.txt mới...")
        
        with open("students_accounts.txt", 'w', encoding='utf-8') as f:
            f.writelines(remaining_lines)
        
        # Tạo file báo cáo
        with open("cleaning_report.txt", 'w', encoding='utf-8') as f:
            f.write("# BÁO CÁO DỌN DẸP FILE STUDENTS_ACCOUNTS.TXT\n")
            f.write(f"# Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## THỐNG KÊ:\n")
            f.write(f"- Tài khoản gốc: {len(all_lines)}\n")
            f.write(f"- Đã xóa: {removed_count}\n")
            f.write(f"- Còn lại: {len(remaining_lines)}\n")
            f.write(f"- File backup: {backup_filename}\n\n")
            f.write(f"## DANH SÁCH ĐÃ XÓA:\n")
            for username in accounts_to_remove:
                if any(username in line for line in all_lines):
                    f.write(f"- {username}\n")
        
        print("✅ HOÀN THÀNH DỌN DẸP!")
        print(f"📊 Kết quả:")
        print(f"   - Tài khoản gốc: {len(all_lines)}")
        print(f"   - Đã xóa: {removed_count}")
        print(f"   - Còn lại: {len(remaining_lines)}")
        print(f"   - File backup: {backup_filename}")
        print(f"   - Báo cáo: cleaning_report.txt")
        
        print(f"\n🎯 FILE STUDENTS_ACCOUNTS.TXT ĐÃ SẠCH!")
        print(f"🚀 CÓ THỂ CHẠY TOOL VỚI {len(remaining_lines)} TÀI KHOẢN MỚI!")
        
    except Exception as e:
        print(f"❌ Lỗi tổng quát: {e}")

if __name__ == "__main__":
    clean_students_file()
    input("\nNhấn Enter để thoát...")
