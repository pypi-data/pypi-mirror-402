import string
import unicodedata

def slugify(title:str):
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('utf-8')
    title = title.lower()
    title = title.replace("(wn)","")
    title = title.replace("sui**de","suicide")
    title = title.replace("m*rder","murder")
    title = title.replace("-"," ")
    title = title.translate(str.maketrans("","",string.punctuation))
    title = title.replace(" ","-")
    return title

