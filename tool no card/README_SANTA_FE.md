# 🎓 SANTA FE COLLEGE - AUTO REGISTRATION TOOL

Công cụ đăng ký tự động cho Santa Fe College với email verification hoàn chỉnh.

## 📋 TÍNH NĂNG

✅ **Đăng ký hoàn chỉnh**: Từ điền form đến email verification  
✅ **Email tạm**: Tích hợp imail.edu.vn với domain @naka.edu.pl  
✅ **Auto navigation**: Điều hướng qua 3 bước selection tự động  
✅ **Smart form filling**: Điền form thông minh với dữ liệu US  
✅ **Email verification**: Xử lý verification code (manual + auto)  
✅ **Multi-mode**: Fast mode (Gmail) và Complete mode (imail)  

## 🚀 CÁCH SỬ DỤNG

### 1. Quick Start
```bash
python run_santa_fe_registration.py
```

### 2. Chạy riêng lẻ

#### Fast Registration (Gmail)
```bash
python sf_auto_registration_fast.py
```

#### Complete Registration (imail)
```bash
python sf_auto_registration_final.py
```

#### Test imail Explorer
```bash
python test_imail_explore.py
```

#### Tạo dữ liệu test
```bash
python generate_us_data.py
```

## 📁 CẤU TRÚC FILES

```
📂 tool no card/
├── 🎯 Main Scripts
│   ├── sf_auto_registration_fast.py      # Fast mode với Gmail
│   ├── sf_auto_registration_final.py     # Complete mode với imail
│   └── run_santa_fe_registration.py      # Quick run script
│
├── 🌐 Email Tools
│   ├── imail_client.py                   # imail client v1
│   ├── imail_client_v2.py                # imail client v2 (improved)
│   └── test_imail_explore.py             # imail explorer
│
├── 📊 Data & Config
│   ├── generate_us_data.py               # US data generator
│   ├── sf_registration_data.json         # Generated data
│   └── sf_registration_data.txt          # Human readable data
│
├── 📸 Screenshots
│   ├── final_reg_step*.png               # Registration steps
│   ├── imail_step*.png                   # imail exploration
│   └── complete_reg_*.png                # Complete flow
│
└── 📄 Results
    ├── sf_final_registrations.json       # Final results
    ├── sf_registered_accounts.txt        # Account info
    └── README_SANTA_FE.md               # This file
```

## 🔧 QUY TRÌNH HOẠT ĐỘNG

### 1. Chuẩn bị dữ liệu
- Tạo người Mỹ với SSN, địa chỉ Florida
- Sinh ngày tháng năm hợp lệ
- Email, điện thoại thật

### 2. Tạo email tạm
- **Fast mode**: Dùng Gmail có sẵn
- **Complete mode**: Tạo email @naka.edu.pl từ imail.edu.vn

### 3. Điều hướng Santa Fe
```
🌐 Homepage → 🎯 Start Application
    ↓
👥 First Time Student → ▶️ Next
    ↓  
🎓 No High School Diploma → ▶️ Next
    ↓
📝 Registration Form
```

### 4. Điền form
- **First Name**: Từ data generated
- **Last Name**: Từ data generated  
- **Email**: Email tạm từ imail
- **Confirm Email**: Same as above
- **SSN**: Valid US SSN format
- **Birth Date**: MM/DD/YYYY
- **Birth Country**: United States

### 5. Email Verification
- Submit form → Verification page
- Check email từ imail.edu.vn
- Nhập mã 6 số → Complete!

## 📧 EMAIL VERIFICATION

### Auto Mode (đang phát triển)
- Tự động check inbox imail
- Extract verification code
- Nhập và submit

### Manual Mode (hiện tại)
```
1. 🌐 Truy cập: https://imail.edu.vn  
2. 🔍 Tìm email từ Santa Fe College
3. 📝 Copy mã verification 6 số
4. 🔐 Nhập vào trang Santa Fe
5. ✅ Complete registration!
```

## 🎯 SCENARIOS SỬ DỤNG

### Scenario 1: Test nhanh
```bash
python sf_auto_registration_fast.py
```
- Dùng Gmail có sẵn
- Manual verification
- Nhanh và đơn giản

### Scenario 2: Production hoàn chỉnh  
```bash
python sf_auto_registration_final.py
```
- Tạo email tạm thật
- Xử lý verification
- Save complete info

### Scenario 3: Khám phá imail
```bash
python test_imail_explore.py
```
- Test tạo email @naka.edu.pl
- Khám phá interface
- Debug email creation

## 📊 KẾT QUẢ OUTPUTS

### Registration Results
```
📄 sf_final_registrations.txt - Thông tin đăng ký
📊 sf_final_registrations.json - Data structured  
📸 final_reg_step*.png - Screenshots từng bước
```

### Email Info
```
📧 Email: firstname99@naka.edu.pl
👤 Person: Generated US person
🆔 SSN: Valid format XXX-XX-XXXX
🎯 Status: Success/Pending/Manual Required
```

## 🚨 LƯU Ý QUAN TRỌNG

⚠️ **Email Verification**: Hiện tại cần manual input mã  
⚠️ **imail Stability**: Service có thể thay đổi giao diện  
⚠️ **Santa Fe Changes**: Website có thể update selectors  
⚠️ **Rate Limiting**: Không spam quá nhiều requests  

## 🔧 TROUBLESHOOTING

### Lỗi không tìm thấy elements
```bash
# Update selectors trong FLOW_SELECTORS
# Check screenshots để debug
```

### imail không hoạt động
```bash
# Fallback sang email format manual
# Hoặc dùng fast mode với Gmail
```

### Verification timeout
```bash
# Check spam folder
# Thử resend code
# Manual input
```

## 📞 SUPPORT

- Check screenshots trong thư mục
- Xem logs console output  
- Debug với browser mở (comment driver.quit())

## 🎉 SUCCESS EXAMPLE

```
🎯 SANTA FE COLLEGE - FINAL AUTO REGISTRATION
============================================================
👤 Đăng ký: John Smith
📧 Email: john84@naka.edu.pl
✅ Form submitted successfully
🔐 Verification code: 123456
🏆 ĐĂNG KÝ HOÀN THÀNH!
```

---

**🚀 Sẵn sàng đăng ký Santa Fe College tự động!** 