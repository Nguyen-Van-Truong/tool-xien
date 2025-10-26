#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 CREATE NEW ACCOUNT AND FAST REGISTER
Tạo người mới và đăng ký nhanh
"""

import subprocess
import sys
import time

def create_and_register():
    """Tạo người mới và đăng ký nhanh"""
    print("🎯 CREATE NEW ACCOUNT & FAST REGISTER")
    print("=" * 50)
    print("🚀 Quy trình: Tạo người mới → Đăng ký nhanh")
    print("-" * 50)
    
    try:
        # Bước extract gg from pdf: Tạo người mới
        print("\n👤 BƯỚC extract gg from pdf: Tạo người mới...")
        result = subprocess.run([
            sys.executable, "generate_us_data.py"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Đã tạo người mới thành công!")
            print(result.stdout)
        else:
            print("❌ Lỗi tạo người mới:")
            print(result.stderr)
            return
        
        # Chờ một chút
        time.sleep(2)
        
        # Bước 2: Đăng ký nhanh
        print("\n🚀 BƯỚC 2: Bắt đầu đăng ký nhanh...")
        print("⚡ Sử dụng chế độ FAST - ít chờ đợi")
        print("-" * 30)
        
        # Chạy registration
        subprocess.run([
            sys.executable, "sf_auto_registration_fast.py"
        ], cwd=".")
        
    except Exception as e:
        print(f"💥 Lỗi: {e}")

if __name__ == "__main__":
    create_and_register() 