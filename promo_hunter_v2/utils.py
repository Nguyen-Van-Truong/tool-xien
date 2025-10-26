#!/usr/bin/env python3
"""
Tiện ích chung cho Promo Hunter V2
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any
import config

def setup_logging():
    """Cấu hình logging"""
    logging.basicConfig(
        level=getattr(logging, config.LOGGING_CONFIG['level']),
        format=config.LOGGING_CONFIG['format'],
        datefmt=config.LOGGING_CONFIG['date_format'],
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def save_json(data: Dict[str, Any], filename: str) -> bool:
    """Lưu dữ liệu ra file JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Lỗi lưu file {filename}: {e}")
        return False

def load_json(filename: str) -> Dict[str, Any]:
    """Đọc dữ liệu từ file JSON"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Lỗi đọc file {filename}: {e}")
    return {}

def append_to_file(filename: str, content: str) -> bool:
    """Thêm nội dung vào cuối file"""
    try:
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(content + '\n')
        return True
    except Exception as e:
        logging.error(f"Lỗi ghi file {filename}: {e}")
        return False

def read_codes_from_file(filename: str) -> List[str]:
    """Đọc danh sách codes từ file"""
    codes = []
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    code = line.strip()
                    if code and not code.startswith('#') and len(code) == config.CODE_LENGTH:
                        codes.append(code)
    except Exception as e:
        logging.error(f"Lỗi đọc codes từ {filename}: {e}")
    return codes

def calculate_rate(count: int, elapsed_time: float) -> float:
    """Tính tốc độ thực hiện"""
    return count / elapsed_time if elapsed_time > 0 else 0

def format_time(seconds: float) -> str:
    """Format thời gian thành chuỗi dễ đọc"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def format_number(num: int) -> str:
    """Format số với dấu phẩy"""
    return f"{num:,}"

class Statistics:
    """Class quản lý thống kê"""
    
    def __init__(self):
        self.start_time = time.time()
        self.total_generated = 0
        self.total_checked = 0
        self.valid_found = 0
        self.error_count = 0
        self.strategy_stats = {}
        
    def increment_generated(self, strategy: str = "unknown"):
        """Tăng số lượng đã tạo"""
        self.total_generated += 1
        if strategy not in self.strategy_stats:
            self.strategy_stats[strategy] = {'generated': 0, 'valid': 0}
        self.strategy_stats[strategy]['generated'] += 1
        
    def increment_checked(self):
        """Tăng số lượng đã check"""
        self.total_checked += 1
        
    def increment_valid(self, strategy: str = "unknown"):
        """Tăng số lượng valid"""
        self.valid_found += 1
        if strategy in self.strategy_stats:
            self.strategy_stats[strategy]['valid'] += 1
            
    def increment_error(self):
        """Tăng số lượng lỗi"""
        self.error_count += 1
        
    def get_elapsed_time(self) -> float:
        """Lấy thời gian đã trôi qua"""
        return time.time() - self.start_time
        
    def get_check_rate(self) -> float:
        """Lấy tốc độ check"""
        return calculate_rate(self.total_checked, self.get_elapsed_time())
        
    def get_success_rate(self) -> float:
        """Lấy tỷ lệ thành công"""
        return (self.valid_found / self.total_checked * 100) if self.total_checked > 0 else 0
        
    def get_summary(self) -> Dict[str, Any]:
        """Lấy tổng quan thống kê"""
        elapsed = self.get_elapsed_time()
        return {
            'elapsed_time': elapsed,
            'elapsed_formatted': format_time(elapsed),
            'total_generated': self.total_generated,
            'total_checked': self.total_checked,
            'valid_found': self.valid_found,
            'error_count': self.error_count,
            'check_rate': self.get_check_rate(),
            'success_rate': self.get_success_rate(),
            'strategy_stats': self.strategy_stats,
            'timestamp': datetime.now().isoformat()
        }
        
    def print_summary(self):
        """In tổng quan thống kê"""
        summary = self.get_summary()
        print(f"\n{'='*60}")
        print(f"📊 THỐNG KÊ TỔNG QUAN")
        print(f"{'='*60}")
        print(f"⏱️  Thời gian chạy: {summary['elapsed_formatted']}")
        print(f"🎲 Tổng tạo: {format_number(summary['total_generated'])}")
        print(f"✅ Tổng check: {format_number(summary['total_checked'])}")
        print(f"🎉 Tìm thấy valid: {format_number(summary['valid_found'])}")
        print(f"❌ Lỗi: {format_number(summary['error_count'])}")
        print(f"⚡ Tốc độ check: {summary['check_rate']:.2f} codes/giây")
        print(f"📈 Tỷ lệ thành công: {summary['success_rate']:.4f}%")
        
        if summary['strategy_stats']:
            print(f"\n📋 Chi tiết theo chiến lược:")
            for strategy, stats in summary['strategy_stats'].items():
                success_rate = (stats['valid'] / stats['generated'] * 100) if stats['generated'] > 0 else 0
                print(f"   {strategy}: {stats['generated']} tạo, {stats['valid']} valid ({success_rate:.2f}%)")
        
        print(f"{'='*60}")

def validate_code(code: str) -> bool:
    """Kiểm tra tính hợp lệ của code"""
    if not code or len(code) != config.CODE_LENGTH:
        return False
    return all(c in config.CHARSET for c in code)

def sanitize_filename(filename: str) -> str:
    """Làm sạch tên file"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def ensure_directory(path: str) -> bool:
    """Đảm bảo thư mục tồn tại"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Lỗi tạo thư mục {path}: {e}")
        return False
