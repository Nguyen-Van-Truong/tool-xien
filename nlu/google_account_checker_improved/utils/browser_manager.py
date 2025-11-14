#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class BrowserManager:
    """Quản lý browser với anti-detection features"""

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]

    @staticmethod
    def create_driver(config, thread_id=0):
        """Tạo Chrome driver với anti-detection"""
        chrome_options = Options()

        # Basic options
        chrome_opts_config = config['chrome_options']

        if config['performance']['headless']:
            chrome_options.add_argument('--headless=new')

        chrome_options.add_argument(f"--window-size={chrome_opts_config['window_size']}")

        if chrome_opts_config['no_sandbox']:
            chrome_options.add_argument('--no-sandbox')

        if chrome_opts_config['disable_dev_shm_usage']:
            chrome_options.add_argument('--disable-dev-shm-usage')

        if chrome_opts_config['disable_gpu']:
            chrome_options.add_argument('--disable-gpu')

        # Anti-detection options
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Random user agent
        if config['anti_detection']['rotate_user_agents']:
            user_agent = random.choice(BrowserManager.USER_AGENTS)
            chrome_options.add_argument(f'user-agent={user_agent}')

        # Performance options
        if config['performance']['disable_images']:
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.password_manager_enabled": False,
                "credentials_enable_service": False
            }
            chrome_options.add_experimental_option("prefs", prefs)

        # Additional privacy/speed options
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--incognito')

        # Unique debugging port per thread
        debug_port = chrome_opts_config['remote_debugging_base_port'] + thread_id
        chrome_options.add_argument(f'--remote-debugging-port={debug_port}')

        try:
            # Try using chromedriver from driver folder first
            try:
                service = Service('../runhere/driver/chromedriver.exe')
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except:
                # Fallback to system chromedriver or Selenium Manager
                driver = webdriver.Chrome(options=chrome_options)

            # Stealth mode - remove webdriver flag
            if config['anti_detection']['use_stealth_mode']:
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": driver.execute_script("return navigator.userAgent").replace('Headless', '')
                })
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Set timeouts
            driver.set_page_load_timeout(config['performance']['page_load_timeout'])

            return driver

        except Exception as e:
            raise Exception(f"Failed to create driver: {e}")

    @staticmethod
    def random_delay(config):
        """Random delay để tránh detection"""
        if config['anti_detection']['random_delays']:
            delay = random.uniform(
                config['anti_detection']['min_delay_seconds'],
                config['anti_detection']['max_delay_seconds']
            )
            time.sleep(delay)
        else:
            time.sleep(1.0)

    @staticmethod
    def short_delay():
        """Short random delay"""
        time.sleep(random.uniform(0.3, 0.7))

    @staticmethod
    def close_driver(driver):
        """Safely close driver"""
        if driver:
            try:
                driver.quit()
                time.sleep(0.3)
            except:
                pass
