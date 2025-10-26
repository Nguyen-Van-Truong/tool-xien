#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SANTA FE COLLEGE - QUICK RUN SCRIPT
Script chạy nhanh để test registration
"""

import subprocess
import sys
import os

def main():
    print("🎯 SANTA FE COLLEGE - QUICK RUN")
    print("=" * 50)
    print("🚀 Chọn script để chạy:")
    print("extract gg from pdf. 📧 Test imail explorer (khám phá imail.edu.vn)")
    print("2. 🎯 Run fast registration (nhanh, dùng Gmail)")
    print("3. 🏆 Run final registration (hoàn chỉnh với imail)")
    print("4. 📊 Generate test data (tạo dữ liệu test)")
    print("5. ❌ Exit")
    print("-" * 50)
    
    try:
        choice = input("Nhập lựa chọn (extract gg from pdf-5): ").strip()
        
        if choice == "extract gg from pdf":
            print("\n🌐 Chạy imail explorer...")
            subprocess.run([sys.executable, "test_imail_explore.py"])
            
        elif choice == "2":
            print("\n⚡ Chạy fast registration...")
            subprocess.run([sys.executable, "sf_auto_registration_fast.py"])
            
        elif choice == "3":
            print("\n🏆 Chạy final registration...")
            subprocess.run([sys.executable, "sf_auto_registration_final.py"])
            
        elif choice == "4":
            print("\n📊 Tạo dữ liệu test...")
            subprocess.run([sys.executable, "generate_us_data.py"])
            
        elif choice == "5":
            print("👋 Bye!")
            return
            
        else:
            print("❌ Lựa chọn không hợp lệ!")
            
    except KeyboardInterrupt:
        print("\n❌ Hủy bởi user")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main() 