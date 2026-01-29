from curl_cffi import requests
from bs4 import BeautifulSoup
from .constants import BASE_URL
import asyncio
from .cf_bypass import get_cf_clearance

session = {
    "token": None,
    "user_agent": None
}

async def refresh_cf_token():
    session["token"],session["user_agent"]=await get_cf_clearance(BASE_URL)

def get_html(url,query_params={}):
    
    for i in range(5):
        headers={
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        res = requests.get(
            url,
            headers=headers,
            cookies={"cf_clearance":session["token"]},
            impersonate="chrome",
            params=query_params
        )
        if res.status_code!=403:
            break
        else:  
            asyncio.run(refresh_cf_token())

    soup = BeautifulSoup(res.content, 'html.parser')
    return soup


