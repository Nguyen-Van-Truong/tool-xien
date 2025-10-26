#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 CHECK TEST PROGRESS
Monitor test verification progress
"""

import os
import time
from datetime import datetime

def check_screenshots():
    """Check screenshots được tạo"""
    screenshots = [
        "auto_verify_step1_homepage.png",
        "auto_verify_step2_after_start.png", 
        "auto_verify_step3_after_option1.png",
        "auto_verify_step4_registration_form.png",
        "auto_verify_step5_form_filled.png",
        "auto_verify_step6_after_submit.png",
        "auto_verify_step7_verification_page.png",
        "auto_verify_step8_after_verification.png",
        "auto_verify_final_result.png"
    ]
    
    print("🔍 CHECKING TEST PROGRESS")
    print("=" * 40)
    
    for i, screenshot in enumerate(screenshots, 1):
        if os.path.exists(screenshot):
            stat = os.stat(screenshot)
            size = stat.st_size / 1024  # KB
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M:%S")
            print(f"✅ Step {i}: {screenshot} ({size:.1f}KB at {mod_time})")
        else:
            print(f"⏳ Step {i}: {screenshot} - Chưa có")
            break
    
    # Check result files
    result_files = [
        "auto_verify_test_result.json",
        "auto_verify_test_result.txt"
    ]
    
    print("\n📄 RESULT FILES:")
    for file in result_files:
        if os.path.exists(file):
            stat = os.stat(file)
            size = stat.st_size
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M:%S")
            print(f"✅ {file} ({size}B at {mod_time})")
        else:
            print(f"⏳ {file} - Chưa có")

def check_browsers():
    """Check có browser nào đang chạy"""
    try:
        import subprocess
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq chrome.exe'], 
                              capture_output=True, text=True)
        
        lines = result.stdout.strip().split('\n')
        chrome_processes = [line for line in lines if 'chrome.exe' in line]
        
        print(f"\n🌐 CHROME PROCESSES: {len(chrome_processes)}")
        if chrome_processes:
            print("✅ Test đang chạy (có browser)")
        else:
            print("⚠️ Không có Chrome browser")
            
    except:
        print("⚠️ Không check được browser")

if __name__ == "__main__":
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        check_screenshots()
        check_browsers()
        
        print(f"\n🔄 Refresh sau 10s... (Ctrl+C để thoát)")
        
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print(f"\n👋 Thoát monitor!")
            break 