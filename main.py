from scraping.rpp import RPPScraping
from json import dumps

scraping = RPPScraping()
scraping.getHtmlBody()
scraping.getArticles()
articles = scraping.getDataFromArticles()

print(dumps(articles, indent=2, ensure_ascii=False))
