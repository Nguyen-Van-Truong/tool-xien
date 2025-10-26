#!/usr/bin/env python3
"""
Quick Generator - Tool tạo promo codes nhanh
Standalone tool để tạo codes mà không cần check
"""

import argparse
import sys
import random
from typing import List
import config
import utils
from generator import PromoGenerator

def generate_and_save(count: int, strategy: str = None, output_file: str = "generated_codes.txt", 
                     include_known_valid: bool = True, avoid_duplicates: bool = True):
    """Tạo codes và lưu vào file"""
    print(f"🎲 Tạo {count} promo codes...")
    
    generator = PromoGenerator()
    codes = []
    
    # Load codes đã check để tránh duplicate
    checked_codes = set()
    if avoid_duplicates:
        # Load từ các file cũ
        old_files = [
            "../checkpromogpt3m/promocode.txt",
            "../checkpromogpt3m/valid_codes.txt", 
            "generated_codes.txt",
            "valid_codes.txt",
            "found_valid_codes.txt"
        ]
        for file_path in old_files:
            old_codes = utils.read_codes_from_file(file_path)
            checked_codes.update(old_codes)
        
        print(f"📂 Đã load {len(checked_codes)} codes cũ để tránh duplicate")
    
    # Thêm code valid ở đầu để test
    if include_known_valid:
        test_code = "CYG9B5A7ATFFZ4XG"
        codes.append(test_code)
        print(f"✅ Đã thêm test code ở vị trí đầu: {test_code}")
        
    # Statistics
    strategy_counts = {}
    duplicate_count = 0
    
    # Tạo codes mới
    target_new_codes = count - len(codes)
    generated_count = 0
    
    while generated_count < target_new_codes:
        if strategy:
            code = generator.generate_code(strategy)
            used_strategy = strategy
        else:
            # Random strategy
            strategies = list(config.GENERATION_STRATEGIES.keys())
            used_strategy = random.choice(strategies)
            code = generator.generate_code(used_strategy)
        
        # Kiểm tra duplicate
        if avoid_duplicates and (code in checked_codes or code in codes):
            duplicate_count += 1
            continue
            
        codes.append(code)
        generated_count += 1
        
        # Count strategies
        strategy_counts[used_strategy] = strategy_counts.get(used_strategy, 0) + 1
        
        # Progress
        if generated_count % 1000 == 0 or generated_count == target_new_codes:
            print(f"  Progress: {len(codes)}/{count} (skipped {duplicate_count} duplicates)")
            
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        for code in codes:
            f.write(code + '\n')
            
    print(f"\n✅ Đã tạo {len(codes)} codes và lưu vào: {output_file}")
    print(f"🔄 Đã skip {duplicate_count} codes trùng lặp")
    
    # Print strategy breakdown
    if strategy_counts:
        print(f"\n📊 Phân bố strategies:")
        total_strategy_codes = sum(strategy_counts.values())
        for strategy, count in strategy_counts.items():
            percentage = (count / total_strategy_codes) * 100
            print(f"   {strategy}: {count} codes ({percentage:.1f}%)")
        
    return codes

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Quick Promo Code Generator V2")
    parser.add_argument('count', type=int, help='Số lượng codes cần tạo')
    parser.add_argument('--strategy', choices=list(config.GENERATION_STRATEGIES.keys()), 
                       help='Strategy cụ thể (nếu không chỉ định sẽ random)')
    parser.add_argument('--output', default='generated_codes.txt', 
                       help='File output (default: generated_codes.txt)')
    parser.add_argument('--preview', type=int, default=10,
                       help='Số codes preview (default: 10)')
    parser.add_argument('--no-test-code', action='store_true',
                       help='Không thêm test code ở đầu')
    parser.add_argument('--allow-duplicates', action='store_true',
                       help='Cho phép codes trùng lặp')
    
    args = parser.parse_args()
    
    if args.count <= 0:
        print("❌ Số lượng codes phải > 0")
        sys.exit(1)
        
    # Generate codes
    codes = generate_and_save(
        args.count, 
        args.strategy, 
        args.output,
        include_known_valid=not args.no_test_code,
        avoid_duplicates=not args.allow_duplicates
    )
    
    # Preview
    preview_count = min(args.preview, len(codes))
    if preview_count > 0:
        print(f"\n👀 Preview {preview_count} codes đầu tiên:")
        for i, code in enumerate(codes[:preview_count], 1):
            print(f"   {i:2d}. {code}")
            
        if len(codes) > preview_count:
            print(f"   ... và {len(codes) - preview_count} codes khác")

if __name__ == "__main__":
    main()
