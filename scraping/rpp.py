from helpers import fetchWebsite


class RPPScraping:
    def __init__(self):
        self.base_url = "https://rpp.pe"
        # self.news_url = "https://rpp.pe/tecnologia/moviles"
        self.news_url = "https://rpp.pe/noticias/lluvias"
        self.html_body = None
        self.articles = []
        self.limit = 5

    def getHtmlBody(self):
        try:
            self.html_body = fetchWebsite(self.news_url)
        except Exception as e:
            print(f"getHTMLBody -> {e}")

    def getArticles(self):
        if self.html_body:
            self.articles = self.html_body.find_all(
                "article",
                {"class": "news news--summary-onlydesktop news--summary-standard"},
            )[: self.limit]

    def getDataFromArticles(self):
        if len(self.articles):
            data = []
            for article in self.articles:
                # location = article.find("h3").get_text()
                title = article.find("h2").find("a")
                url = title.get("href")
                image = self.getInternalDataFromArticles(url)
                autor_span = article.find("span", class_="news__author")
                autor = (
                    autor_span.get_text().strip() if autor_span else "Unknown Author"
                )
                published_at = article.find("time", {"class": "x-ago"}).get("data-x")

                data.append(
                    {
                        "title": title.get_text().strip(),
                        "autor": autor,
                        "url": url,
                        "image": image,
                        "published_at": published_at,
                    }
                )

            return data

    def getInternalDataFromArticles(self, article_url):
        image = ""

        try:
            internal_data = fetchWebsite(article_url)
            media_content = internal_data.find("div", class_="media__content")
            image = media_content.find("img").get("src")

        except Exception as e:
            print(f"getInternalDataFromArticles -> {e}")

        return image
