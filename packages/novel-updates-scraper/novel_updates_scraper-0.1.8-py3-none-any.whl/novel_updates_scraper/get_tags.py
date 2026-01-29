from .scraper import get_html
from .utils import slugify

html=get_html("https://www.novelupdates.com/series-finder/?sf=1&sort=sdate&order=desc")

options=html.find("select",id="tags_include").find_all("option")
with open("tag_constants.py", "w", encoding="utf-8") as f:
    f.write("TAGS={")
    for o in options:
        f.write(f'"TAG_{slugify(o.text).upper().replace("-","_")}":"{o["value"]}",\n')
    f.write("}")