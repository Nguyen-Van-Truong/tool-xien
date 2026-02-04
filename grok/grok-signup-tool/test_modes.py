"""
Test script for Grok Signup Tool
Tests both Browser Mode and API Direct Mode
"""

import asyncio
import sys
from utils.logger import log_info, log_success, log_error
from utils.email_service import generate_email, check_email_for_code
from utils.browser_handler import GrokBrowser
from utils.api_direct import signup_account_api


async def test_browser_mode():
    """Test Browser Mode signup"""
    log_info("\n" + "="*60)
    log_info("🧪 TEST 1: BROWSER MODE")
    log_info("="*60)
    
    test_account = {
        'email': 'test_browser@example.com',
        'password': 'TestPassword123!',
        'first_name': 'Browser',
        'last_name': 'Test'
    }
    
    browser = None
    temp_email = None
    
    try:
        # Step 1: Generate email
        log_info("📧 Generating temporary email...")
        temp_email = await generate_email()
        log_success(f"✅ Temp email: {temp_email}")
        
        # Step 2: Start browser
        log_info("🌐 Starting browser...")
        browser = GrokBrowser(headless=False)  # Keep visible for testing
        await browser.start()
        
        # Step 3: Navigate
        log_info("🔗 Navigating to signup...")
        await browser.navigate_to_signup()
        
        # Step 4: Handle Cloudflare
        log_info("🔐 Handling Cloudflare (60s timeout)...")
        await browser.wait_for_cloudflare(timeout=60)
        
        # Step 5: Fill form
        log_info(f"📝 Filling form...")
        await browser.fill_email_field(temp_email)
        await browser.fill_name_fields(test_account['first_name'], test_account['last_name'])
        await browser.request_verification_code()
        
        # Step 6: Get code
        log_info("📬 Waiting for verification code...")
        verification_code = await check_email_for_code(temp_email)
        
        if not verification_code:
            raise Exception("Failed to get verification code")
        
        log_success(f"✅ Code: {verification_code}")
        
        # Step 7: Submit code
        await browser.submit_verification_code(verification_code)
        
        # Step 8: Set credentials
        log_info("🔑 Setting credentials...")
        await browser.set_account_credentials(
            test_account['email'],
            test_account['password']
        )
        
        # Step 9: Check success
        await asyncio.sleep(3)
        success = await browser.check_signup_success()
        
        if success:
            log_success("✅ BROWSER MODE TEST: PASSED")
            return True
        else:
            log_error("❌ BROWSER MODE TEST: FAILED (validation failed)")
            return False
            
    except Exception as e:
        log_error(f"❌ BROWSER MODE TEST: FAILED - {str(e)}")
        return False
    finally:
        if browser:
            await browser.close()


async def test_api_direct_mode():
    """Test API Direct Mode signup"""
    log_info("\n" + "="*60)
    log_info("🧪 TEST 2: API DIRECT MODE")
    log_info("="*60)
    
    test_account = {
        'email': 'test_api@example.com',
        'password': 'TestPassword456!',
        'first_name': 'API',
        'last_name': 'Test'
    }
    
    try:
        result = await signup_account_api(
            email=test_account['email'],
            password=test_account['password'],
            first_name=test_account['first_name'],
            last_name=test_account['last_name']
        )
        
        if result['status'] == 'success':
            log_success("✅ API DIRECT MODE TEST: PASSED")
            return True
        else:
            error = result.get('error', 'Unknown error')
            if 'Turnstile' in error or 'token' in error.lower():
                log_info(f"⚠️ API DIRECT MODE TEST: EXPECTED FAILURE (Turnstile not implemented)")
                log_info(f"Error: {error}")
                return 'expected_fail'
            else:
                log_error(f"❌ API DIRECT MODE TEST: FAILED - {error}")
                return False
                
    except Exception as e:
        log_error(f"❌ API DIRECT MODE TEST: EXCEPTION - {str(e)}")
        return False


async def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 GROK SIGNUP TOOL - AUTOMATED TESTS")
    print("="*60)
    
    results = {}
    
    # Test 1: Browser Mode
    log_info("\nStarting Browser Mode test...")
    await asyncio.sleep(2)
    results['browser'] = await test_browser_mode()
    
    # Wait between tests
    log_info("\n⏳ Waiting 10s before next test...")
    await asyncio.sleep(10)
    
    # Test 2: API Direct Mode
    log_info("\nStarting API Direct Mode test...")
    await asyncio.sleep(2)
    results['api_direct'] = await test_api_direct_mode()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    browser_status = "✅ PASS" if results['browser'] else "❌ FAIL"
    print(f"Browser Mode:     {browser_status}")
    
    if results['api_direct'] == 'expected_fail':
        api_status = "⚠️ EXPECTED FAIL (Turnstile)"
    elif results['api_direct']:
        api_status = "✅ PASS"
    else:
        api_status = "❌ FAIL"
    print(f"API Direct Mode:  {api_status}")
    
    print("="*60)
    
    # Overall result
    if results['browser'] and (results['api_direct'] == 'expected_fail' or results['api_direct']):
        print("\n🎉 Overall: TESTS PASSED (Browser Mode working as expected)")
        return 0
    else:
        print("\n❌ Overall: TESTS FAILED")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(run_tests())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
