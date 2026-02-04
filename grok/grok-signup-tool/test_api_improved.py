"""
Test Improved API Direct Mode
Tests new implementation with browser-based Turnstile solving
"""

import asyncio
import random
import sys
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init()
except:
    class Fore:
        GREEN = RED = YELLOW = CYAN = WHITE = RESET = ""
    class Style:
        BRIGHT = RESET_ALL = ""

from utils.api_direct_improved import signup_account_api_improved


async def test_api_direct_improved():
    """Test improved API Direct mode with browser solving"""
    
    print("\n" + "="*70)
    print(f"{Fore.GREEN}{Style.BRIGHT}API DIRECT MODE - IMPROVED TEST{Style.RESET_ALL}")
    print("="*70)
    
    # Generate test account
    account = {
        'email': f'api_test_{random.randint(1000,9999)}@example.com',
        'password': f'ApiPass{random.randint(100,999)}!',
        'first_name': random.choice(['API', 'Direct', 'Fast', 'Test']),
        'last_name': random.choice(['User', 'Mode', 'Account'])
    }
    
    print(f"\n{Fore.WHITE}Test Account:{Fore.RESET}")
    print(f"  Email: {account['email']}")
    print(f"  Password: {account['password']}")
    print(f"  Name: {account['first_name']} {account['last_name']}")
    
    print(f"\n{Fore.CYAN}Method: Browser-based Turnstile Solving (FREE){Fore.RESET}")
    print(f"{Fore.YELLOW}Note: Browser will open visibly to solve Turnstile{Fore.RESET}")
    
    start_time = datetime.now()
    
    try:
        print(f"\n{Fore.CYAN}[1/1] Starting API Direct signup...{Fore.RESET}")
        
        result = await signup_account_api_improved(
            email=account['email'],
            password=account['password'],
            first_name=account['first_name'],
            last_name=account['last_name'],
            solver_method='browser'  # Using free browser method
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*70)
        
        if result['status'] == 'success':
            print(f"{Fore.GREEN}{Style.BRIGHT}✅ TEST PASSED - ACCOUNT CREATED!{Style.RESET_ALL}")
            print("="*70)
            print(f"\n{Fore.WHITE}Success Details:{Fore.RESET}")
            print(f"  Account: {result['email']}")
            print(f"  Password: {result['password']}")
            print(f"  Temp Email: {result.get('temp_email')}")
            print(f"  Code: {result.get('verification_code')}")
            print(f"  Duration: {duration:.1f}s")
            
            # Save to success file
            with open('output/success.txt', 'a', encoding='utf-8') as f:
                f.write(f"{result['email']}|{result['password']}|{result.get('temp_email')}|{result.get('verification_code')}|{datetime.now().isoformat()}\n")
            
            return True
            
        else:
            error = result.get('error', 'Unknown error')
            print(f"{Fore.RED}{Style.BRIGHT}❌ TEST FAILED{Style.RESET_ALL}")
            print("="*70)
            print(f"\n{Fore.RED}Error: {error}{Fore.RESET}")
            print(f"Duration: {duration:.1f}s")
            
            # Check if it's expected failure
            if 'Turnstile' in error or 'Browser Mode' in error:
                print(f"\n{Fore.YELLOW}💡 This is expected if Turnstile solving failed{Fore.RESET}")
                print(f"{Fore.YELLOW}💡 Recommendation: Use Browser Mode (main tool){Fore.RESET}")
            
            # Save to failed file
            with open('output/failed.txt', 'a', encoding='utf-8') as f:
                f.write(f"{account['email']}|{error}|{datetime.now().isoformat()}\n")
            
            return False
            
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*70)
        print(f"{Fore.RED}{Style.BRIGHT}❌ TEST EXCEPTION{Style.RESET_ALL}")
        print("="*70)
        print(f"\n{Fore.RED}Exception: {str(e)}{Fore.RESET}")
        print(f"Duration: {duration:.1f}s")
        
        import traceback
        print(f"\n{Fore.YELLOW}Traceback:{Fore.RESET}")
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    print(f"\n{Fore.YELLOW}Testing API Direct Mode with Browser Solving...{Fore.RESET}")
    print(f"{Fore.YELLOW}Press Ctrl+C to stop{Fore.RESET}\n")
    
    try:
        result = asyncio.run(test_api_direct_improved())
        
        print("\n" + "="*70)
        if result:
            print(f"{Fore.GREEN}🎉 API Direct Mode: WORKING{Fore.RESET}")
        else:
            print(f"{Fore.YELLOW}⚠️ API Direct Mode: NEEDS WORK{Fore.RESET}")
            print(f"{Fore.CYAN}👉 Recommend: Use Browser Mode instead{Fore.RESET}")
        print("="*70)
        
        sys.exit(0 if result else 1)
        
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⏹️ Test stopped by user{Fore.RESET}")
        sys.exit(1)
