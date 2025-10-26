import os
from typing import Dict, List

class Idfirstset:
    def __init__(self, key: str = "default_key"):
        self.key = self._process_key(key)
    
    def _process_key(self, key: str) -> bytes:
        """Xử lý key thành bytes và đảm bảo độ dài phù hợp"""
        key_bytes = key.encode()
        # Tạo key có độ dài 32 bytes
        if len(key_bytes) < 32:
            key_bytes = key_bytes * (32 // len(key_bytes) + 1)
        return key_bytes[:32]
    
    def _transform_data(self, data: bytes, key: bytes) -> bytes:
        """Biến đổi dữ liệu bằng phép XOR và dịch bit"""
        result = bytearray()
        for i, byte in enumerate(data):
            # XOR với key
            transformed = byte ^ key[i % len(key)]
            # Dịch bit
            transformed = ((transformed << 2) | (transformed >> 6)) & 0xFF
            result.append(transformed)
        return bytes(result)
    
    def encrypt_card(self, card: Dict[str, str]) -> str:
        """Mã hóa thông tin một thẻ"""
        # Chuyển thông tin thẻ thành chuỗi
        card_str = f"{card['number']}|{card['expiry']}|{card['cvc']}|{card.get('name', '')}"
        # Mã hóa
        encrypted = self._transform_data(card_str.encode(), self.key)
        # Chuyển thành hex string
        return encrypted.hex()
    
    def decrypt_card(self, encrypted_str: str) -> Dict[str, str]:
        """Giải mã thông tin một thẻ"""
        try:
            # Chuyển từ hex string về bytes
            encrypted = bytes.fromhex(encrypted_str)
            # Giải mã
            decrypted = self._transform_data(encrypted, self.key)
            # Chuyển về chuỗi và tách thông tin
            card_str = decrypted.decode()
            parts = card_str.split('|')
            return {
                'number': parts[0],
                'expiry': parts[1],
                'cvc': parts[2],
                'name': parts[3] if len(parts) > 3 else None
            }
        except:
            return None
    
    def encrypt_file(self, input_file: str, output_file: str):
        """Mã hóa toàn bộ file cards.txt"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                cards = []
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split('|')
                    card = {
                        'number': parts[0],
                        'expiry': parts[1] if len(parts) > 1 else '',
                        'cvc': parts[2] if len(parts) > 2 else '',
                        'name': parts[3] if len(parts) > 3 else None
                    }
                    cards.append(card)
            
            # Mã hóa từng thẻ và lưu vào file mới
            with open(output_file, 'w', encoding='utf-8') as f:
                for card in cards:
                    encrypted = self.encrypt_card(card)
                    f.write(f"{encrypted}\n")
            
            return True
        except Exception as e:
            print(f"Lỗi khi mã hóa file: {str(e)}")
            return False
    
    def decrypt_file(self, input_file: str, output_file: str):
        """Giải mã file cards.txt đã mã hóa"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                cards = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    card = self.decrypt_card(line)
                    if card:
                        cards.append(card)
            
            # Lưu thông tin thẻ đã giải mã vào file mới
            with open(output_file, 'w', encoding='utf-8') as f:
                for card in cards:
                    card_str = f"{card['number']}|{card['expiry']}|{card['cvc']}"
                    if card['name']:
                        card_str += f"|{card['name']}"
                    f.write(f"{card_str}\n")
            
            return True
        except Exception as e:
            print(f"Lỗi khi giải mã file: {str(e)}")
            return False 