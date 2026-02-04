"""
Simple debug test - just open browser and check what's on the page
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_page():
    """Debug what's actually on the page"""
    async with async_playwright() as p:
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        print("🔗 Navigating to https://accounts.x.ai/sign-up...")
        await page.goto('https://accounts.x.ai/sign-up')
        
        print("⏳ Waiting 10s for page to load...")
        await asyncio.sleep(10)
        
        # Get page title and URL
        title = await page.title()
        url = page.url
        print(f"\n📄 Page Title: {title}")
        print(f"🔗 Current URL: {url}")
        
        # Get all input elements
        print("\n🔍 Finding all input elements...")
        inputs = await page.query_selector_all('input')
        print(f"Found {len(inputs)} input elements:")
        for i, inp in enumerate(inputs, 1):
            input_type = await inp.get_attribute('type')
            input_name = await inp.get_attribute('name')
            input_id = await inp.get_attribute('id')
            input_placeholder = await inp.get_attribute('placeholder')
            print(f"  {i}. type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}")
        
        # Get all buttons
        print("\n🔘 Finding all buttons...")
        buttons = await page.query_selector_all('button')
        print(f"Found {len(buttons)} button elements:")
        for i, btn in enumerate(buttons, 1):
            btn_text = await btn.inner_text()
            btn_type = await btn.get_attribute('type')
            print(f"  {i}. text='{btn_text}', type={btn_type}")
        
        # Check for Cloudflare
        content = await page.content()
        has_cloudflare = 'cloudflare' in content.lower()
        print(f"\n🔐 Cloudflare detected: {has_cloudflare}")
        
        # Take screenshot
        await page.screenshot(path='output/logs/debug_screenshot.png')
        print("\n📸 Screenshot saved to output/logs/debug_screenshot.png")
        
        print("\n⏸️ Browser will stay open for 30s for manual inspection...")
        await asyncio.sleep(30)
        
        await browser.close()
        print("✅ Debug complete!")

if __name__ == "__main__":
    asyncio.run(debug_page())
