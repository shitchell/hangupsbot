from hangupsbot.utils import replace_entities, remove_tags

import requests
import urllib.parse
from . import api_key

class SearchResult:
    def __init__(self, result):
        if 'link' in result.keys():
            self._from_api(result)
        else:
            self._from_dep(result)
    
    def _from_api(self, result):
        self.url = result['link']
        self.title = result['title']
        self.snippet = result['snippet']
    
    def _from_dep(self, result):
        self.title = replace_entities(result['titleNoFormatting'])
        self.snippet = result['content'].replace('\n', '')
        self.snippet = remove_tags(self.snippet)
        self.snippet = replace_entities(self.snippet)
        self.url = result['url']

def web_search(query):
    url = 'https://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=' + urllib.parse.quote(query)
    req = requests.get(url)
    resp = req.json()
    
    return [SearchResult(x) for x in resp['responseData']['results']]

def image_search(query):
    url = 'https://www.googleapis.com/customsearch/v1?key={}&cx=008423659245751881210:lyuoakwwzh8&searchType=image&fields=items(link,title,snippet)&q={}'.format(api_key, urllib.parse.quote(query))
    req = requests.get(url)
    resp = req.json()
    
    return [SearchResult(x) for x in resp['items']]