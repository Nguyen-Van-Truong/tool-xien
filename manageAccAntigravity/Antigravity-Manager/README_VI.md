# Antigravity Tools 🚀
> Hệ thống Quản lý Tài khoản AI & Proxy Chuyên nghiệp (v3.3.20)

<div align="center">
  <img src="public/icon.png" alt="Antigravity Logo" width="120" height="120" style="border-radius: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">

  <h3>Cổng Điều phối AI Hiệu suất Cao Cá nhân của Bạn</h3>
  <p>Proxy Gemini & Claude mượt mà. Tương thích OpenAI. Bảo mật trước hết.</p>
  
  <p>
    <a href="https://github.com/lbjlaq/Antigravity-Manager">
      <img src="https://img.shields.io/badge/Version-3.3.20-blue?style=flat-square" alt="Version">
    </a>
    <img src="https://img.shields.io/badge/Tauri-v2-orange?style=flat-square" alt="Tauri">
    <img src="https://img.shields.io/badge/Backend-Rust-red?style=flat-square" alt="Rust">
    <img src="https://img.shields.io/badge/Frontend-React-61DAFB?style=flat-square" alt="React">
    <img src="https://img.shields.io/badge/License-CC--BY--NC--SA--4.0-lightgrey?style=flat-square" alt="License">
  </p>

  <p>
    <a href="./README.md">简体中文</a> | 
    <a href="./README_EN.md">English</a> |
    <strong>Tiếng Việt</strong>
  </p>
</div>

---

**Antigravity Tools** là ứng dụng desktop đa năng được thiết kế cho các nhà phát triển và những người đam mê AI. Nó kết hợp hoàn hảo việc quản lý đa tài khoản, chuyển đổi giao thức và điều phối yêu cầu thông minh để cung cấp cho bạn một **Trạm Trung chuyển AI Cục bộ** ổn định, tốc độ cao và chi phí thấp.

Bằng cách sử dụng ứng dụng này, bạn có thể chuyển đổi các Web Session thông thường (Google/Anthropic) thành giao diện API chuẩn, hoàn toàn loại bỏ khoảng cách giao thức giữa các nhà cung cấp khác nhau.

## 🌟 Tính năng Chi tiết

### 1. 🎛️ Bảng điều khiển Tài khoản Thông minh
- **Giám sát Thời gian Thực**: Xem ngay tình trạng của tất cả tài khoản, bao gồm quota trung bình còn lại cho Gemini Pro, Gemini Flash, Claude và Imagen.
- **Gợi ý Thông minh**: Hệ thống tự động lọc và gợi ý "Tài khoản Tốt nhất" dựa trên dung lượng quota, hỗ trợ **chuyển đổi một click**.
- **Snapshot Tài khoản Hoạt động**: Hiển thị trực quan phần trăm quota cụ thể và thời gian đồng bộ cuối cùng.

### 2. 🔐 Quản lý Tài khoản Chuyên nghiệp
- **Xác thực OAuth 2.0 (Tự động/Thủ công)**: Tạo sẵn URL authorization để bạn có thể hoàn tất xác thực trong bất kỳ trình duyệt nào.
- **Import Đa chiều**: Hỗ trợ nhập token đơn lẻ, import JSON hàng loạt, và tự động migrate từ cơ sở dữ liệu V1 cũ.
- **View Gateway**: Hỗ trợ chuyển đổi giữa view "Danh sách" và "Lưới". Phát hiện 403 Forbidden, tự động đánh dấu và bỏ qua tài khoản có vấn đề.

### 3. 🔌 Chuyển đổi Giao thức & Relay (API Proxy)
- **Thích ứng Đa giao thức**:
  - **OpenAI Format**: Cung cấp endpoint `/v1/chat/completions`, tương thích 99% ứng dụng AI hiện có.
  - **Anthropic Format**: Cung cấp interface `/v1/messages` gốc, hỗ trợ **Claude Code CLI** đầy đủ.
  - **Gemini Format**: Hỗ trợ gọi trực tiếp từ Google AI SDK chính thức.
- **Tự phục hồi Thông minh**: Khi gặp lỗi `429` hoặc `401`, backend tự động **retry và xoay vòng im lặng** trong mili giây.

### 4. 🔀 Trung tâm Định tuyến Model
- **Mapping theo Series**: Phân loại model ID phức tạp thành "Nhóm Series" (ví dụ: định tuyến tất cả yêu cầu GPT-4 đến `gemini-3-pro-high`).
- **Redirect Chuyên gia**: Hỗ trợ mapping model bằng regex tùy chỉnh.
- **Routing Phân cấp**: Tự động ưu tiên theo loại tài khoản (Ultra/Pro/Free) và tần suất reset.
- **Downgrade Tác vụ nền**: Tự động nhận diện tác vụ nền (như tạo tiêu đề Claude CLI) và chuyển hướng đến model Flash.

### 5. 🎨 Hỗ trợ Đa phương thức & Imagen 3
- **Kiểm soát Hình ảnh Nâng cao**: Hỗ trợ kiểm soát chính xác qua tham số `size` OpenAI hoặc hậu tố tên model.
- **Payload Lớn**: Backend hỗ trợ payload lên đến **100MB**, đủ cho nhận dạng và xử lý ảnh 4K HD.

---

## 📥 Cài đặt

### Lựa chọn A: Tải về Thủ công (Windows - Khuyến nghị)
Tải từ [GitHub Releases](https://github.com/lbjlaq/Antigravity-Manager/releases):
- **Windows**: File `.msi` hoặc `.zip` portable
- **macOS**: File `.dmg` (Universal, Apple Silicon & Intel)
- **Linux**: File `.deb` hoặc `AppImage`

### Lựa chọn B: Terminal (macOS & Linux)
```bash
# 1. Thêm repository
brew tap lbjlaq/antigravity-manager https://github.com/lbjlaq/Antigravity-Manager

# 2. Cài đặt
brew install --cask antigravity-tools
```

### 🛠️ Xử lý Sự cố

#### macOS báo "Ứng dụng bị hỏng"?
```bash
sudo xattr -rd com.apple.quarantine "/Applications/Antigravity Tools.app"
```

---

## 🔌 Hướng dẫn Sử dụng Nhanh

### Bước 1: Thêm Tài khoản

1. Mở app → vào **Accounts** → **Add Account** → **OAuth**
2. Dialog sẽ tạo sẵn URL authorization → Click để copy vào clipboard
3. Mở URL trong browser và hoàn tất xác thực
4. Browser sẽ hiển thị "✅ Authorized successfully!"
5. App tự động hoàn tất và lưu tài khoản

> **Lưu ý**: URL authorization chứa port callback một lần. Luôn sử dụng URL mới nhất trong dialog.

### Bước 2: Bật API Proxy

1. Vào tab **API Proxy**
2. Bật toggle để khởi động service
3. Mặc định: `http://127.0.0.1:8045`

### Bước 3: Kết nối Client

#### Claude Code CLI
```bash
export ANTHROPIC_API_KEY="sk-antigravity"
export ANTHROPIC_BASE_URL="http://127.0.0.1:8045"
claude
```

#### Python (OpenAI SDK)
```python
import openai

client = openai.OpenAI(
    api_key="sk-antigravity",
    base_url="http://127.0.0.1:8045/v1"
)

response = client.chat.completions.create(
    model="gemini-3-flash",
    messages=[{"role": "user", "content": "Xin chào, hãy giới thiệu về bạn"}]
)
print(response.choices[0].message.content)
```

#### Kilo Code
1. **Protocol**: Ưu tiên sử dụng **Gemini Protocol**
2. **Base URL**: `http://127.0.0.1:8045`
3. **Lưu ý**: 
   - OpenAI mode có thể gây lỗi 404 do path không chuẩn
   - Nếu không kết nối được, kiểm tra **Model Mapping** trong settings

#### Các Client khác (Cherry Studio, Cursor, NextChat...)
- **Base URL**: `http://127.0.0.1:8045/v1`
- **API Key**: `sk-antigravity` (hoặc bất kỳ giá trị nào)
- **Model**: `gemini-3-flash`, `gemini-3-pro`, `claude-sonnet-4`, v.v.

---

## 🏗️ Kiến trúc Hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                     External Apps                           │
│         (Claude Code / Cursor / Cherry Studio)              │
└─────────────────────┬───────────────────────────────────────┘
                      │ OpenAI / Anthropic / Gemini Protocol
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Antigravity Axum Server                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Middleware: Auth / Rate Limit / Logging             │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Model Router: ID Mapping & Regex Routing            │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Account Dispatcher: Rotation / Weights / Failover   │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Request Mapper: Protocol Conversion                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Upstream APIs                                  │
│         (Google AI / Anthropic Claude)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Tính năng Nâng cao

### Model Mapping
Bạn có thể tùy chỉnh mapping model trong tab **Model Router**:

| Request Model | → Actual Model |
|---------------|----------------|
| `gpt-4*` | `gemini-3-pro-high` |
| `gpt-3.5*` | `gemini-3-flash` |
| `claude-*` | `gemini-3-pro` |

### Scheduling Mode
- **Cache First**: Ưu tiên giữ account cho session (tốt cho prompt caching)
- **Balance**: Cân bằng giữa các account
- **Performance First**: Xoay vòng nhanh, tối đa throughput

### LAN Access
Bật "Allow LAN Access" để cho phép các thiết bị khác trong mạng LAN sử dụng proxy.

---

## 📋 Models Hỗ trợ

### Gemini
- `gemini-3-flash` - Nhanh, miễn phí
- `gemini-3-pro` - Cân bằng
- `gemini-3-pro-high` / `gemini-3-pro-low` - Thinking models
- `gemini-3-pro-image` - Tạo ảnh Imagen 3

### Claude (qua proxy)
- `claude-sonnet-4` 
- `claude-opus-4-5`
- `claude-opus-4-5-thinking`

---

## 🔐 Bảo mật

- Tất cả dữ liệu tài khoản được **mã hóa** và lưu trữ **cục bộ** trong SQLite
- Dữ liệu **không bao giờ rời khỏi thiết bị** của bạn trừ khi bật đồng bộ
- Mặc định chỉ lắng nghe trên `127.0.0.1` (localhost only)

---

## 📜 License

**CC BY-NC-SA 4.0** - Chỉ sử dụng phi thương mại.

---

<div align="center">
  <p>Nếu thấy công cụ này hữu ích, hãy ⭐️ trên GitHub!</p>
  <p>Copyright © 2025 Antigravity Team.</p>
</div>
