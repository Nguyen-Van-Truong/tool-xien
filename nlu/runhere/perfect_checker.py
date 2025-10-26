#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class PerfectChecker:
    def __init__(self):
        self.good_accounts = []
        self.processed_count = 0
        self.wrong_password_count = 0
        self.error_count = 0
        self.lock = threading.Lock()
        self.start_time = datetime.now()
        
    def log(self, message, level="INFO", thread_id=None):
        """Log thread-safe"""
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            icons = {"INFO": "[INFO]", "SUCCESS": "[OK]", "ERROR": "[ERR]", "WARNING": "[WARN]", "STEP": "[STEP]"}
            icon = icons.get(level, "[LOG]")
            thread_str = f"T{thread_id}" if thread_id else ""
            print(f"[{timestamp}] {thread_str} {icon} {message}")
    
    def update_counts(self, result):
        """Cập nhật số liệu thread-safe"""
        with self.lock:
            self.processed_count += 1
            
            if result["status"] == "success":
                self.good_accounts.append(result)
            elif result["status"] == "wrong_password":
                self.wrong_password_count += 1
            else:
                self.error_count += 1

def test_single_account_fresh_chrome(account_data):
    """Test một tài khoản với Chrome hoàn toàn mới - MỖI TÀI KHOẢN MỘT CHROME"""
    username, password, index, thread_id, main_checker = account_data
    
    result = {
        "username": username,
        "password": password,
        "index": index,
        "thread_id": thread_id,
        "status": "unknown"
    }
    
    # Tạo Chrome hoàn toàn mới cho tài khoản này
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--incognito')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-save-password-bubble')
        chrome_options.add_argument('--disable-password-generation')
        chrome_options.add_argument('--disable-autofill')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Tối ưu tốc độ
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        
        # Port riêng cho thread
        debug_port = 9222 + thread_id
        chrome_options.add_argument(f'--remote-debugging-port={debug_port}')
        
        # Sử dụng Selenium Manager tự động tải ChromeDriver phù hợp
        # Không cần chỉ định path, Selenium sẽ tự động xử lý
        driver = webdriver.Chrome(options=chrome_options)
        
        # Bước 1: Mở Google login
        driver.get("https://accounts.google.com/signin")
        time.sleep(0.5)
        
        # Bước 2: Nhập email
        try:
            email_field = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_field.clear()
            email_field.send_keys(username)
            
            next_btn = driver.find_element(By.ID, "identifierNext")
            next_btn.click()
            time.sleep(0.5)
            
        except Exception as e:
            result["status"] = "email_error"
            return result
        
        # Bước 3: Nhập password
        try:
            password_field = None
            
            try:
                password_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )
            except:
                try:
                    password_fields = driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')
                    if password_fields:
                        password_field = password_fields[0]
                except:
                    pass
            
            if not password_field:
                result["status"] = "password_field_not_found"
                return result
            
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(0.5)
            
            password_next = driver.find_element(By.ID, "passwordNext")
            password_next.click()
            time.sleep(3)  # Đợi kết quả
            
        except Exception as e:
            result["status"] = "password_error"
            return result
        
        # Bước 4: Kiểm tra kết quả chính xác
        time.sleep(1.5)  # Đợi thêm để chắc chắn
        
        current_url = driver.current_url
        page_source = driver.page_source.lower()
        
        # Kiểm tra thành công trước
        if any(success_url in current_url for success_url in ["myaccount.google.com", "oauth", "ManageAccount"]):
            result["status"] = "success"
            main_checker.log(f"[OK] TK{index}: {username[:25]}... -> THANH CONG", "SUCCESS", thread_id)
            return result
        
        # Kiểm tra sai password
        error_keywords = ["wrong password", "incorrect password", "try again", "forgot password", "couldn't sign you in"]
        
        for keyword in error_keywords:
            if keyword in page_source:
                result["status"] = "wrong_password"
                main_checker.log(f"[ERR] TK{index}: {username[:25]}... -> SAI PASSWORD", "ERROR", thread_id)
                return result
        
        # Vẫn ở trang login = có thể là tài khoản mới → LƯU LẠI
        if "signin" in current_url and "challenge" in current_url:
            result["status"] = "success"  # THAY ĐỔI: Lưu lại thay vì bỏ
            main_checker.log(f"[WARN] TK{index}: {username[:25]}... -> LUU (van login - co the tai khoan moi)", "WARNING", thread_id)
            return result
        
        # Mặc định thành công
        result["status"] = "success"
        main_checker.log(f"[OK] TK{index}: {username[:25]}... -> THANH CONG (mac dinh)", "SUCCESS", thread_id)
        return result
        
    except Exception as e:
        result["status"] = "error"
        main_checker.log(f"[WARN] TK{index}: {username[:25]}... -> LOI: {str(e)[:30]}", "WARNING", thread_id)
        return result
    
    finally:
        # QUAN TRỌNG: Luôn đóng Chrome hoàn toàn sau mỗi tài khoản
        if driver:
            try:
                driver.quit()
                time.sleep(0.3)
            except:
                pass

def main():
    print("PERFECT CHECKER - MOI TAI KHOAN MOT CHROME MOI")
    print("="*80)
    print("Moi tai khoan = Tao Chrome moi -> Test -> Dong ngay")
    print("Threading thay vi multiprocessing")
    print("Time sleep toi uu: 1.5s")
    print("Co 'Wrong password' ro rang -> KHONG LUU")
    print("Khong co hoac 'van login' -> LUU VAO DANH SACH TOT")
    print("'Van login' co the la tai khoan moi chua kich hoat")
    print("="*80)
    
    # Nhập số threads
    try:
        num_threads = int(input("Nhập số threads (khuyến nghị 4-8): ") or "6")
        num_threads = min(max(num_threads, 1), 12)
    except:
        num_threads = 6
    
    print(f"Su dung {num_threads} threads")
    
    checker = PerfectChecker()
    
    # Load tài khoản
    try:
        with open("students_accounts.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        accounts = []
        for i, line in enumerate(lines):
            line = line.strip()
            if '|' in line:
                username, password = line.split('|', 1)
                accounts.append((username.strip(), password.strip(), i+1))
        
        print(f"Da tai {len(accounts)} tai khoan")
        
    except Exception as e:
        print(f"Loi tai tai khoan: {e}")
        return
    
    print(f"\nBAT DAU {num_threads} THREADS...")
    
    try:
        # Chuẩn bị data cho threads
        account_data = []
        for i, (username, password, index) in enumerate(accounts):
            thread_id = (i % num_threads) + 1
            account_data.append((username, password, index, thread_id, checker))
        
        # Chạy với ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit tất cả jobs
            future_to_account = {
                executor.submit(test_single_account_fresh_chrome, data): data 
                for data in account_data
            }
            
            # Xử lý kết quả
            for future in as_completed(future_to_account):
                try:
                    result = future.result()
                    checker.update_counts(result)
                    
                    # Progress mỗi 10 tài khoản
                    if checker.processed_count % 10 == 0:
                        elapsed = datetime.now() - checker.start_time
                        speed = checker.processed_count / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
                        eta_minutes = (len(accounts) - checker.processed_count) / (speed / 60) if speed > 0 else 0
                        
                        print(f"PROGRESS: {checker.processed_count}/{len(accounts)} | GOOD:{len(checker.good_accounts)} WRONG:{checker.wrong_password_count} ERROR:{checker.error_count} | {speed:.1f} tk/phut | ETA: {eta_minutes:.0f}p")
                    
                    # Backup mỗi 200 tài khoản
                    if checker.processed_count % 200 == 0:
                        timestamp = datetime.now().strftime('%H%M%S')
                        filename = f"perfect_backup_{checker.processed_count}_{timestamp}.txt"
                        
                        with checker.lock:
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(f"# PERFECT BACKUP - {checker.processed_count} TÀI KHOẢN\n")
                                f.write(f"# Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                f.write(f"# Tài khoản tốt: {len(checker.good_accounts)}\n\n")
                                
                                for acc in checker.good_accounts:
                                    f.write(f"{acc['username']}|{acc['password']}\n")
                        
                        print(f"Backup: {filename} ({len(checker.good_accounts)} tai khoan tot)")
                    
                except Exception as e:
                    print(f"Loi xu ly ket qua: {e}")
        
        # Tạo file kết quả cuối cùng
        elapsed = datetime.now() - checker.start_time
        speed = len(accounts) / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
        
        with open("good_accounts.txt", "w", encoding="utf-8") as f:
            f.write("# TÀI KHOẢN HOẠT ĐỘNG TỐT - PERFECT CHECKER\n")
            f.write(f"# Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Tổng thời gian: {elapsed}\n")
            f.write(f"# Threads: {num_threads}\n")
            f.write(f"# Phương pháp: Mỗi tài khoản một Chrome hoàn toàn mới\n")
            f.write(f"# Đã xử lý: {len(accounts)} tài khoản\n")
            f.write(f"# Tìm được: {len(checker.good_accounts)} tài khoản hoạt động tốt\n\n")
            
            for acc in checker.good_accounts:
                f.write(f"{acc['username']}|{acc['password']}\n")
        
        with open("accstatus.txt", "w", encoding="utf-8") as f:
            f.write("# BÁO CÁO PERFECT CHECKER - CHỈ TÀI KHOẢN TỐT\n")
            f.write(f"# Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Threads: {num_threads}\n")
            f.write(f"# Tổng thời gian: {elapsed}\n")
            f.write(f"# Tốc độ: {speed:.1f} tài khoản/phút\n\n")
            
            f.write(f"## THỐNG KÊ:\n")
            f.write(f"- Tài khoản hoạt động tốt: {len(checker.good_accounts)}\n")
            f.write(f"- Sai mật khẩu (không lưu): {checker.wrong_password_count}\n")
            f.write(f"- Lỗi kỹ thuật (không lưu): {checker.error_count}\n")
            f.write(f"- Tổng đã xử lý: {len(accounts)}\n")
            f.write(f"- Tỷ lệ thành công: {len(checker.good_accounts)/len(accounts)*100:.1f}%\n\n")
            
            f.write(f"## {len(checker.good_accounts)} TÀI KHOẢN HOẠT ĐỘNG TỐT:\n")
            for acc in checker.good_accounts:
                f.write(f"{acc['username']}|{acc['password']}\n")
        
        print(f"\n{'='*100}")
        print("PERFECT CHECKER HOAN THANH!")
        print("="*100)
        print(f"KET QUA CUOI CUNG:")
        print(f"   GOOD: Tai khoan hoat dong tot: {len(checker.good_accounts)}/{len(accounts)} ({len(checker.good_accounts)/len(accounts)*100:.1f}%)")
        print(f"   WRONG: Sai mat khau (khong luu): {checker.wrong_password_count}/{len(accounts)} ({checker.wrong_password_count/len(accounts)*100:.1f}%)")
        print(f"   ERROR: Loi ky thuat (khong luu): {checker.error_count}/{len(accounts)} ({checker.error_count/len(accounts)*100:.1f}%)")
        print(f"   TIME: Thoi gian: {elapsed}")
        print(f"   THREADS: {num_threads}")
        print(f"   SPEED: Toc do: {speed:.1f} tai khoan/phut")
        print("="*100)
        print(f"FILE: CHI TAI KHOAN TOT: good_accounts.txt ({len(checker.good_accounts)} tai khoan)")
        
    except KeyboardInterrupt:
        print("Dung boi nguoi dung")
    except Exception as e:
        print(f"Loi: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTam biet!")
    except Exception as e:
        print(f"\nLoi: {e}")
