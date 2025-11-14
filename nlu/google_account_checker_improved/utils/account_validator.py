#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class AccountValidator:
    """Validate Google account credentials"""

    @staticmethod
    def validate_account(driver, username, password, config):
        """
        Validate a single Google account

        Returns:
            dict: {
                'status': 'success'|'wrong_password'|'captcha'|'phone_verification'|'error',
                'message': str,
                'details': str
            }
        """
        result = {
            'status': 'unknown',
            'message': '',
            'details': ''
        }

        try:
            # Step 1: Navigate to Google login
            driver.get("https://accounts.google.com/signin/v2/identifier")
            time.sleep(random.uniform(0.8, 1.5))

            # Step 2: Enter email
            try:
                email_field = WebDriverWait(driver, config['performance']['element_wait_timeout']).until(
                    EC.presence_of_element_located((By.ID, "identifierId"))
                )

                # Human-like typing
                AccountValidator._human_type(email_field, username)
                time.sleep(random.uniform(0.4, 0.8))

                next_btn = driver.find_element(By.ID, "identifierNext")
                next_btn.click()
                time.sleep(random.uniform(1.2, 2.0))

            except TimeoutException:
                result['status'] = 'error'
                result['message'] = 'Email field timeout'
                return result
            except Exception as e:
                result['status'] = 'error'
                result['message'] = f'Email step error: {str(e)[:50]}'
                return result

            # Check for email not found
            try:
                page_source = driver.page_source.lower()
                if "couldn't find your google account" in page_source or "couldn't find" in page_source:
                    result['status'] = 'wrong_password'  # Email not exist = invalid credential
                    result['message'] = 'Email not found'
                    return result
            except:
                pass

            # Step 3: Enter password
            try:
                password_field = WebDriverWait(driver, config['performance']['element_wait_timeout']).until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )

                # Human-like typing
                AccountValidator._human_type(password_field, password)
                time.sleep(random.uniform(0.4, 0.8))

                password_next = driver.find_element(By.ID, "passwordNext")
                password_next.click()
                time.sleep(random.uniform(2.5, 3.5))

            except TimeoutException:
                # Password field not found - might be captcha or other challenge
                result['status'] = 'captcha'
                result['message'] = 'Password field not found - possible captcha'
                return result
            except Exception as e:
                result['status'] = 'error'
                result['message'] = f'Password step error: {str(e)[:50]}'
                return result

            # Step 4: Analyze result
            time.sleep(random.uniform(1.5, 2.5))

            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()

            # Check for success
            success_urls = config['validation']['check_login_success_urls']
            for success_url in success_urls:
                if success_url.lower() in current_url:
                    result['status'] = 'success'
                    result['message'] = 'Login successful'
                    result['details'] = f'Redirected to {current_url[:100]}'
                    return result

            # Check for wrong password (explicit)
            wrong_password_keywords = [
                'wrong password',
                'incorrect password',
                'wrong-password'
            ]

            for keyword in wrong_password_keywords:
                if keyword in page_source:
                    result['status'] = 'wrong_password'
                    result['message'] = 'Wrong password detected'
                    result['details'] = keyword
                    return result

            # Check for phone verification
            phone_verify_keywords = [
                'verify it\'s you',
                'verify your identity',
                'phone number',
                'recovery phone',
                'get a verification code'
            ]

            for keyword in phone_verify_keywords:
                if keyword in page_source:
                    result['status'] = 'phone_verification'
                    result['message'] = 'Phone verification required'
                    result['details'] = keyword
                    return result

            # Check for captcha
            captcha_keywords = [
                'captcha',
                'unusual activity',
                'automated requests',
                'verify you\'re not a robot'
            ]

            for keyword in captcha_keywords:
                if keyword in page_source:
                    result['status'] = 'captcha'
                    result['message'] = 'Captcha detected'
                    result['details'] = keyword
                    return result

            # Check for 2-step verification
            if '2-step verification' in page_source or 'two-step verification' in page_source:
                result['status'] = 'success'  # Account valid but has 2FA
                result['message'] = 'Account valid - 2FA enabled'
                result['details'] = '2-step verification'
                return result

            # Check if still on challenge page
            if 'challenge' in current_url or 'signin' in current_url:
                result['status'] = 'success'  # Might be new account or security check
                result['message'] = 'Login challenge - likely valid account'
                result['details'] = 'Still on challenge page'
                return result

            # Default: consider success if no explicit error
            result['status'] = 'success'
            result['message'] = 'No explicit error detected'
            result['details'] = current_url[:100]
            return result

        except Exception as e:
            result['status'] = 'error'
            result['message'] = f'Validation error: {str(e)[:100]}'
            return result

    @staticmethod
    def _human_type(element, text, min_delay=0.05, max_delay=0.15):
        """Type text like a human with random delays"""
        import random
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))


# Import at top for random
import random
