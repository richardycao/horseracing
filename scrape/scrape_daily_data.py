# https://medium.com/swlh/introduction-to-selenium-create-a-web-bot-with-python-cd59a741fdae

"""
TODO:
convert html to csv and save that instead
test all get_x()
use webdriver wait instead of time.sleep() https://stackoverflow.com/questions/56119289/element-not-interactable-selenium
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

import os
from datetime import date

import config

def safe_find(browser, by, value, num_results, retries=1, delay=2):
    for r in range(retries + 1):
        time.sleep(delay)
        elements = browser.find_elements(by=by, value=value)
        
        if len(elements) > 0:
            if num_results:
                return elements[:num_results]
            return elements
        print("Retrying for value", value)
    return None

def login(browser):
    browser.find_element(by=By.CLASS_NAME, value='tvg-btn-secondary-alt-1lkym').click()

    fields = browser.find_elements(by=By.CLASS_NAME, value='styled-components-sc-vsf6p0-0')
    fields[0].send_keys(config.USERNAME)
    fields[1].send_keys(config.PASSWORD)
    browser.find_element(by=By.ID, value='stateSelector').send_keys(config.STATE)
    browser.find_element(by=By.CLASS_NAME, value='default-styled-sc-1xv0x-0.RJxHr.styled-components__ButtonComp-sc-a6y9jp-0.iPDLvC').click()

def setup():
    today = date.today()
    date_string = today.strftime("%Y-%m-%d")
    date_path = f'./results/{date_string}'
    if not os.path.exists(date_path):
        os.makedirs(date_path)
    
    options = Options()
    # Add all these params to bypass bot detection: https://stackoverflow.com/questions/53039551/selenium-webdriver-modifying-navigator-webdriver-flag-to-prevent-selenium-detec
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    browser.get("https://www.tvg.com/results")

    # Refresh the page to bypass the promotion popup
    browser.refresh()

    # login(browser) # uncomment later
    
    return browser, date_path

def check_and_close_login_popup(browser):
    login_headers = browser.find_elements(by=By.CLASS_NAME, value='styled-components__TitleAtom-sc-1njzr4m-0.styled-components-sc-1njzr4m-1.styled-components__Title-sc-12hkef7-5.ZkNAE.cjGtIh.eOcmRs')
    if len(login_headers) > 0:
        browser.find_element(by=By.CLASS_NAME, value='default-styled-sc-1xv0x-0.RJxHr.styled-components__HeaderButton-sc-12hkef7-2.joFbFy').click()

# Doesn't work yet
def get_details(browser, race_path):
    details = safe_find(browser, By.CLASS_NAME, 'pp-header_row.pp-header_race-details', num_results=1, retries=1)
    if not details:
        print('Error finding details. Skipping this section for path:', race_path)
        return

    with open(f'{race_path}/details.txt', 'w') as f:
        f.write(details[0].get_attribute('innerHTML'))

def get_results(browser, race_path):
    results = safe_find(browser, By.CLASS_NAME, 'table.race-results.no-margin', num_results=1, retries=1)
    if not results:
        print('Error finding results. Skipping this section for path:', race_path)
        return

    with open(f'{race_path}/results.txt', 'w') as f:
        f.write(results[0].get_attribute('innerHTML'))

def get_race_card(browser, race_path):
    tabs = ['Summary', 'Snapshot', 'Speed & Class', 'Pace', 'Jockey/Trainer Stats']

    for t in tabs:
        tabs = safe_find(browser, By.LINK_TEXT, t, num_results=1, retries=1)
        if not tabs:
            print(f'Error finding element tab {t}. Skipping this section for path:', race_path)
            return

        tables = safe_find(browser, By.CLASS_NAME, 'race-handicapping-results', num_results=1, retries=1)
        if not tables:
            print(f'Error finding data for tab {t}. Skipping this section for path:', race_path)
            return
        
        with open(f'{race_path}/{t[:4].lower()}.txt', 'w') as f:
            f.write(tables[0].get_attribute('innerHTML'))

def get_probables(browser, race_path):
    probables = safe_find(browser, By.CLASS_NAME, 'scroll-x', num_results=1, retries=1)
    if not probables:
        print('Error finding probables. Skipping this section for path:', race_path)
        return

    with open(f'{race_path}/probables.txt', 'w') as f:
        f.write(probables[0].get_attribute('innerHTML'))

def get_willpays(browser, race_path):
    willpays = safe_find(browser, By.CLASS_NAME, 'result-runners-table', num_results=1, retries=1)
    if not willpays:
        print('Error finding willpays. Skipping this section for path:', race_path)
        return

    with open(f'{race_path}/willpays.txt', 'w') as f:
        f.write(willpays[0].get_attribute('innerHTML'))

def get_pools(browser, race_path):
    pools = safe_find(browser, By.CLASS_NAME, 'result-runners-table.pools-table', num_results=1, retries=1)
    if not pools:
        print('Error finding pools. Skipping this section for path:', race_path)
        return

    with open(f'{race_path}/pools.txt', 'w') as f:
        f.write(pools[0].get_attribute('innerHTML'))    

def get_race(browser, race_path):
    # get_details(browser, race_path)
    get_results(browser, race_path)
    return
    get_race_card(browser, race_path)
    get_probables(browser, race_path)
    get_willpays(browser, race_path)
    get_pools(browser, race_path)

def get_page(browser, date_path, page_idx):
    items = safe_find(browser, By.CLASS_NAME, 'replay-list__item', num_results=None, retries=3)
    if not items:
        print(f'Error finding results on page {page_idx}. Skipping to the next page.')
        return
    
    item_idx = 0
    while item_idx < 1:#len(items):
        race_path = f'{date_path}/race_{page_idx}_{item_idx}'
        if not os.path.exists(race_path):
            os.makedirs(race_path)
        
        buttons = safe_find(browser, By.LINK_TEXT, 'Go to Program Page', num_results=1, retries=1)
        if buttons:
            buttons[0].click()
            get_race(browser, race_path)
            browser.back()
        else:
            print('Error finding button to program page. Skipping race #' + str(item_idx))
        
        item_idx += 1

        new_items = safe_find(browser, By.CLASS_NAME, 'replay-list__item', num_results=None, retries=3)
        if not new_items:
            print('Error find results when returning to results page.')
            break

        if item_idx < len(new_items):
            time.sleep(2)
            new_items[item_idx].click()
        else:
            break

def main():
    browser, date_path = setup()
    # 15 seconds for bot check
    # time.sleep(20) # uncomment later
    page_idx = 0
    
    has_next = True
    while has_next:
        # get_page(browser, date_path, page_idx) # uncomment later
        page_idx += 1

        next_pages = safe_find(browser, By.CSS_SELECTOR, "a[ng-click='selectPage(page + 1, $event)']:not([disabled='disabled'])", num_results=1, retries=1) # https://devqa.io/selenium-css-selectors/
        if not next_pages:
            print(f'Cannot find next page ({page_idx}). Exiting...')
            has_next = False
            return
        next_pages[0].click()

    browser.close()

if __name__ == '__main__':
    main()
