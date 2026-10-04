from tools import crossref, openalex, web_search

COLLECTIONS = {
    "web": ("Web (DuckDuckGo)", web_search.search),
    "openalex": ("Scholarly works (OpenAlex)", openalex.search),
    "crossref": ("Publication records (Crossref)", crossref.search),
}
