"""
================================================================================
TOOL ĐIỀN THÔNG TIN THẺ SINH VIÊN - TAY ĐO COLLEGE
================================================================================
Giao diện đơn giản để điền thông tin vào thẻ sinh viên
Sử dụng cấu hình từ profiles/thegithut.json

Tính năng:
- Chọn ảnh thẻ gốc
- Nhập thông tin sinh viên (hỗ trợ random)
- Chọn giới tính nam/nữ
- Preview trực tiếp
- Xuất ảnh hoàn chỉnh
- Xuất hàng loạt nhiều ảnh

Tác giả: Generated Code
Ngày: 2025-11-27
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk
import json
import os
import random
from datetime import datetime, timedelta
import sys
import io

# Set UTF-8 encoding cho Windows
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass


class FillCardTayDo:
    """
    Tool điền thông tin thẻ sinh viên Tây Đô College
    Giao diện đơn giản, dễ sử dụng
    """
    
    def __init__(self, root):
        """
        Khởi tạo giao diện
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("📝 Điền Thẻ Sinh Viên - Tây Đô College")
        self.root.geometry("950x700")
        self.root.resizable(True, True)
        
        # Đường dẫn cấu hình
        self.config_file = "profiles/thegithut.json"
        self.settings_file = "profiles/taydo_settings.json"
        
        # Email domain mặc định (có thể thay đổi trong giao diện)
        self.default_email_domain = "@professionalbeautyschool.com"
        self.default_gender = "female"  # Giới tính mặc định
        
        # File ảnh thẻ gốc theo giới tính
        self.template_file_male = "phoinam.png"    # Ảnh thẻ nam
        self.template_file_female = "phoinu.png"   # Ảnh thẻ nữ
        
        # Dữ liệu ảnh
        self.image_path = None
        self.original_image = None
        self.photo_image = None
        self.scale_factor = 1.0
        
        # Vị trí các trường (load từ config)
        self.positions = {}
        self.load_config()
        
        # Dữ liệu sinh viên
        self.student_data = {
            "ho_ten": "",
            "ngay_sinh": "",
            "chuyen_nganh": "",
            "ma_sinh_vien": "",
            "thoi_han_the": ""
        }
        
        # Text entries
        self.entries = {}
        
        # Khởi tạo dữ liệu random
        self.init_random_data()
        
        # Load settings đã lưu
        self.load_settings()
        
        # Tạo giao diện
        self.create_ui()
        
        # Áp dụng settings đã load vào UI
        self.apply_settings_to_ui()
        
        # Thông báo
        print("[Start] Tool điền thẻ sinh viên Tây Đô College đã khởi động!")
    
    def load_config(self):
        """
        Load cấu hình vị trí từ file JSON
        File: profiles/thegithut.json
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.positions = json.load(f)
                print(f"[Config] Đã load cấu hình từ {self.config_file}")
            else:
                # Cấu hình mặc định nếu không tìm thấy file (khớp với thegithut.json)
                self.positions = {
                    "ho_ten": {"x_ratio": 0.521484375, "y_ratio": 0.4632867132867133, "font_size": 24, "bold": True, "enabled": True},
                    "ngay_sinh": {"x_ratio": 0.5224609375, "y_ratio": 0.5297202797202797, "font_size": 26, "bold": True, "enabled": True},
                    "chuyen_nganh": {"x_ratio": 0.564453125, "y_ratio": 0.5996503496503497, "font_size": 23, "bold": True, "enabled": True},
                    "ma_sinh_vien": {"x_ratio": 0.5537109375, "y_ratio": 0.6678321678321678, "font_size": 24, "bold": True, "enabled": True},
                    "thoi_han_the": {"x_ratio": 0.5537109375, "y_ratio": 0.736013986013986, "font_size": 24, "bold": True, "enabled": True}
                }
                print("[Config] Sử dụng cấu hình mặc định")
        except Exception as e:
            print(f"[Error] Lỗi load config: {e}")
            messagebox.showerror("Lỗi", f"Không thể load cấu hình:\n{e}")
    
    def load_settings(self):
        """
        Load các settings đã lưu (giới tính, email domain, ảnh gốc...)
        File: profiles/taydo_settings.json
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Load giới tính
                self.default_gender = settings.get("gender", "female")
                
                # Load email domain
                self.default_email_domain = settings.get("email_domain", "@professionalbeautyschool.com")
                
                # Load đường dẫn ảnh gốc
                saved_image = settings.get("image_path", None)
                if saved_image and os.path.exists(saved_image):
                    self.image_path = saved_image
                
                print(f"[Settings] Đã load: gender={self.default_gender}, domain={self.default_email_domain}")
            else:
                print("[Settings] Chưa có file settings, sử dụng mặc định")
        except Exception as e:
            print(f"[Settings] Lỗi load: {e}")
    
    def save_settings(self):
        """
        Lưu các settings hiện tại vào file
        Bao gồm: giới tính, email domain, đường dẫn ảnh
        """
        try:
            settings = {
                "gender": self.gender_var.get(),
                "email_domain": self.email_domain_var.get(),
                "image_path": self.image_path
            }
            
            # Đảm bảo thư mục tồn tại
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            print(f"[Settings] Đã lưu: {settings}")
        except Exception as e:
            print(f"[Settings] Lỗi lưu: {e}")
    
    def apply_settings_to_ui(self):
        """
        Áp dụng settings đã load vào các UI components
        Gọi sau khi create_ui()
        """
        # Áp dụng giới tính
        self.gender_var.set(self.default_gender)
        
        # Áp dụng email domain
        self.email_domain_var.set(self.default_email_domain)
        
        # Load ảnh nếu có
        if self.image_path and os.path.exists(self.image_path):
            try:
                self.original_image = Image.open(self.image_path)
                filename = os.path.basename(self.image_path)
                w, h = self.original_image.size
                self.image_label.config(text=f"✅ {filename}\n📐 {w}x{h}px", foreground="green")
                self.update_preview()
                print(f"[Settings] Đã load ảnh: {self.image_path}")
            except Exception as e:
                print(f"[Settings] Lỗi load ảnh: {e}")
    
    def on_gender_changed(self):
        """
        Xử lý khi thay đổi giới tính
        Tự động chọn ảnh thẻ gốc từ thư mục tương ứng và lưu settings
        """
        gender = self.gender_var.get()
        
        # Tự động chọn ảnh thẻ gốc theo giới tính
        if gender in ["male", "female"]:
            self.load_template_by_gender(gender)
        
        self.save_settings()
        gender_text = {"random": "Ngẫu nhiên", "male": "Nam", "female": "Nữ"}.get(gender, gender)
        print(f"[Gender] Đã chọn: {gender_text}")
    
    def get_template_file(self, gender):
        """
        Lấy file ảnh thẻ gốc theo giới tính
        Args:
            gender: 'male' hoặc 'female'
        Returns:
            Đường dẫn file ảnh
        """
        if gender == "male":
            return self.template_file_male
        else:
            return self.template_file_female
    
    def load_template_by_gender(self, gender):
        """
        Load ảnh thẻ gốc theo giới tính
        Args:
            gender: 'male' hoặc 'female'
        Returns:
            True nếu thành công, False nếu thất bại
        """
        template_file = self.get_template_file(gender)
        
        if not os.path.exists(template_file):
            print(f"[Template] File không tồn tại: {template_file}")
            return False
        
        try:
            self.image_path = template_file
            self.original_image = Image.open(template_file)
            
            # Cập nhật label
            w, h = self.original_image.size
            gender_text = "Nam" if gender == "male" else "Nữ"
            self.image_label.config(
                text=f"✅ {template_file}\n📐 {w}x{h}px\n👤 {gender_text}", 
                foreground="green"
            )
            
            self.update_preview()
            print(f"[Template] Đã chọn ảnh {gender_text}: {template_file}")
            return True
        except Exception as e:
            print(f"[Template] Lỗi load ảnh: {e}")
            return False
    
    def on_email_domain_changed(self):
        """
        Xử lý khi thay đổi email domain
        Cập nhật email và lưu settings
        """
        self.update_email()
        self.save_settings()
    
    def init_random_data(self):
        """
        Khởi tạo dữ liệu cho việc random thông tin
        Bao gồm họ, tên đệm, tên nam/nữ, chuyên ngành
        Danh sách mở rộng để random đa dạng hơn
        """
        # Danh sách họ phổ biến (50 họ)
        self.ho = [
            "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
            "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đinh", "Trương", "Lương", "Cao",
            "Lưu", "Tạ", "Hà", "Tô", "Trịnh", "Mai", "Đoàn", "Lâm", "Tăng", "Châu",
            "Quách", "Thái", "Từ", "Kiều", "Mạc", "Tống", "Triệu", "Vương", "La", "Đào",
            "Phùng", "Hứa", "Chu", "Thạch", "Liêu", "Giang", "Quang", "Thiều", "Diệp", "Khưu"
        ]
        
        # Tên đệm nam (30 tên đệm)
        self.ten_dem_nam = [
            "Văn", "Đức", "Minh", "Hữu", "Thành", "Quang", "Hoàng", "Anh",
            "Công", "Đình", "Xuân", "Quốc", "Bảo", "Gia", "Hùng", "Ngọc",
            "Tấn", "Trung", "Thanh", "Phúc", "Đăng", "Tuấn", "Huy", "Duy",
            "Nhật", "Thiên", "Khánh", "Vinh", "Chí", "Tiến"
        ]
        
        # Tên đệm nữ (30 tên đệm)
        self.ten_dem_nu = [
            "Thị", "Ngọc", "Thanh", "Kim", "Hoàng", "Phương", "Thu", "Bích",
            "Minh", "Thùy", "Quỳnh", "Khánh", "Diệu", "Tuyết", "Mỹ", "Ánh",
            "Thúy", "Như", "Hồng", "Xuân", "Mai", "Lan", "Yến", "Hà",
            "Trúc", "Bảo", "Huệ", "Cẩm", "Nguyệt", "Ái"
        ]
        
        # Tên nam (80 tên)
        self.ten_nam = [
            "Hùng", "Dũng", "Tuấn", "Hải", "Nam", "Minh", "Long", "Sơn", "Hiếu", "Khoa",
            "Đức", "Thắng", "Quân", "Phong", "Bình", "Hoàng", "Kiên", "Trung", "Huy", "Việt",
            "Tùng", "Đạt", "Cường", "Thành", "Nghĩa", "Tân", "Toàn", "Tiến", "Quang", "Trọng",
            "Phú", "Lộc", "Tài", "Phát", "An", "Khang", "Khánh", "Vinh", "Hưng", "Thịnh",
            "Nhân", "Thiện", "Tâm", "Trí", "Dũng", "Mạnh", "Hào", "Vương", "Đông", "Tây",
            "Bắc", "Nam", "Sáng", "Sang", "Quý", "Hiển", "Hậu", "Lâm", "Phước", "Thuận",
            "Hòa", "Bằng", "Linh", "Luân", "Nhật", "Thanh", "Triều", "Vỹ", "Khôi", "Kiệt",
            "Phước", "Thịnh", "Lợi", "Danh", "Đại", "Chương", "Diễn", "Giàu", "Hiệp", "Hùng"
        ]
        
        # Tên nữ (80 tên)
        self.ten_nu = [
            "Linh", "Anh", "Hương", "Mai", "Lan", "Ngọc", "Thảo", "Hà", "Trang", "Yến",
            "Hằng", "Phương", "Vy", "Trinh", "Nhung", "Chi", "Nhi", "Như", "Oanh", "Hạnh",
            "Thúy", "Quyên", "Giang", "Vân", "Hoa", "Dung", "Tâm", "Loan", "Hiền", "Uyên",
            "Trâm", "Thy", "Thư", "Tiên", "Ngân", "Châu", "Trúc", "Diễm", "Huệ", "Kiều",
            "Lệ", "Mỹ", "Nga", "Nhàn", "Nhiên", "Nương", "Phụng", "Quynh", "Sen", "Thanh",
            "Thắm", "Thơ", "Thu", "Thủy", "Tuyền", "Tuyết", "Vui", "Xoan", "Xuân", "Yến",
            "Ánh", "Bích", "Cẩm", "Cúc", "Dao", "Đào", "Điệp", "Đông", "Duyên", "Gấm",
            "Hồng", "Huyền", "Khanh", "Lam", "Liễu", "Ly", "Mai", "Nguyệt", "Nhạn", "Quế"
        ]
        
        # Danh sách chuyên ngành phổ biến
        self.chuyen_nganh_list = [
            "Ngôn ngữ Anh", "Kế toán", "Marketing", "Thiết kế đồ họa", "Cơ khí",
            "Xây dựng", "Du lịch", "Luật", "Y tá", "Dược", "Nông nghiệp",
            "Kinh tế", "Sư phạm", "Báo chí", "Điều dưỡng", "Quản lý đất đai", "Thú y"
        ]
    
    def create_ui(self):
        """Tạo giao diện chính"""
        # Main container với 2 cột
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === CỘT TRÁI: Form nhập liệu ===
        left_frame = ttk.LabelFrame(main_frame, text="📋 Thông tin sinh viên", width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Chọn ảnh
        img_frame = ttk.LabelFrame(left_frame, text="🖼️ Ảnh thẻ gốc")
        img_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(img_frame, text="📂 Chọn ảnh...", command=self.open_image).pack(fill=tk.X, padx=5, pady=5)
        
        self.image_label = ttk.Label(img_frame, text="Chưa chọn ảnh", foreground="gray")
        self.image_label.pack(padx=5, pady=(0, 5))
        
        # Cấu hình Email Domain
        email_config_frame = ttk.LabelFrame(left_frame, text="📧 Cấu hình Email")
        email_config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        domain_frame = ttk.Frame(email_config_frame)
        domain_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(domain_frame, text="Domain:", width=8).pack(side=tk.LEFT)
        self.email_domain_var = tk.StringVar(value=self.default_email_domain)
        self.email_domain_entry = ttk.Entry(domain_frame, textvariable=self.email_domain_var, font=("Arial", 10))
        self.email_domain_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.email_domain_entry.bind("<KeyRelease>", lambda e: self.on_email_domain_changed())
        
        # Giới tính
        gender_frame = ttk.LabelFrame(left_frame, text="👤 Giới tính (cho Random)")
        gender_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.gender_var = tk.StringVar(value=self.default_gender)
        
        for text, value in [("🎲 Ngẫu nhiên", "random"), ("👨 Nam", "male"), ("👩 Nữ", "female")]:
            ttk.Radiobutton(
                gender_frame, 
                text=text, 
                variable=self.gender_var, 
                value=value,
                command=self.on_gender_changed
            ).pack(side=tk.LEFT, padx=8, pady=5)
        
        # Form nhập thông tin
        form_frame = ttk.LabelFrame(left_frame, text="✏️ Điền thông tin")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Các trường thông tin
        fields = [
            ("Họ và tên:", "ho_ten"),
            ("Ngày sinh:", "ngay_sinh"),
            ("Chuyên ngành:", "chuyen_nganh"),
            ("Mã sinh viên:", "ma_sinh_vien"),
            ("Thời hạn thẻ:", "thoi_han_the")
        ]
        
        for label_text, field_name in fields:
            frame = ttk.Frame(form_frame)
            frame.pack(fill=tk.X, padx=5, pady=3)
            
            ttk.Label(frame, text=label_text, width=14, anchor=tk.W).pack(side=tk.LEFT)
            
            entry = ttk.Entry(frame, font=("Arial", 10))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
            
            # Bind event - mã sinh viên thay đổi thì cập nhật email
            if field_name == "ma_sinh_vien":
                entry.bind("<KeyRelease>", lambda e: self.on_ma_sv_changed())
            else:
                entry.bind("<KeyRelease>", lambda e: self.update_preview())
            
            self.entries[field_name] = entry
        
        # Trường Email (tự động tạo từ mã SV + domain)
        email_frame = ttk.Frame(form_frame)
        email_frame.pack(fill=tk.X, padx=5, pady=3)
        
        ttk.Label(email_frame, text="📧 Email:", width=14, anchor=tk.W).pack(side=tk.LEFT)
        
        self.email_entry = ttk.Entry(email_frame, font=("Arial", 10))
        self.email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.entries["email"] = self.email_entry
        
        # Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="🎲 Random", command=self.random_info).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="🗑️ Xóa tất cả", command=self.clear_all).pack(fill=tk.X, pady=2)
        
        ttk.Separator(btn_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="👁️ Preview", command=self.update_preview).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="💾 Xuất ảnh", command=self.export_image).pack(fill=tk.X, pady=2)
        
        ttk.Separator(btn_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Xuất hàng loạt
        batch_frame = ttk.LabelFrame(btn_frame, text="📦 Xuất hàng loạt")
        batch_frame.pack(fill=tk.X, pady=5)
        
        count_frame = ttk.Frame(batch_frame)
        count_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(count_frame, text="Số lượng:").pack(side=tk.LEFT)
        self.batch_count = ttk.Spinbox(count_frame, from_=1, to=100, width=8)
        self.batch_count.set(10)
        self.batch_count.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(batch_frame, text="🚀 Xuất nhiều ảnh", command=self.export_batch).pack(fill=tk.X, padx=5, pady=5)
        
        # === CỘT PHẢI: Preview ===
        right_frame = ttk.LabelFrame(main_frame, text="🖼️ Preview")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas để hiển thị ảnh
        self.canvas = tk.Canvas(right_frame, bg="#f0f0f0")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Hiển thị hướng dẫn ban đầu
        self.show_welcome_message()
    
    def show_welcome_message(self):
        """Hiển thị thông báo chào mừng trên canvas"""
        self.canvas.delete("all")
        self.canvas.create_text(
            300, 200,
            text="👋 Chào mừng!\n\n1. Chọn ảnh thẻ gốc\n2. Nhập thông tin hoặc Random\n3. Xuất ảnh",
            font=("Arial", 14),
            fill="gray",
            justify=tk.CENTER
        )
    
    def open_image(self):
        """Mở ảnh thẻ gốc"""
        file = filedialog.askopenfilename(
            title="Chọn ảnh thẻ sinh viên",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if file:
            try:
                self.image_path = file
                self.original_image = Image.open(file)
                
                # Cập nhật label
                filename = os.path.basename(file)
                w, h = self.original_image.size
                self.image_label.config(text=f"✅ {filename}\n📐 {w}x{h}px", foreground="green")
                
                self.update_preview()
                
                # Lưu settings với ảnh mới
                self.save_settings()
                
                print(f"[Image] Đã mở: {file}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở ảnh:\n{e}")
    
    def get_font(self, size, bold=False):
        """
        Lấy font để vẽ text
        Args:
            size: Kích thước font
            bold: Có in đậm không
        Returns:
            ImageFont object
        """
        if bold:
            paths = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/timesbd.ttf", 
                    "C:/Windows/Fonts/arial.ttf"]
        else:
            paths = ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/times.ttf"]
        
        for path in paths:
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
        return ImageFont.load_default()
    
    def update_preview(self):
        """Cập nhật preview ảnh"""
        if not self.original_image:
            return
        
        # Tạo bản copy để vẽ
        preview = self.original_image.copy()
        draw = ImageDraw.Draw(preview)
        width, height = preview.size
        
        # Lấy dữ liệu từ entries
        data = {}
        for field, entry in self.entries.items():
            data[field] = entry.get()
        
        # Vẽ từng trường
        for field_name, pos in self.positions.items():
            # Bỏ qua trường bị tắt
            if not pos.get("enabled", True):
                continue
            
            # Bỏ qua nếu không có trong form
            if field_name not in data:
                continue
            
            text = data.get(field_name, "")
            if not text:
                continue
            
            x = int(width * pos["x_ratio"])
            y = int(height * pos["y_ratio"])
            font_size = pos.get("font_size", 24)
            is_bold = pos.get("bold", False)
            
            font = self.get_font(font_size, is_bold)
            draw.text((x, y), text, font=font, fill=(0, 0, 0))
        
        # Scale để hiển thị
        canvas_width = self.canvas.winfo_width() or 550
        canvas_height = self.canvas.winfo_height() or 400
        
        # Tính scale factor để fit canvas
        scale_w = canvas_width / width
        scale_h = canvas_height / height
        self.scale_factor = min(scale_w, scale_h, 1.0)  # Không phóng to quá kích thước gốc
        
        display_w = int(width * self.scale_factor)
        display_h = int(height * self.scale_factor)
        
        display_image = preview.resize((display_w, display_h), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(display_image)
        
        # Hiển thị trên canvas
        self.canvas.delete("all")
        self.canvas.create_image(
            canvas_width // 2, canvas_height // 2,
            anchor=tk.CENTER,
            image=self.photo_image
        )
    
    def update_email(self):
        """
        Cập nhật email dựa trên mã sinh viên và domain
        Email = mã_sinh_viên + domain
        """
        ma_sv = self.entries["ma_sinh_vien"].get().strip()
        domain = self.email_domain_var.get().strip()
        
        # Tạo email
        if ma_sv:
            email = f"{ma_sv}{domain}"
        else:
            email = ""
        
        # Cập nhật entry email
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, email)
    
    def on_ma_sv_changed(self):
        """
        Xử lý khi mã sinh viên thay đổi
        Cập nhật email và preview
        """
        self.update_email()
        self.update_preview()
    
    def random_info(self):
        """Random thông tin sinh viên và tự động chọn ảnh thẻ theo giới tính"""
        # Lấy giới tính
        gender = self.gender_var.get()
        if gender == "random":
            gender = random.choice(["male", "female"])
        
        # Tự động chọn ảnh thẻ gốc theo giới tính
        self.load_template_by_gender(gender)
        
        ho = random.choice(self.ho)
        
        if gender == "male":
            ten_dem = random.choice(self.ten_dem_nam)
            ten = random.choice(self.ten_nam)
        else:
            ten_dem = random.choice(self.ten_dem_nu)
            ten = random.choice(self.ten_nu)
        
        # Họ và tên: Họ + Tên đệm + Tên (luôn đầy đủ)
        ho_ten = f"{ho} {ten_dem} {ten}".upper()
        
        # Ngày sinh (18-25 tuổi)
        today = datetime.now()
        start = today - timedelta(days=25*365)
        end = today - timedelta(days=18*365)
        days = random.randrange((end - start).days)
        ngay_sinh = (start + timedelta(days=days)).strftime("%d/%m/%Y")
        
        # Chuyên ngành
        chuyen_nganh = random.choice(self.chuyen_nganh_list)
        
        # Mã sinh viên (format: 24XXXXXX)
        year = random.randint(20, 25)
        id_num = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        ma_sinh_vien = f"{year}{id_num}"
        
        # Email (mã sinh viên + domain)
        domain = self.email_domain_var.get().strip()
        email = f"{ma_sinh_vien}{domain}"
        
        # Thời hạn thẻ (chỉ lấy năm 2024 hoặc 2025)
        start_year = random.choice([2024, 2025])
        end_year = start_year + 4
        start_month = random.choice([8, 9, 10])
        thoi_han_the = f"{start_month:02d}/{start_year} - {start_month:02d}/{end_year}"
        
        # Cập nhật entries
        self.entries["ho_ten"].delete(0, tk.END)
        self.entries["ho_ten"].insert(0, ho_ten)
        
        self.entries["ngay_sinh"].delete(0, tk.END)
        self.entries["ngay_sinh"].insert(0, ngay_sinh)
        
        self.entries["chuyen_nganh"].delete(0, tk.END)
        self.entries["chuyen_nganh"].insert(0, chuyen_nganh)
        
        self.entries["ma_sinh_vien"].delete(0, tk.END)
        self.entries["ma_sinh_vien"].insert(0, ma_sinh_vien)
        
        self.entries["thoi_han_the"].delete(0, tk.END)
        self.entries["thoi_han_the"].insert(0, thoi_han_the)
        
        # Cập nhật email
        self.entries["email"].delete(0, tk.END)
        self.entries["email"].insert(0, email)
        
        self.update_preview()
        print(f"[Random] {ho_ten} - {ma_sinh_vien} - {email}")
    
    def clear_all(self):
        """Xóa tất cả thông tin"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.update_preview()
    
    def create_final_image(self):
        """
        Tạo ảnh hoàn chỉnh (không có markers)
        Returns:
            PIL Image object hoặc None nếu lỗi
        """
        if not self.original_image:
            return None
        
        img = self.original_image.copy()
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Lấy dữ liệu
        data = {}
        for field, entry in self.entries.items():
            data[field] = entry.get()
        
        # Vẽ từng trường
        for field_name, pos in self.positions.items():
            if not pos.get("enabled", True):
                continue
            
            if field_name not in data:
                continue
            
            text = data.get(field_name, "")
            if not text:
                continue
            
            x = int(width * pos["x_ratio"])
            y = int(height * pos["y_ratio"])
            font_size = pos.get("font_size", 24)
            is_bold = pos.get("bold", False)
            
            font = self.get_font(font_size, is_bold)
            draw.text((x, y), text, font=font, fill=(0, 0, 0))
        
        return img
    
    def export_image(self):
        """Xuất ảnh đã điền thông tin"""
        if not self.original_image:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ảnh trước!")
            return
        
        ma_sv = self.entries["ma_sinh_vien"].get() or "card"
        
        file = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")],
            initialfile=f"card_{ma_sv}.jpg"
        )
        
        if file:
            try:
                img = self.create_final_image()
                if img:
                    img.save(file, quality=95)
                    messagebox.showinfo("Thành công", f"Đã lưu:\n{file}")
                    print(f"[Export] {file}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu:\n{e}")
    
    def export_batch(self):
        """Xuất hàng loạt nhiều ảnh với ảnh thẻ gốc tự động theo giới tính"""
        gender = self.gender_var.get()
        
        # Kiểm tra file ảnh tồn tại
        if gender == "random":
            # Kiểm tra cả 2 file
            if not os.path.exists(self.template_file_male) and not os.path.exists(self.template_file_female):
                messagebox.showwarning("Cảnh báo", f"Không tìm thấy file ảnh!\n\nVui lòng có file:\n- {self.template_file_male}\n- {self.template_file_female}")
                return
        elif gender == "male":
            if not os.path.exists(self.template_file_male):
                messagebox.showwarning("Cảnh báo", f"Không tìm thấy file:\n{self.template_file_male}")
                return
        else:
            if not os.path.exists(self.template_file_female):
                messagebox.showwarning("Cảnh báo", f"Không tìm thấy file:\n{self.template_file_female}")
                return
        
        # Chọn thư mục lưu
        folder = filedialog.askdirectory(title="Chọn thư mục lưu ảnh")
        if not folder:
            return
        
        try:
            count = int(self.batch_count.get())
        except:
            count = 10
        
        # Xác nhận
        if not messagebox.askyesno("Xác nhận", f"Sẽ tạo {count} ảnh thẻ sinh viên ngẫu nhiên.\n\nTiếp tục?"):
            return
        
        # Tạo progress window
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Đang xuất...")
        progress_win.geometry("300x100")
        progress_win.transient(self.root)
        
        ttk.Label(progress_win, text="Đang tạo ảnh...").pack(pady=10)
        progress = ttk.Progressbar(progress_win, length=250, mode='determinate')
        progress.pack(pady=10)
        progress_label = ttk.Label(progress_win, text="0 / 0")
        progress_label.pack()
        
        success_count = 0
        
        for i in range(count):
            # Random thông tin mới
            self.random_info()
            
            # Tạo ảnh
            img = self.create_final_image()
            if img:
                ma_sv = self.entries["ma_sinh_vien"].get()
                filename = os.path.join(folder, f"card_{ma_sv}.jpg")
                img.save(filename, quality=95)
                success_count += 1
                print(f"[Batch] {i+1}/{count}: {filename}")
            
            # Cập nhật progress
            progress['value'] = (i + 1) / count * 100
            progress_label.config(text=f"{i+1} / {count}")
            progress_win.update()
        
        progress_win.destroy()
        
        messagebox.showinfo("Hoàn thành", f"Đã tạo {success_count}/{count} ảnh!\n\nThư mục: {folder}")
        
        # Mở thư mục
        if sys.platform == 'win32':
            os.startfile(folder)


def main():
    """Hàm chính khởi chạy ứng dụng"""
    root = tk.Tk()
    app = FillCardTayDo(root)
    root.mainloop()


if __name__ == "__main__":
    main()

