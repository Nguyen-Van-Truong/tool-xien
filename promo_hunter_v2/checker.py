#!/usr/bin/env python3
"""
Promo Code Checker V2 - Check codes với tối ưu hóa
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Tuple, Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging

import config
import utils

logger = logging.getLogger(__name__)

class PromoChecker:
    """Class check promo codes với tối ưu hóa"""
    
    def __init__(self):
        self.session_stats = utils.Statistics()
        self.checked_codes = set()
        self.valid_codes = []
        self.failed_codes = []
        self.lock = threading.Lock()
        
    def _build_headers(self) -> Dict[str, str]:
        """Tạo headers cho request"""
        headers = config.HTTP_HEADERS.copy()
        headers["Authorization"] = f"Bearer {config.BEARER_TOKEN}"
        return headers
        
    def _make_request(self, code: str) -> Tuple[bool, Optional[str], int]:
        """Thực hiện request check code"""
        url = config.API_URL + urllib.parse.quote(code)
        headers = self._build_headers()
        
        request = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(request, timeout=config.REQUEST_TIMEOUT) as response:
                status_code = response.getcode()
                data = response.read().decode('utf-8')
                
                try:
                    result = json.loads(data)
                    is_eligible = result.get('is_eligible', False)
                    
                    if is_eligible:
                        reason = "Valid"
                    else:
                        ineligible_reason = result.get('ineligible_reason', {})
                        if isinstance(ineligible_reason, dict):
                            reason = ineligible_reason.get('message', 'Invalid')
                        else:
                            reason = str(ineligible_reason) if ineligible_reason else 'Invalid'
                            
                    return is_eligible, reason, status_code
                    
                except json.JSONDecodeError:
                    # Lưu response HTML để debug
                    debug_file = f"debug_response_{code}_{int(time.time())}.html"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(data)
                    return False, f"Invalid JSON (saved to {debug_file})", status_code
                    
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP {e.code}"
            if e.code == 401:
                error_msg += " - Token có thể đã hết hạn"
            elif e.code == 403:
                error_msg += " - Bị chặn, cần cookies"
            elif e.code == 429:
                error_msg += " - Rate limited"
            return False, error_msg, e.code
            
        except urllib.error.URLError as e:
            return False, f"Connection error: {e.reason}", 0
            
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", 0
            
    def check_code_with_retry(self, code: str) -> Tuple[bool, str, int, str]:
        """Check code với retry logic"""
        strategy = "unknown"  # Có thể truyền vào từ generator
        
        for attempt in range(config.MAX_RETRIES + 1):
            try:
                is_valid, reason, status_code = self._make_request(code)
                
                # Retry conditions
                if status_code in [429, 500, 502, 503, 504] and attempt < config.MAX_RETRIES:
                    wait_time = (attempt + 1) * 0.5  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                    
                return is_valid, reason, status_code, strategy
                
            except Exception as e:
                if attempt == config.MAX_RETRIES:
                    return False, f"Final error: {str(e)}", 0, strategy
                time.sleep(0.5)
                
        return False, "Max retries exceeded", 0, strategy
        
    def check_single_code(self, code: str, strategy: str = "unknown") -> Dict:
        """Check một code và trả về kết quả chi tiết"""
        with self.lock:
            if code in self.checked_codes:
                return {
                    'code': code,
                    'is_valid': False,
                    'reason': 'Already checked',
                    'status_code': 0,
                    'strategy': strategy,
                    'timestamp': time.time(),
                    'duplicate': True
                }
            self.checked_codes.add(code)
            
        start_time = time.time()
        is_valid, reason, status_code, detected_strategy = self.check_code_with_retry(code)
        check_duration = time.time() - start_time
        
        # Update statistics
        with self.lock:
            self.session_stats.increment_checked()
            self.session_stats.increment_generated(strategy)
            
            if is_valid:
                self.session_stats.increment_valid(strategy)
                self.valid_codes.append(code)
                # Lưu ngay valid code
                utils.append_to_file(config.VALID_CODES_FILE, code)
                logger.info(f"🎉 FOUND VALID: {code}")
            else:
                self.failed_codes.append(code)
                if 'error' in reason.lower():
                    self.session_stats.increment_error()
                    
        result = {
            'code': code,
            'is_valid': is_valid,
            'reason': reason,
            'status_code': status_code,
            'strategy': strategy,
            'timestamp': time.time(),
            'duration': check_duration,
            'duplicate': False
        }
        
        return result
        
    def check_batch(self, codes: List[str], strategies: List[str] = None) -> List[Dict]:
        """Check một batch codes song song"""
        if not strategies:
            strategies = ["unknown"] * len(codes)
            
        results = []
        
        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_code = {
                executor.submit(self.check_single_code, code, strategy): (code, strategy)
                for code, strategy in zip(codes, strategies)
            }
            
            # Collect results
            for future in as_completed(future_to_code):
                code, strategy = future_to_code[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Print progress
                    status = "✅ VALID" if result['is_valid'] else f"❌ {result['reason']}"
                    print(f"[{self.session_stats.total_checked}/{len(codes)}] {code} ({strategy}): {status}")
                    
                except Exception as e:
                    logger.error(f"Error checking {code}: {e}")
                    results.append({
                        'code': code,
                        'is_valid': False,
                        'reason': f"Exception: {str(e)}",
                        'status_code': 0,
                        'strategy': strategy,
                        'timestamp': time.time(),
                        'duration': 0,
                        'duplicate': False
                    })
                    
                # Rate limiting
                time.sleep(config.REQUEST_DELAY / config.MAX_WORKERS)
                
        return results
        
    def check_codes_stream(self, codes_generator, max_codes: int = None):
        """Check codes từ generator (streaming)"""
        checked_count = 0
        
        try:
            for batch_codes, batch_strategies in codes_generator:
                if max_codes and checked_count >= max_codes:
                    break
                    
                # Limit batch size
                actual_batch_size = min(len(batch_codes), config.BATCH_SIZE)
                if max_codes:
                    actual_batch_size = min(actual_batch_size, max_codes - checked_count)
                    
                batch_codes = batch_codes[:actual_batch_size]
                batch_strategies = batch_strategies[:actual_batch_size]
                
                # Check batch
                results = self.check_batch(batch_codes, batch_strategies)
                
                # Save results
                self._save_batch_results(results)
                
                checked_count += len(results)
                
                # Print periodic stats
                if checked_count % 50 == 0:
                    self.print_progress()
                    
        except KeyboardInterrupt:
            logger.info("Check process interrupted by user")
        except Exception as e:
            logger.error(f"Error in check_codes_stream: {e}")
            
    def _save_batch_results(self, results: List[Dict]):
        """Lưu kết quả batch"""
        # Append to results file
        existing_results = utils.load_json(config.ALL_RESULTS_FILE)
        if 'results' not in existing_results:
            existing_results['results'] = []
            
        existing_results['results'].extend(results)
        existing_results['last_updated'] = time.time()
        
        utils.save_json(existing_results, config.ALL_RESULTS_FILE)
        
    def print_progress(self):
        """In tiến độ hiện tại"""
        stats = self.session_stats.get_summary()
        print(f"\n📊 [{stats['elapsed_formatted']}] Checked: {stats['total_checked']} | Valid: {stats['valid_found']} | Rate: {stats['check_rate']:.1f}/s | Success: {stats['success_rate']:.4f}%")
        
    def get_session_summary(self) -> Dict:
        """Lấy tổng kết session"""
        return {
            'statistics': self.session_stats.get_summary(),
            'valid_codes': self.valid_codes.copy(),
            'total_unique_checked': len(self.checked_codes),
            'error_codes_sample': self.failed_codes[-10:] if self.failed_codes else []
        }
        
    def save_session(self, filename: str = None):
        """Lưu session hiện tại"""
        if not filename:
            filename = config.PROGRESS_FILE
            
        session_data = self.get_session_summary()
        utils.save_json(session_data, filename)
        logger.info(f"Session saved to {filename}")
        
    def load_session(self, filename: str = None):
        """Load session từ file"""
        if not filename:
            filename = config.PROGRESS_FILE
            
        session_data = utils.load_json(filename)
        if session_data:
            # Restore valid codes
            self.valid_codes = session_data.get('valid_codes', [])
            # Note: không restore checked_codes để tránh skip
            logger.info(f"Session loaded from {filename}")
            return True
        return False
