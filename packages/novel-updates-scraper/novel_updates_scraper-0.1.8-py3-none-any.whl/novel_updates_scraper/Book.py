from .scraper import get_html
from .utils import slugify
from .constants import BASE_URL

class Book():

    def __init__(self,title,genres,tags,rating,num_ratings):
        self.title=title
        self.genres=genres
        self.tags=tags
        self.rating=rating
        self.num_ratings=num_ratings
        self.url=f"{BASE_URL}series/{slugify(title)}/"
    
    @staticmethod
    def _get_book_html(title):
        url = f"{BASE_URL}series/{slugify(title)}/"
        return get_html(url)

    @staticmethod
    def _parse_list_html(container_html):
        text_list=[a.text for a in container_html.find_all('a')]
        return text_list

    @staticmethod
    def make_book(title):
        html=Book._get_book_html(title)
        tags=Book._parse_list_html(html.find('div',id="showtags"))
        genres=Book._parse_list_html(html.find('div',id="seriesgenre"))

        rating_text=html.find("span",class_="uvotes").text
        rating=float(rating_text[1:4])
        num_ratings=int(rating_text[12:-7])

        return Book(title, genres,tags, rating,num_ratings)

    def __str__(self):
        return self.title
