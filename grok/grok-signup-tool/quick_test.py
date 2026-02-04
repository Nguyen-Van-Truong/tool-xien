"""
Quick Manual Test - Browser Mode with 1 Random Account
Run GUI and generate 1 account to verify
"""

import asyncio
import random
from utils.logger import log_info, log_success, log_error
from utils.email_service import generate_email, check_email_for_code
from utils.browser_handler import GrokBrowser

async def quick_test():
    """Quick single account test"""
    print("\n" + "="*60)
    print("🧪 QUICK MANUAL TEST - Browser Mode")
    print("="*60)
    
    # Random account
    account = {
        'email': f'grok_test_{random.randint(1000,9999)}@example.com',
        'password': f'TestPass{random.randint(100,999)}!',
        'first_name': random.choice(['John', 'Jane', 'Alex', 'Sam']),
        'last_name': random.choice(['Smith', 'Johnson', 'Williams', 'Brown'])
    }
    
    log_info(f"📧 Test Account: {account['email']}")
    log_info(f"👤 Name: {account['first_name']} {account['last_name']}")
    
    browser = None
    try:
        # Generate email
        log_info("\n📧 Step 1: Generating temp email...")
        temp_email = await generate_email()
        log_success(f"✅ Temp: {temp_email}")
        
        # Start browser (visible for manual inspection)
        log_info("\n🌐 Step 2: Starting browser (VISIBLE)...")
        browser = GrokBrowser(headless=False)
        await browser.start()
        
        # Navigate
        log_info("\n🔗 Step 3: Navigating to signup...")
        await browser.navigate_to_signup()
        
        # Wait for you to manually inspect
        log_info("\n⏸️ Browser is OPEN. You can:")
        log_info("  - Check if page loaded correctly")
        log_info("  - See if Cloudflare appears")
        log_info("  - Inspect form elements")
        log_info("\nWaiting 15s for manual inspection...")
        await asyncio.sleep(15)
        
        # Try to handle page
        log_info("\n🔐 Step 4: Attempting to wait for form...")
        await browser.wait_for_cloudflare(timeout=60)
        
        log_info("\n📝 Step 5: Filling form...")
        await browser.fill_email_field(temp_email)
        await browser.fill_name_fields(account['first_name'], account['last_name'])
        await browser.request_verification_code()
        
        log_info("\n📬 Step 6: Waiting for code...")
        code = await check_email_for_code(temp_email)
        
        if code:
            log_success(f"✅ Got code: {code}")
            await browser.submit_verification_code(code)
            
            log_info("\n🔑 Step 7: Setting credentials...")
            await browser.set_account_credentials(account['email'], account['password'])
            
            await asyncio.sleep(3)
            success = await browser.check_signup_success()
            
            if success:
                log_success("\n🎉 TEST PASSED - Account created!")
                print(f"\n✅ Account: {account['email']}")
                print(f"✅ Password: {account['password']}")
            else:
                log_error("\n❌ TEST FAILED - Validation failed")
        else:
            log_error("\n❌ TEST FAILED - No verification code")
            
    except Exception as e:
        log_error(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            log_info("\n⏸️ Keeping browser open for 10s...")
            await asyncio.sleep(10)
            await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(quick_test())
    except KeyboardInterrupt:
        print("\n\n⏹️ Test stopped")
