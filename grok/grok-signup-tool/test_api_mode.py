"""
Test API Direct Mode
Simple test to see if API mode works
"""

import asyncio
import random
from utils.logger import log_info, log_success, log_error, log_warning
from utils.api_direct import signup_account_api

async def test_api_mode():
    """Test API Direct signup"""
    print("\n" + "="*60)
    print("🧪 API DIRECT MODE TEST")
    print("="*60)
    
    # Random test account
    email = f'api_test_{random.randint(1000,9999)}@example.com'
    password = f'ApiPass{random.randint(100,999)}!'
    first_name = random.choice(['API', 'Direct', 'Fast'])
    last_name = random.choice(['Test', 'Mode', 'User'])
    
    log_info(f"📧 Account: {email}")
    log_info(f"🔑 Password: {password}")
    log_info(f"👤 Name: {first_name} {last_name}")
    
    try:
        log_info("\n📡 Starting API Direct signup...")
        log_warning("⚠️ Expected: Will fail due to Turnstile token not implemented")
        
        result = await signup_account_api(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        print("\n" + "="*60)
        print("📊 RESULT:")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Email: {result.get('email', 'N/A')}")
        
        if result['status'] == 'success':
            log_success("✅ TEST PASSED - Account created!")
            print(f"Temp Email: {result.get('temp_email')}")
            print(f"Code: {result.get('verification_code')}")
        else:
            error = result.get('error', 'Unknown')
            print(f"Error: {error}")
            
            if 'Turnstile' in error or 'token' in error.lower():
                log_warning("\n⚠️ EXPECTED FAILURE: Turnstile token not implemented")
                log_info("This is normal - API mode needs Turnstile solver")
                log_info("Recommendation: Use Browser Mode instead")
                return 'expected_fail'
            else:
                log_error("\n❌ UNEXPECTED FAILURE")
                return False
        
    except Exception as e:
        log_error(f"\n❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_api_mode())
        
        print("\n" + "="*60)
        if result == 'expected_fail':
            print("✅ Test completed - Expected failure (Turnstile)")
            print("👉 Use Browser Mode for production")
        elif result:
            print("🎉 Test PASSED")
        else:
            print("❌ Test FAILED")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Test stopped")
