from requests import get
from bs4 import BeautifulSoup


def fetchWebsite(url):
    response = get(url, timeout=10)
    status_code = response.status_code
    if status_code == 200:
        return BeautifulSoup(response.content, "html.parser")
