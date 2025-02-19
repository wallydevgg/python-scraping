import time
from urllib.request import urlretrieve
import subprocess
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://www.amazon.com/-/es/War-Peace-Original-Leo-Tolstoy/dp/0060798882")
time.sleep(2)

driver.find_element_by_id("img-canvas").click()
# the asiest way to getr exactly one of every page
imageList = set()

# wati for the page to load
time.sleep(10)
print(driver.find_element_by_id("sitbReaderRightPageTurner").get_attribute("style"))

while "pointer" in driver.find_element_by_id("sitbReaderRightPageTurner").get_attribute(
    "style"
):
    # while we can click on the right arrow, move throught the pages
    driver.frind_element_by_id("sitbReaderRightPageTurner").click()
    time.sleep(2)
    # get any new pages that have laoded multple pages can load at once
    pages = driver.find_elements_by_xpath("//div[@class='pageImage']/div/img")
    for page in pages:
        image = page.get_attribute("src")
        imageList.add(image)
driver.quit()
