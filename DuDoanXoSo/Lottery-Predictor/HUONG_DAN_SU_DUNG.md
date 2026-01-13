# 📖 HƯỚNG DẪN SỬ DỤNG LOTTERY-PREDICTOR

## 📋 MỤC LỤC
1. [Cài Đặt](#cài-đặt)
2. [Cách Chạy Chương Trình](#cách-chạy-chương-trình)
3. [Giao Diện Chính](#giao-diện-chính)
4. [Dữ Liệu Cần Thiết](#dữ-liệu-cần-thiết)
5. [Các Tính Năng Chính](#các-tính-năng-chính)
6. [Viết Thuật Toán Mới](#viết-thuật-toán-mới)
7. [Tối Ưu Hóa Thuật Toán](#tối-ưu-hóa-thuật-toán)
8. [Xử Lý Lỗi Thường Gặp](#xử-lý-lỗi-thường-gặp)

---

## 🔧 CÀI ĐẶT

### Yêu Cầu Hệ Thống
- **Python 3.8+** (khuyến nghị 3.10 trở lên)
- **Windows / macOS / Linux**

### Bước 1: Cài Đặt Python
Nếu chưa có Python, tải từ: https://www.python.org/downloads/

### Bước 2: Cài Đặt Các Thư Viện Cần Thiết

Mở Command Prompt (Windows) hoặc Terminal (Mac/Linux) tại thư mục chương trình, chạy:

```bash
pip install PyQt5 requests astor psutil google-generativeai packaging
```

**Giải thích các thư viện:**
- **PyQt5**: Tạo giao diện người dùng (GUI)
- **requests**: Tải dữ liệu từ internet
- **astor**: Hỗ trợ xử lý code Python
- **psutil**: Theo dõi tài nguyên hệ thống
- **google-generativeai**: Tạo thuật toán bằng AI (Gemini)
- **packaging**: Quản lý phiên bản

---

## ▶️ CÁCH CHẠY CHƯƠNG TRÌNH

### Cách 1: Chạy Trực Tiếp (Đơn Giản Nhất)

1. Mở Command Prompt (Windows) hoặc Terminal (Mac/Linux)
2. Điều hướng đến thư mục chương trình:
   ```bash
   cd đường_dẫn_đến_Lottery-Predictor
   ```
3. Chạy lệnh:
   ```bash
   python main.py
   ```

### Cách 2: Tạo File Batch (Windows)

Tạo file `run.bat` trong thư mục chương trình với nội dung:
```batch
@echo off
python main.py
pause
```

Sau đó, double-click vào file `run.bat` để chạy.

### Cách 3: Tạo Shortcut (Windows)

1. Chuột phải trên Desktop → New → Shortcut
2. Nhập: `python.exe "đường_dẫn_đến_main.py"`
3. Đặt tên và click Finish

---

## 🖥️ GIAO DIỆN CHÍNH

Chương trình có các tab chính:

### 1. **Tab Main (Trang Chính)**
- **Chọn Ngày**: Chọn ngày muốn dự đoán
- **Chọn Thuật Toán**: Lựa chọn các thuật toán để sử dụng
- **Kết Quả Dự Đoán**: Hiển thị top 3-5-10 số có điểm cao nhất
- **So Sánh**: Nếu có kết quả ngày hôm sau, sẽ so sánh độ chính xác

### 2. **Tab Hiệu Suất (Performance)**
- Kiểm tra độ chính xác của thuật toán trong khoảng thời gian
- Xem tỷ lệ trúng top 3, top 5, top 10
- Phân tích hiệu suất từng thuật toán

### 3. **Tab Tối Ưu (Optimize)**
- Tối ưu hóa tham số của thuật toán
- Chọn khoảng thời gian để test
- Lưu kết quả tối ưu thành công

### 4. **Tab Công Cụ (Tools)**
- **Viết Thuật Toán**: Sử dụng AI Gemini để tạo thuật toán mới
- **Tải Lại Thuật Toán**: Reload các thuật toán từ thư mục
- **Xem Log**: Xem nhật ký hoạt động

### 5. **Tab Cài Đặt (Settings)**
- Cấu hình API Key cho Gemini
- Cấu hình URL tải dữ liệu
- Cấu hình URL cập nhật chương trình

---

## 📊 DỮ LIỆU CẦN THIẾT

### File Dữ Liệu Chính: `data/xsmb-2-digits.json`

**Vị trí**: `DuDoanXoSo/Lottery-Predictor/data/xsmb-2-digits.json`

**Format dữ liệu**:
```json
[
  {
    "date": "2005-10-01T00:00:00.000",
    "special": 84,
    "prize1": 76,
    "prize2_1": 85,
    "prize2_2": 37,
    "prize3_1": 42,
    "prize3_2": 64,
    ...
    "prize7_4": 70
  },
  ...
]
```

**Giải thích các trường:**
- **date**: Ngày quay thưởng (ISO format)
- **special**: Giải đặc biệt (2 chữ số cuối)
- **prize1**: Giải nhất
- **prize2_1, prize2_2**: Giải nhì (2 số)
- **prize3_1 đến prize3_6**: Giải ba (6 số)
- **prize4_1 đến prize4_4**: Giải tư (4 số)
- **prize5_1 đến prize5_6**: Giải năm (6 số)
- **prize6_1 đến prize6_3**: Giải sáu (3 số)
- **prize7_1 đến prize7_4**: Giải bảy (4 số)

### Cách Cập Nhật Dữ Liệu

**Cách 1: Tải Tự Động**
- Trong tab Settings, nhập URL tải dữ liệu
- Mặc định: `https://raw.githubusercontent.com/junlangzi/Lottery-Predictor/refs/heads/main/data/xsmb-2-digits.json`
- Click "Sync Data" để tải

**Cách 2: Cập Nhật Thủ Công**
- Chỉnh sửa file `data/xsmb-2-digits.json` trực tiếp
- Thêm dòng mới với format JSON đúng
- Lưu file

**Cách 3: Sử Dụng Script**
- Chạy script trong thư mục `tools/` để tải dữ liệu từ nguồn

---

## 🎯 CÁC TÍNH NĂNG CHÍNH

### 1. Dự Đoán Xổ Số

**Quy Trình:**
1. Chọn ngày muốn dự đoán ở tab Main
2. Chọn 1 hoặc nhiều thuật toán
3. Click "Predict" hoặc "Dự Đoán"
4. Xem kết quả top 3, top 5, top 10

**Cách Hoạt Động:**
- Chương trình lấy dữ liệu lịch sử từ file JSON
- Áp dụng các thuật toán được chọn
- Tính điểm cho mỗi số từ 00-99
- Sắp xếp theo điểm cao nhất
- Hiển thị top N số

### 2. Kiểm Tra Hiệu Suất

**Quy Trình:**
1. Vào tab "Hiệu Suất" (Performance)
2. Chọn khoảng thời gian (từ ngày - đến ngày)
3. Chọn thuật toán
4. Chọn top N (3, 5, hoặc 10)
5. Click "Kiểm Tra"

**Kết Quả:**
- Tỷ lệ trúng (%)
- Số lần trúng / tổng số ngày
- Biểu đồ hiệu suất

### 3. Tối Ưu Hóa Thuật Toán

**Quy Trình:**
1. Vào tab "Tối Ưu" (Optimize)
2. Chọn thuật toán muốn tối ưu
3. Chọn khoảng thời gian
4. Chọn top N (3, 5, hoặc 10)
5. Cấu hình các tham số:
   - **Bước nhảy** (Step): Khoảng cách giữa các giá trị test
   - **Min/Max**: Giá trị tối thiểu/tối đa
6. Click "Bắt Đầu Tối Ưu"

**Kết Quả:**
- Các tham số tối ưu được lưu vào thư mục `optimize/`
- Có thể sử dụng lại các tham số này

---

## 🤖 VIẾT THUẬT TOÁN MỚI

### Cách 1: Sử Dụng AI Gemini (Dễ Nhất)

**Bước 1: Lấy API Key Gemini**
1. Truy cập: https://aistudio.google.com/
2. Đăng nhập bằng tài khoản Google
3. Click "Get API key" → "Create API key in new project"
4. Sao chép API key

**Bước 2: Nhập API Key**
1. Vào tab "Công Cụ" → "Viết Thuật Toán"
2. Dán API key vào ô "Gemini API Key"
3. Click "Hiện" để xem API key (tùy chọn)

**Bước 3: Mô Tả Thuật Toán**
1. Nhập tên file (ví dụ: `my_algorithm`)
2. Tên lớp sẽ tự động sinh (ví dụ: `MyAlgorithmAlgorithm`)
3. Nhập mô tả ngắn gọn
4. Mô tả chi tiết logic thuật toán:
   ```
   - Tính tần suất xuất hiện của mỗi số trong 90 ngày qua
   - Cộng điểm cho số có tần suất cao
   - Giảm điểm cho số đã về trong 2 ngày liên tiếp
   - Ưu tiên số không xuất hiện trong 10 ngày gần nhất
   ```

**Bước 4: Tạo Code**
1. Click "Tạo Thuật Toán"
2. Chờ AI tạo code (1-2 phút)
3. Xem code được tạo ở phần "Nội dung thuật toán"

**Bước 5: Lưu Thuật Toán**
1. Click "Lưu" để lưu vào thư mục `algorithms/`
2. Hoặc click "Sao chép" để copy code

### Cách 2: Viết Thủ Công

**Bước 1: Tạo File**
1. Tạo file Python mới trong thư mục `algorithms/`
2. Ví dụ: `my_custom_algorithm.py`

**Bước 2: Viết Code**

Cấu trúc cơ bản:
```python
# -*- coding: utf-8 -*-
import datetime
from algorithms.base import BaseAlgorithm

class MyCustomAlgorithmAlgorithm(BaseAlgorithm):
    def __init__(self, data_results_list=None, cache_dir=None):
        super().__init__(data_results_list=data_results_list, cache_dir=cache_dir)
        
        self.config = {
            "description": "Mô tả thuật toán của tôi",
            "parameters": {
                "window_size": 30,
                "threshold": 0.5,
                "bonus_points": 10.0
            }
        }
        self._log('debug', f"{self.__class__.__name__} initialized.")

    def predict(self, date_to_predict: datetime.date, historical_results: list) -> dict:
        scores = {f'{i:02d}': 0.0 for i in range(100)}
        
        if not historical_results:
            return scores
        
        try:
            params = self.config.get('parameters', {})
            window_size = params.get('window_size', 30)
            
            # Logic tính toán của bạn ở đây
            recent_data = historical_results[-window_size:]
            
            # Ví dụ: Tính tần suất
            from collections import Counter
            all_numbers = []
            for result in recent_data:
                numbers = self.extract_numbers_from_dict(result)
                all_numbers.extend(numbers)
            
            frequency = Counter(all_numbers)
            
            # Cập nhật scores
            for num in range(100):
                num_str = f'{num:02d}'
                scores[num_str] = float(frequency.get(num, 0))
            
            self._log('info', f"Prediction completed for {date_to_predict}.")
            return scores
            
        except Exception as e:
            self._log('error', f"Error: {e}")
            return {}

if __name__ == "__main__":
    # Test thuật toán
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    algo = MyCustomAlgorithmAlgorithm()
    print(f"Config: {algo.get_config()}")
```

**Bước 3: Lưu File**
- Lưu file trong thư mục `algorithms/`
- Tên file phải là `.py`

**Bước 4: Reload Thuật Toán**
1. Vào tab "Công Cụ"
2. Click "Tải Lại Thuật Toán"
3. Thuật toán mới sẽ xuất hiện trong danh sách

---

## ⚙️ TỐI ƯU HÓA THUẬT TOÁN

### Quy Trình Tối Ưu

**Bước 1: Chuẩn Bị**
1. Vào tab "Tối Ưu" (Optimize)
2. Chọn thuật toán muốn tối ưu
3. Chọn khoảng thời gian (ví dụ: 01/01/2024 - 31/12/2024)

**Bước 2: Cấu Hình Tham Số**
- Mỗi tham số có:
  - **Min**: Giá trị tối thiểu
  - **Max**: Giá trị tối đa
  - **Step**: Bước nhảy (khoảng cách giữa các giá trị test)

**Bước 3: Chạy Tối Ưu**
1. Click "Bắt Đầu Tối Ưu"
2. Chương trình sẽ test tất cả các kết hợp tham số
3. Hiển thị tiến độ (%)
4. Lưu kết quả tốt nhất

**Bước 4: Xem Kết Quả**
- Kết quả lưu trong: `optimize/tên_thuật_toán/success/`
- Có thể xem chi tiết từng kết quả

### Ví Dụ Tối Ưu

Giả sử tối ưu thuật toán "frequency_analyzer":
- **window_size**: Min=10, Max=60, Step=5
- **threshold**: Min=0.1, Max=0.9, Step=0.1
- **bonus_points**: Min=5, Max=20, Step=1

Chương trình sẽ test:
- window_size: 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60
- threshold: 0.1, 0.2, 0.3, ..., 0.9
- bonus_points: 5, 6, 7, ..., 20

Tổng cộng: 11 × 9 × 16 = 1,584 kết hợp

---

## 🐛 XỬ LÝ LỖI THƯỜNG GẶP

### Lỗi 1: "ModuleNotFoundError: No module named 'PyQt5'"

**Nguyên Nhân**: Chưa cài đặt PyQt5

**Giải Pháp**:
```bash
pip install PyQt5
```

### Lỗi 2: "FileNotFoundError: data/xsmb-2-digits.json"

**Nguyên Nhân**: File dữ liệu không tồn tại

**Giải Pháp**:
1. Kiểm tra file có trong thư mục `data/` không
2. Nếu không, tải từ GitHub:
   ```bash
   python -c "import requests; open('data/xsmb-2-digits.json', 'wb').write(requests.get('https://raw.githubusercontent.com/junlangzi/Lottery-Predictor/refs/heads/main/data/xsmb-2-digits.json').content)"
   ```

### Lỗi 3: "API key not valid" (Khi dùng Gemini)

**Nguyên Nhân**: API key không đúng hoặc hết hạn

**Giải Pháp**:
1. Kiểm tra lại API key từ https://aistudio.google.com/
2. Xóa API key cũ và nhập lại
3. Kiểm tra tài khoản Google có bị khóa không

### Lỗi 4: Chương trình chạy chậm

**Nguyên Nhân**: Dữ liệu quá lớn hoặc tối ưu quá nhiều tham số

**Giải Pháp**:
1. Giảm khoảng thời gian kiểm tra
2. Giảm bước nhảy (step) khi tối ưu
3. Tối ưu ít tham số hơn
4. Đóng các ứng dụng khác

### Lỗi 5: Thuật toán không hiển thị sau khi viết

**Nguyên Nhân**: Lỗi syntax hoặc chưa reload

**Giải Pháp**:
1. Kiểm tra file `.py` có lỗi syntax không
2. Vào tab "Công Cụ" → Click "Tải Lại Thuật Toán"
3. Xem log để tìm lỗi chi tiết

---

## 📝 TIPS & TRICKS

### 1. Tạo Thuật Toán Tốt
- Mô tả chi tiết logic của bạn cho Gemini
- Sử dụng các chỉ số kỹ thuật (EMA, RSI, MACD, v.v.)
- Test thuật toán trên dữ liệu lịch sử trước

### 2. Tối Ưu Hiệu Quả
- Bắt đầu với bước nhảy lớn (step=5-10)
- Sau đó tối ưu lại với bước nhảy nhỏ hơn
- Lưu kết quả tốt nhất để so sánh

### 3. Kết Hợp Nhiều Thuật Toán
- Chọn 2-3 thuật toán khác nhau
- Kết hợp kết quả để tăng độ chính xác
- Ưu tiên số xuất hiện trong top của nhiều thuật toán

### 4. Cập Nhật Dữ Liệu Thường Xuyên
- Tải dữ liệu mới hàng ngày
- Dữ liệu mới giúp dự đoán chính xác hơn

---

## 📞 HỖ TRỢ & LIÊN HỆ

- **GitHub**: https://github.com/junlangzi/Lottery-Predictor
- **Issues**: Báo cáo lỗi tại GitHub Issues
- **Discussions**: Thảo luận tại GitHub Discussions

---

## 📄 GIẤY PHÉP

Dự án này được phát hành dưới giấy phép MIT.

---

**Cập nhật lần cuối**: 13/01/2026
**Phiên bản**: 5.3.1
