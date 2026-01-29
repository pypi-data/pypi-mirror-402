import string
import unicodedata

def slugify(title:str):
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('utf-8')
    title = title.lower()
    title = title.translate(str.maketrans("","",string.punctuation))
    title = title.replace(" ","-")
    return title

