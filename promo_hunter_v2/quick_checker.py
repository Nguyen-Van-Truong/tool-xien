#!/usr/bin/env python3
"""
Quick Checker - Tool check promo codes nhanh
Standalone tool để check codes từ file
"""

import argparse
import sys
import time
from typing import List
import config
import utils
from checker import PromoChecker

def check_codes_from_file(filename: str, max_codes: int = None):
    """Check codes từ file"""
    print(f"📖 Đọc codes từ file: {filename}")
    
    # Read codes
    codes = utils.read_codes_from_file(filename)
    if not codes:
        print(f"❌ Không tìm thấy codes hợp lệ trong file {filename}")
        return
        
    total_codes = len(codes)
    if max_codes:
        codes = codes[:max_codes]
        
    print(f"✅ Đã load {len(codes)} codes (tổng trong file: {total_codes})")
    
    # Initialize checker
    checker = PromoChecker()
    
    print(f"\n🚀 Bắt đầu check {len(codes)} codes...")
    print(f"⚡ Workers: {config.MAX_WORKERS}")
    print(f"⏱️  Delay: {config.REQUEST_DELAY}s")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Check all codes
        results = checker.check_batch(codes)
        
        # Analysis
        valid_codes = [r['code'] for r in results if r['is_valid']]
        invalid_codes = [r for r in results if not r['is_valid']]
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 50)
        print("🏁 KẾT QUẢ CHECK")
        print("=" * 50)
        print(f"⏱️  Thời gian: {utils.format_time(elapsed)}")
        print(f"📊 Tổng check: {len(results)}")
        print(f"✅ Valid: {len(valid_codes)}")
        print(f"❌ Invalid: {len(invalid_codes)}")
        print(f"⚡ Tốc độ: {len(results)/elapsed:.2f} codes/giây")
        print(f"📈 Tỷ lệ thành công: {(len(valid_codes)/len(results)*100):.2f}%")
        
        if valid_codes:
            print(f"\n🎉 VALID CODES FOUND:")
            for i, code in enumerate(valid_codes, 1):
                print(f"   {i}. {code}")
                
            # Save valid codes
            valid_filename = "found_valid_codes.txt"
            with open(valid_filename, 'w', encoding='utf-8') as f:
                for code in valid_codes:
                    f.write(code + '\n')
            print(f"\n💾 Valid codes đã lưu vào: {valid_filename}")
        else:
            print(f"\n😔 Không tìm thấy valid codes nào")
            
        # Error analysis
        error_reasons = {}
        for result in invalid_codes:
            reason = result['reason']
            error_reasons[reason] = error_reasons.get(reason, 0) + 1
            
        if error_reasons:
            print(f"\n📋 Phân tích lỗi:")
            for reason, count in sorted(error_reasons.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(invalid_codes)) * 100
                print(f"   {reason}: {count} ({percentage:.1f}%)")
                
        # Save detailed results
        detailed_filename = f"check_results_{int(time.time())}.json"
        detailed_data = {
            'summary': {
                'total_checked': len(results),
                'valid_found': len(valid_codes),
                'invalid_found': len(invalid_codes),
                'elapsed_time': elapsed,
                'check_rate': len(results)/elapsed,
                'success_rate': (len(valid_codes)/len(results)*100) if results else 0
            },
            'valid_codes': valid_codes,
            'detailed_results': results,
            'error_analysis': error_reasons
        }
        
        utils.save_json(detailed_data, detailed_filename)
        print(f"📄 Kết quả chi tiết đã lưu vào: {detailed_filename}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Check bị dừng bởi người dùng")
        checker.session_stats.print_summary()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Quick Promo Code Checker")
    parser.add_argument('filename', help='File chứa codes cần check')
    parser.add_argument('--max', type=int, help='Số codes tối đa cần check')
    parser.add_argument('--workers', type=int, help='Số worker threads')
    parser.add_argument('--delay', type=float, help='Delay giữa requests (giây)')
    
    args = parser.parse_args()
    
    # Override config nếu có
    if args.workers:
        config.MAX_WORKERS = args.workers
    if args.delay:
        config.REQUEST_DELAY = args.delay
        
    # Validate file
    try:
        with open(args.filename, 'r') as f:
            pass
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file: {args.filename}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        sys.exit(1)
        
    # Check codes
    check_codes_from_file(args.filename, args.max)

if __name__ == "__main__":
    main()
