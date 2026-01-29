from curl_cffi import requests
from bs4 import BeautifulSoup
from .constants import BASE_URL
import asyncio
from .cf_bypass import get_cf_clearance
import time
import random

session = {
    "token": None,
    "user_agent": None
}

session_client = requests.Session(impersonate="chrome")

async def refresh_cf_token():
    session["token"],session["user_agent"]=await get_cf_clearance(BASE_URL)



def get_html(url,query_params={}):
    print(url)
    for i in range(5):
        time.sleep(random.uniform(1.5, 4.0))
        headers={
            "User-Agent":session["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        print(session["user_agent"])
        res = session_client.get(
            url,
            headers=headers,
            cookies={"cf_clearance":session["token"]},
            params=query_params
        )
        print(res.status_code)
        if res.status_code!=200:
            asyncio.run(refresh_cf_token())
        else:  
            break

    soup = BeautifulSoup(res.content, 'html.parser')
    return soup


