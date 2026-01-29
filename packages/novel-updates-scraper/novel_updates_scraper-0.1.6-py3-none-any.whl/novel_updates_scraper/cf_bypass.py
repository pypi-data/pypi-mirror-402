import nodriver as uc
import asyncio
from .constants import BASE_URL

async def get_cf_clearance(url):
    """Extract cf_clearance using Nodriver stealth browser."""
    
    browser = await uc.start(headless=True)
    page = await browser.get(url)
    
    
    ua = await page.evaluate("navigator.userAgent")
    cookies = await browser.cookies.get_all()
    
    cf_clearance = None
    for cookie in cookies:
        if cookie.name == "cf_clearance":
            cf_clearance = cookie.value
            break
    
    browser.stop()
    return cf_clearance,ua

