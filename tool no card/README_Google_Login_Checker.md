# 🔍 GOOGLE LOGIN CHECKER

Tool kiểm tra đăng nhập Google với danh sách tài khoản sinh viên được trích xuất từ file PDF.

## 📋 Tính năng

✅ **Kiểm tra tự động** đăng nhập Google với danh sách tài khoản  
✅ **Phân loại kết quả** thành công/thất bại/bị khóa  
✅ **Lưu kết quả** vào các file riêng biệt  
✅ **Ghi log chi tiết** quá trình kiểm tra  
✅ **Chế độ headless** (ẩn trình duyệt)  
✅ **Kiểm tra từng phần** hoặc tiếp tục từ vị trí cụ thể  
✅ **Chống detection** với user agent ngẫu nhiên  

## 📁 Files trong bộ công cụ

| File | Mô tả |
|------|-------|
| `google_login_checker.py` | Tool chính để kiểm tra hàng loạt tài khoản |
| `quick_test_google.py` | Test nhanh vài tài khoản đầu tiên |
| `install_requirements.py` | Cài đặt thư viện cần thiết |
| `students_accounts.txt` | File chứa danh sách tài khoản (được tạo từ PDF) |

## 🚀 Hướng dẫn sử dụng

### Bước 1: Cài đặt thư viện
```bash
py install_requirements.py
```

### Bước 2: Đảm bảo có ChromeDriver
- Tải ChromeDriver từ: https://chromedriver.chromium.org/
- Đặt file `chromedriver.exe` vào thư mục `driver/`

### Bước 3: Kiểm tra file dữ liệu
Đảm bảo file `students_accounts.txt` tồn tại với format:
```
20123456@st.hcmuaf.edu.vn|15061995
20234567@st.hcmuaf.edu.vn|20121996
```

### Bước 4: Chạy tool

#### Option A: Test nhanh (khuyến nghị)
```bash
py quick_test_google.py
```
- Kiểm tra 5-10 tài khoản đầu tiên
- Xem kết quả nhanh chóng

#### Option B: Kiểm tra hàng loạt
```bash
py google_login_checker.py
```
Menu options:
1. **Kiểm tra tất cả** - Chạy toàn bộ 4049 tài khoản
2. **Giới hạn số lượng** - Chỉ kiểm tra N tài khoản đầu
3. **Tiếp tục từ vị trí** - Bắt đầu từ tài khoản thứ X
4. **Chế độ ẩn** - Không hiển thị trình duyệt
5. **Xem thống kê** - Kiểm tra file dữ liệu

## 📊 Kết quả output

Tool sẽ tạo ra các file:

| File | Nội dung |
|------|----------|
| `successful_google_accounts.txt` | Tài khoản đăng nhập thành công |
| `failed_google_accounts.txt` | Tài khoản thất bại (với lý do) |
| `blocked_google_accounts.txt` | Tài khoản bị khóa/đình chỉ |
| `google_login_log.txt` | Log chi tiết quá trình kiểm tra |

## 🎯 Kết quả có thể có

| Kết quả | Ý nghĩa |
|---------|---------|
| `success` | ✅ Đăng nhập thành công |
| `wrong_password` | ❌ Sai mật khẩu |
| `invalid_email` | ❌ Email không tồn tại |
| `blocked` | ⚠️ Tài khoản bị khóa |
| `need_verification` | ⚠️ Cần xác minh phone/recovery |
| `captcha` | ⚠️ Gặp captcha |
| `timeout` | ⏰ Timeout |
| `error` | ❌ Lỗi kỹ thuật |

## ⚙️ Cấu hình nâng cao

### Thời gian nghỉ giữa các lần kiểm tra
- Random 5-15 giây (tránh spam)
- Có thể điều chỉnh trong code

### User Agent
- Tự động random user agent
- Giảm khả năng bị phát hiện

### Extensions
- Tự động load captcha solver nếu có
- Hỗ trợ extension khác trong thư mục `driver/`

## 🔒 Lưu ý bảo mật

⚠️ **Quan trọng:**
- Tool này chỉ dành cho mục đích kiểm tra tài khoản hợp pháp
- Không sử dụng để tấn công hoặc vi phạm điều khoản Google
- Giữ bí mật thông tin tài khoản đăng nhập thành công

## 🐛 Xử lý lỗi thường gặp

### Lỗi ChromeDriver
```bash
❌ Lỗi khởi tạo driver: 'chromedriver' executable needs to be in PATH
```
**Giải pháp:** Đảm bảo `chromedriver.exe` trong thư mục `driver/`

### Lỗi không tìm thấy file
```bash
❌ Lỗi đọc file students_accounts.txt
```
**Giải pháp:** Chạy `extract_student_data.py` trước để tạo file

### Timeout thường xuyên
**Giải pháp:** 
- Kiểm tra kết nối internet
- Tăng timeout trong code
- Sử dụng chế độ không headless

## 📈 Thống kê ước tính

Với 4049 tài khoản sinh viên:
- **Thời gian ước tính:** ~8-12 giờ (với delay 5-15s)
- **Tỷ lệ thành công dự kiến:** 5-15% (200-600 tài khoản)
- **Lý do thất bại chính:** Sai mật khẩu, cần xác minh

## 🎯 Tips sử dụng hiệu quả

1. **Bắt đầu với test nhanh** - Chạy `quick_test_google.py` trước
2. **Chia nhỏ batch** - Chạy từng 100-200 tài khoản một lần
3. **Backup kết quả** - Tool tự động save sau mỗi 10 tài khoản
4. **Chạy ban đêm** - Ít bị phát hiện hơn
5. **Sử dụng VPN** - Đổi IP nếu cần thiết

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra file log: `google_login_log.txt`
2. Chạy lại `install_requirements.py`
3. Đảm bảo Chrome và ChromeDriver tương thích
4. Kiểm tra quyền truy cập file/thư mục

---

✨ **Tool được tối ưu hóa cho việc kiểm tra tài khoản sinh viên từ dữ liệu PDF!** 