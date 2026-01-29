## Usage
Get data from novel updates website 

Example:
```python
from Search import Search
from Book import Book
from genre_constants import *

search=Search(included_genres=[GENRES["GENRE_COMEDY"]])
titles=search.get_titles(5)
Book.make_book(titles[0])
```