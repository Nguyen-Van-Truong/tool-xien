#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os

def install_package(package):
    """Cài đặt một package Python"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Đã cài đặt thành công: {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi cài đặt {package}: {e}")
        return False

def check_chromedriver():
    """Kiểm tra ChromeDriver"""
    paths_to_check = [
        "driver/chromedriver.exe",
        "chromedriver.exe",
        "driver/chromedriver",
        "chromedriver"
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            print(f"✅ Tìm thấy ChromeDriver tại: {path}")
            return True
    
    print("❌ Không tìm thấy ChromeDriver!")
    print("📥 Hướng dẫn tải ChromeDriver:")
    print("extract gg from pdf. Truy cập: https://chromedriver.chromium.org/")
    print("2. Tải phiên bản phù hợp với Chrome của bạn")
    print("3. Giải nén và đặt file chromedriver.exe vào thư mục driver/")
    return False

def main():
    print("🔧 CÀI ĐẶT REQUIREMENTS CHO GOOGLE LOGIN CHECKER")
    print("=" * 60)
    
    # Danh sách packages cần thiết
    required_packages = [
        "selenium",
        "webdriver-manager",
        "requests",
        "beautifulsoup4"
    ]
    
    print("📦 Cài đặt các thư viện Python cần thiết...")
    
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Kết quả cài đặt: {success_count}/{len(required_packages)} thành công")
    
    # Kiểm tra ChromeDriver
    print("\n🚗 Kiểm tra ChromeDriver...")
    check_chromedriver()
    
    # Kiểm tra file tài khoản
    print("\n📁 Kiểm tra file dữ liệu...")
    if os.path.exists("students_accounts.txt"):
        with open("students_accounts.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"✅ Tìm thấy file students_accounts.txt với {len(lines)} tài khoản")
    else:
        print("❌ Không tìm thấy file students_accounts.txt")
        print("💡 Hãy chạy script extract_student_data.py trước!")
    
    print("\n" + "=" * 60)
    print("🎯 HƯỚNG DẪN SỬ DỤNG:")
    print("extract gg from pdf. Đảm bảo tất cả requirements đã cài đặt thành công")
    print("2. Đặt ChromeDriver vào thư mục driver/")
    print("3. Chạy: py google_login_checker.py")
    print("=" * 60)

if __name__ == "__main__":
    main() 