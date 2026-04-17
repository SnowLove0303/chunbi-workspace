import asyncio
from playwright.async_api import async_playwright

async def create_version():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = await browser.new_page()
        
        await page.goto("https://open.feishu.cn/app/cli_a95620cbb8399cdd/version/create")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        
        # Fill version number
        version_input = page.locator('input[placeholder*="version"]')
        await version_input.click()
        await version_input.fill("1.0.0")
        
        # Fill update notes
        textarea = page.locator('textarea')
        await textarea.click()
        await textarea.fill("Initial release with bot functionality and message event subscription")
        
        # Check values
        version_val = await version_input.input_value()
        notes_val = await textarea.input_value()
        print(f"Version: {version_val}")
        print(f"Notes: {notes_val}")
        
        # Click Save
        save_btn = page.locator('button:has-text("Save")')
        await save_btn.click()
        await asyncio.sleep(3)
        
        print(f"Final URL: {page.url}")
        await browser.close()

asyncio.run(create_version())
