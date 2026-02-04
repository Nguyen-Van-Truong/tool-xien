"""
Headless Browser Test - No UI
Tests one account signup in headless mode
"""

import asyncio
import random
import sys
from datetime import datetime

# Add color output for Windows
try:
    from colorama import init, Fore, Style
    init()
except:
    class Fore:
        GREEN = RED = YELLOW = CYAN = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""

from utils.logger import log_info, log_success, log_error
from utils.email_service import generate_email, check_email_for_code
from utils.browser_handler import GrokBrowser


def print_step(step_num, total, message):
    """Print step with formatting"""
    print(f"\n{Fore.CYAN}[{step_num}/{total}] {message}{Fore.RESET}")


async def headless_test():
    """Run headless signup test"""
    
    print("\n" + "="*70)
    print(f"{Fore.GREEN}{Style.BRIGHT}GROK SIGNUP - HEADLESS TEST{Style.RESET_ALL}")
    print("="*70)
    
    # Generate random account
    account = {
        'email': f'grok_headless_{random.randint(1000,9999)}@example.com',
        'password': f'Pass{random.randint(1000,9999)}!Test',
        'first_name': random.choice(['John', 'Jane', 'Alex', 'Sam', 'Chris']),
        'last_name': random.choice(['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson'])
    }
    
    print(f"\n{Fore.WHITE}Account Details:{Fore.RESET}")
    print(f"  Email: {account['email']}")
    print(f"  Password: {account['password']}")
    print(f"  Name: {account['first_name']} {account['last_name']}")
    
    start_time = datetime.now()
    browser = None
    temp_email = None
    
    try:
        # Step 1: Generate temp email
        print_step(1, 8, "Generating temporary email...")
        temp_email = await generate_email()
        print(f"  {Fore.GREEN}✓{Fore.RESET} Temp email: {temp_email}")
        
        # Step 2: Start browser (VISIBLE for debugging)
        print_step(2, 8, "Starting browser (VISIBLE MODE)...")
        browser = GrokBrowser(headless=False)  # Changed to False for debugging
        await browser.start()
        print(f"  {Fore.GREEN}✓{Fore.RESET} Browser started")
        
        # Step 3: Navigate
        print_step(3, 8, "Navigating to signup page...")
        await browser.navigate_to_signup()
        print(f"  {Fore.GREEN}✓{Fore.RESET} Page loaded")
        
        # Step 4: Wait for page ready
        print_step(4, 8, "Waiting for page to be ready...")
        await browser.wait_for_cloudflare(timeout=60)
        print(f"  {Fore.GREEN}✓{Fore.RESET} Page ready")
        
        # Step 5: Fill form
        print_step(5, 8, "Filling signup form...")
        await browser.fill_email_field(temp_email)
        await browser.fill_name_fields(account['first_name'], account['last_name'])
        await browser.request_verification_code()
        print(f"  {Fore.GREEN}✓{Fore.RESET} Form submitted")
        
        # Step 6: Get verification code
        print_step(6, 8, "Waiting for verification code...")
        print(f"  {Fore.YELLOW}This may take 30-60 seconds...{Fore.RESET}")
        verification_code = await check_email_for_code(temp_email)
        
        if not verification_code:
            raise Exception("Failed to retrieve verification code from email")
        
        print(f"  {Fore.GREEN}✓{Fore.RESET} Code received: {verification_code}")
        
        # Step 7: Submit code
        print_step(7, 8, "Submitting verification code...")
        await browser.submit_verification_code(verification_code)
        print(f"  {Fore.GREEN}✓{Fore.RESET} Code submitted")
        
        # Step 8: Set credentials
        print_step(8, 8, "Setting account credentials...")
        await browser.set_account_credentials(account['email'], account['password'])
        await asyncio.sleep(3)
        
        # Check success
        success = await browser.check_signup_success()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*70)
        if success:
            print(f"{Fore.GREEN}{Style.BRIGHT}✅ TEST PASSED - ACCOUNT CREATED!{Style.RESET_ALL}")
            print("="*70)
            print(f"\n{Fore.WHITE}Success Details:{Fore.RESET}")
            print(f"  Account: {account['email']}")
            print(f"  Password: {account['password']}")
            print(f"  Temp Email: {temp_email}")
            print(f"  Code: {verification_code}")
            print(f"  Duration: {duration:.1f}s")
            
            # Save to success file
            with open('output/success.txt', 'a', encoding='utf-8') as f:
                f.write(f"{account['email']}|{account['password']}|{temp_email}|{verification_code}|{datetime.now().isoformat()}\n")
            
            return True
        else:
            print(f"{Fore.RED}{Style.BRIGHT}❌ TEST FAILED - VALIDATION FAILED{Style.RESET_ALL}")
            print("="*70)
            
            # Save to failed file
            with open('output/failed.txt', 'a', encoding='utf-8') as f:
                f.write(f"{account['email']}|Signup validation failed|{datetime.now().isoformat()}\n")
            
            return False
            
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*70)
        print(f"{Fore.RED}{Style.BRIGHT}❌ TEST FAILED - EXCEPTION{Style.RESET_ALL}")
        print("="*70)
        print(f"\n{Fore.RED}Error: {str(e)}{Fore.RESET}")
        print(f"Duration: {duration:.1f}s")
        
        # Save to failed file
        with open('output/failed.txt', 'a', encoding='utf-8') as f:
            f.write(f"{account.get('email', 'unknown')}|{str(e)}|{datetime.now().isoformat()}\n")
        
        # Print traceback for debugging
        import traceback
        print(f"\n{Fore.YELLOW}Traceback:{Fore.RESET}")
        traceback.print_exc()
        
        return False
        
    finally:
        if browser:
            print(f"\n{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Fore.RESET}")
            print(f"{Fore.YELLOW}⏸️  Keeping browser OPEN for 60 seconds...{Fore.RESET}")
            print(f"{Fore.YELLOW}   You can inspect the page manually{Fore.RESET}")
            print(f"{Fore.YELLOW}   Press Ctrl+C to close immediately{Fore.RESET}")
            print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Fore.RESET}")
            try:
                await asyncio.sleep(60)
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⏹️ Closing browser early...{Fore.RESET}")
            
            print(f"{Fore.CYAN}Closing browser...{Fore.RESET}")
            await browser.close()
            print(f"{Fore.GREEN}✓ Browser closed{Fore.RESET}")


if __name__ == "__main__":
    print(f"\n{Fore.YELLOW}Press Ctrl+C to stop{Fore.RESET}\n")
    
    try:
        result = asyncio.run(headless_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⏹️ Test stopped by user{Fore.RESET}")
        sys.exit(1)
