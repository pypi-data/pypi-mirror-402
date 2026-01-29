import nodriver as uc
import asyncio
from .constants import BASE_URL
import time
import random

async def get_cf_clearance(url):
    
    browser = await uc.start(
        headless=True,
        browser_args=[
            '--disable-blink-features=AutomationControlled',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
        ]
        )
    page = await browser.get(url)
    
    ua = await page.evaluate("navigator.userAgent")
    ua=ua.replace("HeadlessChrome","Chrome")
    cookies = await browser.cookies.get_all()
    
    cf_clearance = None
    for cookie in cookies:
        if cookie.name == "cf_clearance":
            cf_clearance = cookie.value
            break
    
    browser.stop()
    return cf_clearance,ua
