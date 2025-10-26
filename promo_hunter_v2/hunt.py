#!/usr/bin/env python3
"""
Promo Hunter V2 - Main hunting application
Tích hợp generator và checker để hunt codes hiệu quả
"""

import argparse
import sys
import time
import logging
from typing import Generator, Tuple, List

import config
import utils
from generator import PromoGenerator
from checker import PromoChecker

# Setup logging
logger = utils.setup_logging()

class PromoHunter:
    """Main class điều phối việc hunt promo codes"""
    
    def __init__(self):
        self.generator = PromoGenerator()
        self.checker = PromoChecker()
        self.total_target = 1000
        self.batch_size = config.BATCH_SIZE
        
    def codes_generator(self) -> Generator[Tuple[List[str], List[str]], None, None]:
        """Generator tạo codes theo batch"""
        generated_count = 0
        
        while generated_count < self.total_target:
            # Tính batch size thực tế
            remaining = self.total_target - generated_count
            actual_batch_size = min(self.batch_size, remaining)
            
            batch_codes = []
            batch_strategies = []
            
            for _ in range(actual_batch_size):
                # Chọn strategy ngẫu nhiên theo config
                import random
                rand = random.random()
                cumulative = 0
                strategy = 'random'
                
                for strat, probability in config.GENERATION_STRATEGIES.items():
                    cumulative += probability
                    if rand <= cumulative:
                        strategy = strat
                        break
                        
                # Tạo code
                code = self.generator.generate_code(strategy)
                batch_codes.append(code)
                batch_strategies.append(strategy)
                
            generated_count += len(batch_codes)
            yield batch_codes, batch_strategies
            
    def hunt(self, target_codes: int = 1000):
        """Bắt đầu hunt codes"""
        self.total_target = target_codes
        
        print("🎯 PROMO HUNTER V2 - BẮT ĐẦU SĂN CODES!")
        print("=" * 60)
        print(f"🎲 Target: {utils.format_number(target_codes)} codes")
        print(f"⚡ Workers: {config.MAX_WORKERS}")
        print(f"📦 Batch size: {config.BATCH_SIZE}")
        print(f"⏱️  Delay: {config.REQUEST_DELAY}s")
        print(f"🧠 Strategies: {list(config.GENERATION_STRATEGIES.keys())}")
        
        # Load previous session if exists
        if self.checker.load_session():
            print(f"📂 Loaded previous session với {len(self.checker.valid_codes)} valid codes")
            
        # Print generator stats
        gen_stats = self.generator.get_statistics()
        print(f"🔍 Generator: {gen_stats['known_codes_count']} known codes, {gen_stats['valid_codes_count']} valid codes")
        print("=" * 60)
        
        try:
            # Bắt đầu hunt
            start_time = time.time()
            self.checker.check_codes_stream(self.codes_generator(), target_codes)
            
        except KeyboardInterrupt:
            print("\n⏹️  Hunt bị dừng bởi người dùng")
        except Exception as e:
            logger.error(f"Lỗi trong quá trình hunt: {e}")
        finally:
            # Summary và save
            self._print_final_summary()
            self.checker.save_session()
            
    def _print_final_summary(self):
        """In tổng kết cuối cùng"""
        print("\n🏁 KẾT THÚC HUNT SESSION")
        self.checker.session_stats.print_summary()
        
        if self.checker.valid_codes:
            print(f"\n🎊 CODES VALID TÌM ĐƯỢC:")
            for i, code in enumerate(self.checker.valid_codes, 1):
                print(f"   {i}. {code}")
        else:
            print(f"\n😔 Không tìm thấy valid codes nào trong session này")
            
        print(f"\n💾 Kết quả đã lưu:")
        print(f"   📝 Valid codes: {config.VALID_CODES_FILE}")
        print(f"   📊 Chi tiết: {config.ALL_RESULTS_FILE}")
        print(f"   💽 Progress: {config.PROGRESS_FILE}")
        print(f"   📋 Logs: {config.LOG_FILE}")
        
    def continuous_hunt(self, session_duration: int = 3600):
        """Hunt liên tục trong khoảng thời gian"""
        print(f"🔄 CONTINUOUS HUNT - {session_duration}s ({utils.format_time(session_duration)})")
        
        start_time = time.time()
        session_count = 1
        
        while time.time() - start_time < session_duration:
            remaining_time = session_duration - (time.time() - start_time)
            estimated_codes = int(remaining_time * 1.3)  # Ước tính 1.3 codes/s
            
            print(f"\n🔥 SESSION {session_count} - Target: {estimated_codes} codes")
            
            try:
                self.hunt(estimated_codes)
            except KeyboardInterrupt:
                print(f"\n⏹️  Continuous hunt stopped")
                break
                
            session_count += 1
            
            # Check if found valid codes
            if self.checker.valid_codes:
                print(f"\n🎉 Tìm thấy {len(self.checker.valid_codes)} valid codes, tiếp tục hunt...")
                # Add valid codes to generator for better patterns
                for code in self.checker.valid_codes:
                    self.generator.add_valid_code(code)
                    
    def analyze_results(self):
        """Phân tích kết quả đã có"""
        print("📈 PHÂN TÍCH KẾT QUẢ")
        print("=" * 40)
        
        # Load results
        results_data = utils.load_json(config.ALL_RESULTS_FILE)
        if not results_data or 'results' not in results_data:
            print("❌ Không có dữ liệu để phân tích")
            return
            
        results = results_data['results']
        
        # Thống kê tổng quan
        total_checked = len(results)
        valid_count = sum(1 for r in results if r.get('is_valid', False))
        
        print(f"📊 Tổng checked: {utils.format_number(total_checked)}")
        print(f"🎯 Valid found: {utils.format_number(valid_count)}")
        print(f"📈 Success rate: {(valid_count/total_checked*100):.4f}%" if total_checked > 0 else "N/A")
        
        # Thống kê theo strategy
        strategy_stats = {}
        for result in results:
            strategy = result.get('strategy', 'unknown')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'total': 0, 'valid': 0}
            strategy_stats[strategy]['total'] += 1
            if result.get('is_valid', False):
                strategy_stats[strategy]['valid'] += 1
                
        print(f"\n📋 Thống kê theo strategy:")
        for strategy, stats in strategy_stats.items():
            success_rate = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"   {strategy}: {stats['total']} codes, {stats['valid']} valid ({success_rate:.2f}%)")
            
        # Valid codes
        valid_codes = [r['code'] for r in results if r.get('is_valid', False)]
        if valid_codes:
            print(f"\n🎊 Valid codes:")
            for i, code in enumerate(valid_codes, 1):
                print(f"   {i}. {code}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Promo Hunter V2 - Advanced Promo Code Hunter")
    parser.add_argument('--target', type=int, default=1000, help='Số codes target (default: 1000)')
    parser.add_argument('--continuous', type=int, help='Hunt liên tục trong X giây')
    parser.add_argument('--analyze', action='store_true', help='Phân tích kết quả có sẵn')
    parser.add_argument('--workers', type=int, help='Số worker threads')
    parser.add_argument('--delay', type=float, help='Delay giữa requests (giây)')
    
    args = parser.parse_args()
    
    # Override config nếu có
    if args.workers:
        config.MAX_WORKERS = args.workers
    if args.delay:
        config.REQUEST_DELAY = args.delay
        
    hunter = PromoHunter()
    
    if args.analyze:
        hunter.analyze_results()
    elif args.continuous:
        hunter.continuous_hunt(args.continuous)
    else:
        hunter.hunt(args.target)

if __name__ == "__main__":
    main()
