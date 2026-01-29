from .scraper import get_html
from .utils import slugify

html=get_html("https://www.novelupdates.com/series-finder/?sf=1&sort=sdate&order=desc")

options=html.find_all("a",class_="genreme")
with open("genre_constants.py", "w", encoding="utf-8") as f:
    f.write("GENRES={")
    for o in options:
        f.write(f'"GENRE_{slugify(o.text).upper().replace("-","_")}":"{o["genreid"]}",\n')
    f.write("}")