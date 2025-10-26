#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import zipfile
import subprocess
import sys
from pathlib import Path

def get_chrome_version():
    """Lấy version của Chrome hiện tại"""
    try:
        # Thử lấy version từ registry (Windows)
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
        return version
    except:
        try:
            # Thử lấy từ Chrome executable
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(chrome_path):
                result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True)
                version = result.stdout.strip().split()[-1]
                return version
        except:
            pass
    
    return None

def get_chromedriver_download_url(chrome_version):
    """Lấy URL download ChromeDriver phù hợp"""
    try:
        # Lấy major version (ví dụ: 137 từ 137.0.7151.120)
        major_version = chrome_version.split('.')[0]
        
        # API mới của ChromeDriver
        api_url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        
        response = requests.get(api_url, timeout=10)
        data = response.json()
        
        # Tìm version ChromeDriver phù hợp
        for version_info in reversed(data['versions']):  # Từ mới nhất về cũ
            if version_info['version'].startswith(major_version + '.'):
                downloads = version_info.get('downloads', {})
                chromedriver_downloads = downloads.get('chromedriver', [])
                
                # Tìm download cho Windows
                for download in chromedriver_downloads:
                    if download['platform'] == 'win64':
                        return download['url'], version_info['version']
        
        return None, None
        
    except Exception as e:
        print(f"❌ Lỗi lấy ChromeDriver URL: {e}")
        return None, None

def download_chromedriver(url, version):
    """Download ChromeDriver"""
    try:
        print(f"📥 Đang tải ChromeDriver version {version}...")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        zip_filename = f"chromedriver-win64-{version}.zip"
        
        with open(zip_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Đã tải xong: {zip_filename}")
        return zip_filename
        
    except Exception as e:
        print(f"❌ Lỗi tải ChromeDriver: {e}")
        return None

def extract_chromedriver(zip_filename):
    """Giải nén ChromeDriver"""
    try:
        print(f"📦 Đang giải nén {zip_filename}...")
        
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            # Tạo thư mục driver nếu chưa có
            os.makedirs('driver', exist_ok=True)
            
            # Giải nén tất cả
            zip_ref.extractall('temp_chromedriver')
        
        # Tìm file chromedriver.exe trong thư mục đã giải nén
        for root, dirs, files in os.walk('temp_chromedriver'):
            for file in files:
                if file == 'chromedriver.exe':
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join('driver', 'chromedriver.exe')
                    
                    # Copy file
                    import shutil
                    shutil.copy2(src_path, dst_path)
                    print(f"✅ Đã copy ChromeDriver vào: {dst_path}")
                    
                    # Xóa thư mục tạm
                    shutil.rmtree('temp_chromedriver')
                    os.remove(zip_filename)
                    
                    return True
        
        print("❌ Không tìm thấy chromedriver.exe trong file zip")
        return False
        
    except Exception as e:
        print(f"❌ Lỗi giải nén: {e}")
        return False

def install_selenium():
    """Cài đặt Selenium nếu chưa có"""
    try:
        import selenium
        print("✅ Selenium đã được cài đặt")
        return True
    except ImportError:
        print("📦 Đang cài đặt Selenium...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
            print("✅ Đã cài đặt Selenium thành công")
            return True
        except Exception as e:
            print(f"❌ Lỗi cài đặt Selenium: {e}")
            return False

def test_chromedriver():
    """Test ChromeDriver hoạt động"""
    try:
        print("🧪 Đang test ChromeDriver...")
        
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        chrome_service = Service('driver/chromedriver.exe')
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print(f"✅ ChromeDriver hoạt động tốt! (Đã truy cập Google: {title})")
        return True
        
    except Exception as e:
        print(f"❌ ChromeDriver không hoạt động: {e}")
        return False

def main():
    print("🔧 AUTO CHROMEDRIVER SETUP")
    print("="*50)
    
    # Bước extract gg from pdf: Cài đặt Selenium
    if not install_selenium():
        return
    
    # Bước 2: Lấy Chrome version
    print("\n🔍 Đang kiểm tra Chrome version...")
    chrome_version = get_chrome_version()
    
    if not chrome_version:
        print("❌ Không thể xác định Chrome version!")
        print("💡 Hãy đảm bảo Chrome đã được cài đặt")
        return
    
    print(f"✅ Chrome version: {chrome_version}")
    
    # Bước 3: Lấy ChromeDriver URL
    print("\n🔍 Đang tìm ChromeDriver phù hợp...")
    download_url, driver_version = get_chromedriver_download_url(chrome_version)
    
    if not download_url:
        print("❌ Không tìm thấy ChromeDriver phù hợp!")
        return
    
    print(f"✅ Tìm thấy ChromeDriver version: {driver_version}")
    print(f"🔗 URL: {download_url}")
    
    # Bước 4: Download ChromeDriver
    print("\n📥 Đang tải ChromeDriver...")
    zip_filename = download_chromedriver(download_url, driver_version)
    
    if not zip_filename:
        return
    
    # Bước 5: Giải nén ChromeDriver
    print("\n📦 Đang giải nén ChromeDriver...")
    if not extract_chromedriver(zip_filename):
        return
    
    # Bước 6: Test ChromeDriver
    print("\n🧪 Đang test ChromeDriver...")
    if test_chromedriver():
        print("\n🎉 SETUP THÀNH CÔNG!")
        print("✅ ChromeDriver đã sẵn sàng sử dụng")
        print("💡 Bây giờ bạn có thể chạy các script Google Login")
    else:
        print("\n❌ Setup không thành công!")
        print("💡 Hãy thử chạy lại script này")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng setup!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}") 