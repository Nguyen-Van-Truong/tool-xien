# Military Verification Auto-Fill Extension

Chrome extension để tự động điền form xác minh quân nhân SheerID và tìm kiếm thông tin veteran từ VA.gov.

## Tính năng

✅ **Auto-fill form SheerID** - Tự động điền các trường:
- Status (Military Veteran/Active Duty/etc)
- Branch of Service (Army, Navy, Air Force, etc)
- First Name, Last Name
- Date of Birth
- Discharge Date  
- Email Address

✅ **Tìm kiếm VLM** - Tìm kiếm và lưu thông tin veteran từ vlm.cem.va.gov

✅ **Quản lý Data** - Lưu trữ danh sách veteran với Import/Export JSON

## Cài đặt

1. Mở Chrome → `chrome://extensions/`
2. Bật **Developer mode** (góc phải trên)
3. Click **Load unpacked**
4. Chọn thư mục `military-verify-extension`

## Sử dụng

### Fill Form
1. Mở trang SheerID verification
2. Click icon extension
3. Nhập thông tin veteran
4. Click **🚀 Fill Form**

### Tìm Veteran
1. Tab **Search VA**
2. Nhập tên veteran
3. Click **🔍 Search VLM**

### Import Data
1. Tab **Data**
2. Click **📥 Import JSON**
3. Chọn file JSON với format:

```json
[
  {
    "firstName": "DENNIS",
    "lastName": "BAILEY",
    "branch": "Navy",
    "birthMonth": "June",
    "birthDay": "4",
    "birthYear": "1947",
    "dischargeMonth": "March",
    "dischargeDay": "16",
    "dischargeYear": "2025",
    "email": "example@email.com"
  }
]
```

## Hotkey

Trên trang SheerID sẽ có nút **🎖️ Auto Fill** ở góc phải dưới để fill nhanh.
