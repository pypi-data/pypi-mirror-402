from .scraper import get_html
from .query_constants import *
from .tag_constants import *
from .constants import BASE_URL

class Search():

    def __init__(self,
    query_word=None,
    novel_types=[],
    languages=[],
    num_chapters=None, # int
    num_chapters_search_type=MIN_SEARCH, # search type
    release_frequency=None, # int
    release_frequency_search_type=MAX_SEARCH,# search type
    num_reviews=None, # int
    num_reviews_search_type=MIN_SEARCH,# search type
    rating=None, # int
    rating_search_type=MIN_SEARCH,# search type
    num_rating=None, # int
    num_rating_search_type=MIN_SEARCH,# search type
    num_readers=None, # int
    num_readers_search_type=MIN_SEARCH,# search type
    first_release_date=None,
    first_release_date_search_type=MIN_SEARCH,# search type
    last_release_date=None,
    last_release_date_search_type=MIN_SEARCH,# search type
    included_genres=[],
    excluded_genres=[],
    genres_search_type=AND_SEARCH, # search type
    included_tags=[],
    excluded_tags=[],
    tags_search_type=OR_SEARCH,
    story_status=None,
    sort=SORT_LAST_UPDATED,
    sort_type=SORT_DESCENDING,
    ):
        self.query_word=query_word
        self.novel_types=novel_types
        self.languages=languages

        self.num_chapters=num_chapters
        self.num_chapters_search_type=num_chapters_search_type

        self.release_frequency=release_frequency
        self.release_frequency_search_type=release_frequency_search_type

        self.num_reviews = num_reviews
        self.num_reviews_search_type = num_reviews_search_type

        self.rating=rating
        self.rating_search_type=rating_search_type

        self.num_rating=num_rating
        self.num_rating_search_type=num_rating_search_type

        self.num_readers=num_readers
        self.num_readers_search_type=num_readers_search_type

        self.first_release_date=first_release_date
        self.first_release_date_search_type=first_release_date_search_type

        self.last_release_date=last_release_date
        self.last_release_date_search_type=last_release_date_search_type

        self.included_genres=included_genres
        self.excluded_genres=excluded_genres
        self.genres_search_type=genres_search_type

        self.included_tags=included_tags
        self.excluded_tags=excluded_tags
        self.tags_search_type=tags_search_type

        self.story_status=story_status

        self.sort=sort
        self.sort_type=sort_type
    
    def _get_language_query(self):
        return ",".join(self.languages)
    
    def _get_novel_type_query(self):
        return ",".join(self.novel_types)

    def _get_first_release_date_query(self):
        return self.first_release_date.strftime("%m/%d/%Y") if self.first_release_date else None

    def _get_last_release_date_query(self):
        return self.last_release_date.strftime("%m/%d/%Y") if self.last_release_date else None

    def _get_included_genres_query(self):
        return ",".join(self.included_genres)

    def _get_excluded_genres_query(self):
        return ",".join(self.excluded_genres)

    def _get_included_tags_query(self):
        return ",".join(self.included_tags)

    def _get_excluded_tags_query(self):
        return ",".join(self.excluded_tags)

    def get_query_params(self):
        params= {
            "sf":1,
            "nt":self._get_novel_type_query(),
            "org":self._get_language_query(),

            "rl":self.num_chapters,
            "mrl":self.num_chapters_search_type if self.num_chapters else None,

            "rf":self.release_frequency,
            "mrf":self.release_frequency_search_type if self.release_frequency else None,

            "rvc":self.num_reviews,
            "mrvc":self.num_reviews_search_type if self.num_reviews else None,

            "rt":self.rating,
            "mrt":self.rating_search_type if self.rating else None,

            "rtc":self.num_rating,
            "mrtc":self.num_rating_search_type if self.num_rating else None,

            "rct": self.num_readers,
            "mrct": self.num_readers_search_type if self.num_readers else None,

            "dtf": self._get_first_release_date_query(),
            "mdtf": self.first_release_date_search_type if self.first_release_date else None,

            "dt": self._get_last_release_date_query(),
            "mdt": self.last_release_date_search_type if self.last_release_date else None,
            

            "gi":self._get_included_genres_query(),
            "ge":self._get_excluded_genres_query(),
            "mgi":self.genres_search_type if self.included_genres or self.excluded_genres else None,

            "tgi":self._get_included_tags_query(),
            "tge":self._get_excluded_tags_query(),
            "mtgi":self.tags_search_type if self.included_tags or self.excluded_tags else None,

            "sort":self.sort,
            "order":self.sort_type,

            "sh":self.query_word,
        }
            

        return {k:v for k,v in params.items() if v}

    def fetch_html(self):
        url=f"{BASE_URL}series-finder"
        query_params=self.get_query_params()
        html= get_html(url,query_params)
        return html
    
    def get_titles(self, numberOfTitles=5):
        html=self.fetch_html()
        titles=[a.find("a").text for a in html.find_all('div',class_="search_title")][:numberOfTitles]
        return titles
