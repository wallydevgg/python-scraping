from requests import get
from bs4 import BeautifulSoup


class RPPScraping:
    def __init__(self):
        self.base_url = "https://rpp.pe"
        # self.news_url = "https://rpp.pe/tecnologia/moviles"
        self.news_url = "https://rpp.pe/noticias/lluvias"
        self.html_body = None
        self.articles = []

    def getHtmlBody(self):
        try:
            response = get(self.news_url)
            status_code = response.status_code
            if status_code == 200:
                self.html_body = BeautifulSoup(response.content, "html.parser")

        except Exception as e:
            print(f"getHTMLBody -> {e}")

    def getArticles(self):
        if self.html_body:
            self.articles = self.html_body.find_all(
                "article",
                {"class": "news news--summary-onlydesktop news--summary-standard"},
            )

    def getDataFromArticles(self):
        if len(self.articles):
            data = []
            for article in self.articles:
                # location = article.find("h3").get_text()
                title = article.find("h2").find("a")
                url = title.get("href")
                redactor = article.find("span").get_text().strip()
                # fecha = article.find("time").get_text()
                data.append(
                    {
                        "title": title.get_text().strip(),
                        "redactor": redactor,
                        "url": url,
                        # "fecha": fecha,
                    }
                )
            return data
