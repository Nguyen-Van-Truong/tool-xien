# 🎖️ Military Verification Module - Hướng Dẫn Tiếng Việt

Đây là module xác thực quân nhân (Military/Veteran) cho ChatGPT thông qua SheerID.

## 📋 Tổng Quan

Module này bao gồm:
- **VLM Scraper**: Tự động thu thập thông tin cựu chiến binh từ VA.gov
- **Military Verifier**: Xác thực tự động qua SheerID API
- **Bulk Verifier**: Xác thực hàng loạt nhiều tài khoản

## 🔧 Cấu Trúc File

```
military/
├── __init__.py           # Module exports
├── config.py             # Cấu hình SheerID & VLM
├── vlm_scraper.py        # Công cụ thu thập data veteran
├── sheerid_verifier.py   # Xác thực Military SheerID
└── README_VI.md          # File này
```

## 📥 Nguồn Dữ Liệu Veteran

### VLM (Veterans Legacy Memorial)
- **URL**: https://www.vlm.cem.va.gov
- **Loại**: Thông tin cựu chiến binh đã mất (public)
- **Data thu được**:
  - Họ tên (First Name, Last Name)
  - Quân chủng (Branch)
  - Ngày mất → Ước tính ngày sinh & ngày xuất ngũ

## 🚀 Cách Sử Dụng

### 1. Lệnh Telegram Bot

#### `/verify6 <link>` - Xác thực Military (cho tất cả users)
```
/verify6 https://services.sheerid.com/verify/xxx/?verificationId=abc123
```
Bot sẽ tự động:
1. Tải dữ liệu veteran từ VLM
2. Điền vào form SheerID
3. Trả về kết quả

#### `/scrape_veterans [tên] [năm] [số lượng]` - Thu thập data (Admin)
```
/scrape_veterans b 2025 50
```
- `b`: Họ bắt đầu bằng chữ "b"
- `2025`: Năm mất
- `50`: Số lượng tối đa

#### `/bulk_verify6 <link1> <link2> ...` - Xác thực hàng loạt (Admin)
```
/bulk_verify6 https://...?verificationId=aaa https://...?verificationId=bbb
```
Xác thực nhiều link cùng lúc (tối đa 10).

### 2. Script Dòng Lệnh

```bash
# Thu thập veteran data
cd tgbot-verify
python scrape_veterans.py -n smith -y 2025 -c 100

# Xuất ra file JSON
python scrape_veterans.py -o veterans.json

# Xuất ra file TXT (pipe format)
python scrape_veterans.py -o veterans.txt --txt

# Thu thập hàng loạt
python scrape_veterans.py --bulk -c 200
```

### 3. Sử Dụng Trong Code Python

```python
from military import MilitaryVerifier, scrape_veterans_sync

# Thu thập veteran data
veterans = scrape_veterans_sync(
    last_name="b",
    death_year=2025,
    max_results=50
)

# Xác thực
verification_id = "abc123def456"
verifier = MilitaryVerifier(verification_id)
result = verifier.verify_with_veteran_data(veterans[0])

if result['success']:
    print("Xác thực thành công!")
    print(f"Redirect: {result.get('redirect_url')}")
```

## 📊 Format Dữ Liệu

### Pipe-delimited format (TXT)
```
FirstName|LastName|Branch|BirthMonth|BirthDay|BirthYear|DischargeMonth|DischargeDay|DischargeYear|Email
JOHN|SMITH|Navy|June|15|1945|March|20|2025|johnsmith123@gmail.com
```

### JSON format
```json
{
  "firstName": "JOHN",
  "lastName": "SMITH",
  "branch": "Navy",
  "birthMonth": "June",
  "birthDay": "15",
  "birthYear": "1945",
  "dischargeMonth": "March",
  "dischargeDay": "20",
  "dischargeYear": "2025",
  "email": "johnsmith123@gmail.com",
  "status": "VETERAN"
}
```

## 🎖️ Quân Chủng (Branch)

| ID | Tên tiếng Anh | Tên tiếng Việt |
|----|---------------|----------------|
| 4070 | Army | Lục quân |
| 4073 | Air Force | Không quân |
| 4072 | Navy | Hải quân |
| 4071 | Marine Corps | Thủy quân lục chiến |
| 4074 | Coast Guard | Tuần duyên |
| 4544268 | Space Force | Lực lượng Vũ trụ |

## 🔄 Quy Trình API

### Bước 1: collectMilitaryStatus
```
POST /rest/v2/verification/{verificationId}/step/collectMilitaryStatus
Body: {"status": "VETERAN"}
```

### Bước 2: collectInactiveMilitaryPersonalInfo
```
POST /rest/v2/verification/{verificationId}/step/collectInactiveMilitaryPersonalInfo
Body: {
  "firstName": "...",
  "lastName": "...",
  "birthDate": "YYYY-MM-DD",
  "email": "...",
  "organization": {"id": 4070, "name": "Army"},
  "dischargeDate": "YYYY-MM-DD",
  ...
}
```

## ⚠️ Lưu Ý

1. **Cập nhật PROGRAM_ID**: Kiểm tra và cập nhật `config.py` nếu cần
2. **Rate Limiting**: Tránh gửi quá nhiều request cùng lúc
3. **VLM Accessibility**: VLM có thể chặn nếu quét quá nhiều
4. **Dữ liệu thật**: Chỉ dùng thông tin cựu chiến binh đã mất (public info)

## 📝 Changelog

### v1.0.0 (2025-12-25)
- ✅ Tạo module Military Verification
- ✅ VLM Scraper với Playwright
- ✅ Tích hợp commands `/verify6`, `/scrape_veterans`, `/bulk_verify6`
- ✅ Script CLI `scrape_veterans.py`
