from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time

driver = webdriver.Chrome(ChromeDriverManager().install())
driver.get("https://www.tvg.com/races")

time.sleep(5) # wait for the html to load

with open("./live_output.txt", "w") as f:
    f.write(driver.page_source)

driver.close()
