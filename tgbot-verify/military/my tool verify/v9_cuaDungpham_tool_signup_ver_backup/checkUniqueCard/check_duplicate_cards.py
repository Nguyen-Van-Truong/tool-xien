"""
Check Duplicate Cards Tool
- Đọc file cards.txt
- Tìm các thẻ có số trùng nhau (>= 2 lần)
- Đánh dấu [DUPLICATE] ở cuối dòng các thẻ trùng
- Xuất file kết quả cards_checked.txt
"""

import re
from collections import Counter

def extract_card_number(line):
    """Trích xuất số thẻ từ dòng"""
    # Format: Live | 5518276012188579|08|2027|603 ...
    # Tìm số thẻ (16 chữ số đầu tiên sau "Live |")
    match = re.search(r'Live\s*\|\s*(\d{16})', line)
    if match:
        return match.group(1)
    return None

def check_duplicate_cards(input_file, output_file=None):
    """Kiểm tra thẻ trùng và đánh dấu"""
    
    if output_file is None:
        output_file = input_file.replace('.txt', '_checked.txt')
    
    # Đọc file
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Trích xuất tất cả số thẻ và đếm
    card_numbers = []
    for line in lines:
        card_num = extract_card_number(line)
        if card_num:
            card_numbers.append(card_num)
    
    # Đếm số lần xuất hiện của mỗi số thẻ
    card_counts = Counter(card_numbers)
    
    # Tìm các thẻ trùng (xuất hiện >= 2 lần)
    duplicate_cards = {card: count for card, count in card_counts.items() if count >= 2}
    
    print(f"📊 Tổng số dòng có thẻ: {len(card_numbers)}")
    print(f"📊 Số thẻ unique: {len(card_counts)}")
    print(f"📊 Số thẻ bị trùng (>=2 lần): {len(duplicate_cards)}")
    
    if duplicate_cards:
        print("\n🔴 Các thẻ bị trùng:")
        for card, count in sorted(duplicate_cards.items(), key=lambda x: -x[1]):
            print(f"   - {card}: {count} lần")
    
    # Đánh dấu các dòng có thẻ trùng
    marked_lines = []
    for line in lines:
        line = line.rstrip('\n\r')
        card_num = extract_card_number(line)
        
        if card_num and card_num in duplicate_cards:
            count = duplicate_cards[card_num]
            # Thêm đánh dấu [DUPLICATE x{count}]
            if '[DUPLICATE' not in line:  # Tránh đánh dấu trùng
                line = f"{line}  [DUPLICATE x{count}]"
        
        marked_lines.append(line)
    
    # Ghi file kết quả
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(marked_lines))
    
    print(f"\n✅ Đã lưu kết quả vào: {output_file}")
    
    # Tạo báo cáo chi tiết
    report_file = input_file.replace('.txt', '_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("BÁO CÁO KIỂM TRA THẺ TRÙNG\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Tổng số dòng có thẻ: {len(card_numbers)}\n")
        f.write(f"Số thẻ unique: {len(card_counts)}\n")
        f.write(f"Số thẻ bị trùng (>=2 lần): {len(duplicate_cards)}\n\n")
        
        if duplicate_cards:
            f.write("-" * 60 + "\n")
            f.write("CHI TIẾT CÁC THẺ TRÙNG:\n")
            f.write("-" * 60 + "\n\n")
            
            for card, count in sorted(duplicate_cards.items(), key=lambda x: -x[1]):
                f.write(f"🔴 Thẻ: {card} - Xuất hiện {count} lần\n")
                # Tìm các dòng chứa thẻ này
                for i, line in enumerate(lines, 1):
                    if card in line:
                        f.write(f"   Dòng {i}: {line.strip()[:80]}...\n")
                f.write("\n")
    
    print(f"📝 Đã lưu báo cáo vào: {report_file}")
    
    return {
        'total_cards': len(card_numbers),
        'unique_cards': len(card_counts),
        'duplicate_count': len(duplicate_cards),
        'duplicates': duplicate_cards
    }

if __name__ == '__main__':
    import sys
    
    # Mặc định đọc cards.txt trong cùng thư mục
    input_file = 'cards.txt'
    
    # Hoặc lấy từ command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    print("🔍 Đang kiểm tra thẻ trùng...\n")
    result = check_duplicate_cards(input_file)
    print("\n✅ Hoàn thành!")
