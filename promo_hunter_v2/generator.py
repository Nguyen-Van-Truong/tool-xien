#!/usr/bin/env python3
"""
Promo Code Generator V2 - Tạo codes thông minh
"""

import random
import string
from collections import defaultdict, Counter
from typing import List, Dict, Set
import config
import utils
import logging

logger = logging.getLogger(__name__)

class PromoGenerator:
    """Class tạo promo codes thông minh"""
    
    def __init__(self):
        self.known_codes = []
        self.valid_codes = []
        self.char_frequencies = defaultdict(int)
        self.position_frequencies = defaultdict(lambda: defaultdict(int))
        self.bigram_frequencies = defaultdict(int)
        self.trigram_frequencies = defaultdict(int)
        self.generated_codes: Set[str] = set()
        
        # Load codes đã biết
        self._load_known_codes()
        self._analyze_patterns()
        
    def _load_known_codes(self):
        """Load codes đã biết từ file"""
        # Load từ file codes cũ nếu có
        old_codes_files = [
            "../checkpromogpt3m/promocode.txt",
            "../checkpromogpt3m/valid_codes.txt",
            "valid_codes.txt",
            "known_codes.txt"
        ]
        
        for file_path in old_codes_files:
            codes = utils.read_codes_from_file(file_path)
            for code in codes:
                if code not in self.known_codes:
                    self.known_codes.append(code)
                    
        # Tách valid codes (giả sử valid codes ít hơn)
        if len(self.known_codes) >= 2:
            # Giả sử 2 codes đầu là valid (từ kinh nghiệm cũ)
            self.valid_codes = self.known_codes[:2]
            
        logger.info(f"Đã load {len(self.known_codes)} codes đã biết, {len(self.valid_codes)} valid codes")
        
    def _analyze_patterns(self):
        """Phân tích patterns từ codes đã biết"""
        for code in self.known_codes:
            # Phân tích tần suất ký tự
            for char in code:
                self.char_frequencies[char] += 1
                
            # Phân tích tần suất theo vị trí
            for i, char in enumerate(code):
                self.position_frequencies[i][char] += 1
                
            # Phân tích bigrams
            for i in range(len(code) - 1):
                bigram = code[i:i+2]
                self.bigram_frequencies[bigram] += 1
                
            # Phân tích trigrams
            for i in range(len(code) - 2):
                trigram = code[i:i+3]
                self.trigram_frequencies[trigram] += 1
                
        logger.info(f"Phân tích patterns: {len(self.char_frequencies)} chars, {len(self.bigram_frequencies)} bigrams")
        
    def _get_weighted_char_for_position(self, position: int) -> str:
        """Lấy ký tự có trọng số cho vị trí cụ thể"""
        pos_freq = self.position_frequencies[position]
        
        if not pos_freq:
            return random.choice(config.CHARSET)
            
        # 70% theo pattern, 30% random
        if random.random() < 0.7:
            chars = list(pos_freq.keys())
            weights = list(pos_freq.values())
            return random.choices(chars, weights=weights)[0]
        else:
            return random.choice(config.CHARSET)
            
    def generate_pattern_based(self) -> str:
        """Tạo code dựa trên pattern đã học"""
        code = ""
        for i in range(config.CODE_LENGTH):
            code += self._get_weighted_char_for_position(i)
        return code
        
    def generate_prefix_based(self) -> str:
        """Tạo code dựa trên prefix phổ biến"""
        prefix = random.choice(config.COMMON_PREFIXES)
        remaining_length = config.CODE_LENGTH - len(prefix)
        
        if remaining_length <= 0:
            return self.generate_random()
            
        # Thêm suffix hoặc random
        if remaining_length >= 4 and random.random() < 0.5:
            suffix = random.choice(config.COMMON_SUFFIXES)
            if len(prefix) + len(suffix) <= config.CODE_LENGTH:
                middle_length = config.CODE_LENGTH - len(prefix) - len(suffix)
                middle = ''.join(random.choices(config.CHARSET, k=middle_length))
                return prefix + middle + suffix
                
        # Chỉ prefix + random
        suffix = ''.join(random.choices(config.CHARSET, k=remaining_length))
        return prefix + suffix
        
    def generate_year_pattern(self) -> str:
        """Tạo code chứa pattern năm"""
        year_pattern = random.choice(config.YEAR_PATTERNS)
        remaining = config.CODE_LENGTH - len(year_pattern)
        
        # Chèn pattern năm ở vị trí ngẫu nhiên
        insert_pos = random.randint(0, remaining)
        
        prefix = ''.join(random.choices(config.CHARSET, k=insert_pos))
        suffix = ''.join(random.choices(config.CHARSET, k=remaining - insert_pos))
        
        return prefix + year_pattern + suffix
        
    def generate_variation(self) -> str:
        """Tạo biến thể từ valid codes"""
        if not self.valid_codes:
            return self.generate_random()
            
        base_code = random.choice(self.valid_codes)
        
        # Chọn phương pháp biến thể
        method = random.choice(['substitute', 'modify_positions', 'hybrid'])
        
        if method == 'substitute':
            return self._substitute_similar_chars(base_code)
        elif method == 'modify_positions':
            return self._modify_random_positions(base_code)
        else:
            return self._hybrid_variation(base_code)
            
    def _substitute_similar_chars(self, code: str) -> str:
        """Thay thế ký tự tương tự"""
        result = list(code)
        
        for i, char in enumerate(result):
            if char in config.CHAR_SUBSTITUTIONS and random.random() < 0.3:
                substitutes = config.CHAR_SUBSTITUTIONS[char]
                result[i] = random.choice(substitutes)
                
        return ''.join(result)
        
    def _modify_random_positions(self, code: str) -> str:
        """Thay đổi 1-2 vị trí ngẫu nhiên"""
        result = list(code)
        positions_to_change = random.sample(range(len(code)), random.randint(1, 2))
        
        for pos in positions_to_change:
            result[pos] = random.choice(config.CHARSET)
            
        return ''.join(result)
        
    def _hybrid_variation(self, code: str) -> str:
        """Kết hợp nhiều phương pháp"""
        result = list(code)
        
        # Thay thế similar chars
        for i, char in enumerate(result):
            if char in config.CHAR_SUBSTITUTIONS and random.random() < 0.2:
                substitutes = config.CHAR_SUBSTITUTIONS[char]
                result[i] = random.choice(substitutes)
                
        # Thay đổi 1 vị trí ngẫu nhiên
        if random.random() < 0.5:
            pos = random.randint(0, len(result) - 1)
            result[pos] = random.choice(config.CHARSET)
            
        return ''.join(result)
        
    def generate_random(self) -> str:
        """Tạo code hoàn toàn ngẫu nhiên"""
        return ''.join(random.choices(config.CHARSET, k=config.CODE_LENGTH))
        
    def generate_sequential_from_known(self) -> str:
        """Tạo code theo sequence từ known codes"""
        if not self.known_codes:
            return self.generate_random()
            
        base_code = random.choice(self.known_codes)
        result = list(base_code)
        
        # Thay đổi vài ký tự cuối theo sequence
        for i in range(len(result) - 1, max(len(result) - 4, -1), -1):
            char = result[i]
            if char.isdigit():
                # Tăng số
                new_num = (int(char) + random.randint(1, 3)) % 10
                result[i] = str(new_num)
            elif char.isalpha():
                # Shift ký tự
                char_index = config.CHARSET.index(char)
                new_index = (char_index + random.randint(1, 3)) % len(config.CHARSET)
                result[i] = config.CHARSET[new_index]
                
        return ''.join(result)
        
    def generate_balanced(self) -> str:
        """Tạo code cân bằng chữ và số"""
        letters = random.choices(string.ascii_uppercase, k=config.CODE_LENGTH//2)
        digits = random.choices(string.digits, k=config.CODE_LENGTH//2)
        
        # Thêm ký tự cuối nếu độ dài lẻ
        if config.CODE_LENGTH % 2 == 1:
            extra = random.choice(config.CHARSET)
            letters.append(extra)
            
        # Trộn ngẫu nhiên
        all_chars = letters + digits
        random.shuffle(all_chars)
        
        return ''.join(all_chars)
        
    def generate_code(self, strategy: str = None) -> str:
        """Tạo code theo chiến lược được chỉ định"""
        if not strategy:
            # Chọn strategy theo tỷ lệ trong config
            rand = random.random()
            cumulative = 0
            
            for strat, probability in config.GENERATION_STRATEGIES.items():
                cumulative += probability
                if rand <= cumulative:
                    strategy = strat
                    break
            else:
                strategy = 'random'
                
        # Tạo code theo strategy
        if strategy == 'pattern_based':
            code = self.generate_pattern_based()
        elif strategy == 'prefix_based':
            code = self.generate_prefix_based()
        elif strategy == 'variation':
            code = self.generate_variation()
        elif strategy == 'year_pattern':
            code = self.generate_year_pattern()
        elif strategy == 'sequential':
            code = self.generate_sequential_from_known()
        elif strategy == 'balanced':
            code = self.generate_balanced()
        else:  # random
            code = self.generate_random()
            
        # Đảm bảo code hợp lệ và chưa tạo
        if not utils.validate_code(code):
            return self.generate_random()
            
        # Tránh duplicate
        attempts = 0
        while code in self.generated_codes and attempts < 10:
            code = self.generate_random()
            attempts += 1
            
        self.generated_codes.add(code)
        return code
        
    def generate_batch(self, count: int) -> List[str]:
        """Tạo một batch codes"""
        codes = []
        for _ in range(count):
            code = self.generate_code()
            codes.append(code)
        return codes
        
    def add_valid_code(self, code: str):
        """Thêm valid code để cải thiện pattern"""
        if code not in self.valid_codes:
            self.valid_codes.append(code)
            # Re-analyze patterns với code mới
            self._analyze_single_code(code)
            logger.info(f"Đã thêm valid code: {code}")
            
    def _analyze_single_code(self, code: str):
        """Phân tích pattern cho 1 code"""
        for char in code:
            self.char_frequencies[char] += 1
            
        for i, char in enumerate(code):
            self.position_frequencies[i][char] += 1
            
        for i in range(len(code) - 1):
            bigram = code[i:i+2]
            self.bigram_frequencies[bigram] += 1
            
    def get_statistics(self) -> Dict:
        """Lấy thống kê generator"""
        return {
            'known_codes_count': len(self.known_codes),
            'valid_codes_count': len(self.valid_codes),
            'generated_codes_count': len(self.generated_codes),
            'unique_chars': len(self.char_frequencies),
            'unique_bigrams': len(self.bigram_frequencies),
            'strategies': list(config.GENERATION_STRATEGIES.keys())
        }
