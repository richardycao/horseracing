# https://medium.com/swlh/introduction-to-selenium-create-a-web-bot-with-python-cd59a741fdae

"""
TODO:
parallelize by opening multiple tabs at once.
use webdriver wait instead of time.sleep() https://stackoverflow.com/questions/56119289/element-not-interactable-selenium
"""

from tkinter import N
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

import os
from datetime import date

import utils
import program

def setup():
    today = date.today()
    date_string = today.strftime("%Y-%m-%d")
    date_path = f'./results/{date_string}'
    if not os.path.exists(date_path):
        os.makedirs(date_path)
    
    options = Options()
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    browser.get("https://www.tvg.com/results")
    browser.refresh()
    
    return browser, date_path

def get_race_path(browser, item_idx):
    info = utils.safe_find(browser, By.CLASS_NAME, 'replay-list__item-line', num_results=None, retries=1)
    if not info:
        print('Error finding info row of race. Skipping race #' + str(item_idx))
        return False
    html = info[item_idx].get_attribute('innerHTML')
    dt = utils.find_value_in_html(html, left='<span class="replay-list__cell col-date" qa-label="raceReplay-date">', right='</span>')
    track = utils.find_value_in_html(html, left='<span ng-if="HandicappingRaceReplays.events.showTrackColumn\(\)" class="replay-list__cell col-track" qa-label="raceReplay-track".{0,10}>', right='</span>')
    racenum = utils.find_value_in_html(html, left='<span class="replay-list__cell col-race__number" qa-label="raceReplay-raceNumber">', right='</span>')

    rp = '_'.join([_ for _ in reversed(dt[0].split(' ')[1:])]) + '_' + track[0].replace(' ', '_') + '_' + racenum[0]
    return rp



class ProgramReader():
    def __init__(self):
        self.start_time = time.time()

    """
    checks if the page has loaded. if not and the page's age exceeds 10 seconds,
    kill it and log an error.
    """
    def is_ready(self):

        return False

    def age(self):
        return time.time() - self.start_time()
    
    """
    saves the html to a file.
    """
    def get_program(self):
        return ""

# I want to get all results on every page in 1 nested loop. this will let the program readers
# exist independent of which page I'm currently on.

"""
I want to open the tabs all at once, then just go to a new url each time, instead of closing the
tab every time I'm done with it.
"""
class Coordinator:
    def __init__(self, num_workers=3):
        self.driver, self.date_path = self.setup()
        self.actions = ActionChains(self.driver)

        self.num_workers = num_workers
        self.worker_idx = 0
        self.workers = [None for i in range(num_workers)]
        self.active_workers = 0

        self.page_idx, self.row_idx = 0, 0

        self.is_start = True
        self.end_of_results = False

    def setup(self):
        today = date.today()
        date_string = today.strftime("%Y-%m-%d")
        date_path = f'./results/{date_string}'
        if not os.path.exists(date_path):
            os.makedirs(date_path)
        
        options = Options()
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        results_url = "https://www.tvg.com/results"
        driver.get(results_url)
        for _ in range(self.num_workers):
            self.driver.execute_script(f"window.open('{results_url}');")
        
        driver.refresh()
        
        return driver, date_path

    def get_rows_on_current_page(self):
        rows = utils.safe_find(self.driver, By.CLASS_NAME, 'replay-list__item-line', num_results=None, retries=3)
        if not rows:
            print(f'Error finding results on page {self.page_idx + 1}. Skipping to the next page.')
            return False
        return rows

    def click_row(self, rows):
        self.actions.move_to_element(rows[self.row_idx]).perform()
        rows[self.row_idx].click()

    def click_next_page(self, page_idx):
        next_pages = utils.safe_find(self.driver, By.CSS_SELECTOR, "a[ng-click='selectPage(page + 1, $event)']:not([disabled='disabled'])", num_results=1, retries=1) # https://devqa.io/selenium-css-selectors/
        if not next_pages:
            print(f'Cannot find next page ({page_idx + 1}). End of results.')
            return False
        next_pages[0].click()
        return True

    def switch_tab(self, idx):
        self.driver.switch_to.window(self.driver.window_handles[idx])

    def run(self):
        # I should be cycling through workers. the results are the "background".

        """
        The problem is checking whether a webpage is done loading. sometimes webpages
        will keep polling for stuff.

        The easier way is to do batch loads. Choose a batch size, e.g. 10.
        Open 10 tabs at once, then load them sequentially. Usually the tabs will finish loading
        very closely in time. In the end it looks like: wait 8 seconds for the first tab to load,
        get the data in the first tab, go to second tab, it should be loaded or close to loaded, get
        data for second tab, etc.
        """

        # save the list of rows on the page here.
        rows = self.get_rows_on_current_page()

        while self.active_workers > 0 or is_start:
            is_start = False

            # If a worker is occupied
            worker = self.workers[self.worker_idx]
            if worker != None:
                self.switch_tab(self.worker_idx + 1)
                # If the worker is ready, get the program info
                if : # TODO: if a certain component can be found on the page,
                    program.get_race(self.driver, )
                    self.workers[self.worker_idx] = None
                    self.active_workers -= 1
                # If the worker is not ready, kill it if it's older than 10 seconds.
                elif worker.age() > 10:
                    self.workers[self.worker_idx] = None
                    self.active_workers -= 1

            # If a worker is available and there are more results left,
            if not self.workers[self.worker_idx] and not self.end_of_results:
                # Try to get the next row
                self.row_idx += 1
                if self.row_idx > len(rows):
                    self.page_idx += 1
                    self.row_idx = 0
                    
                    self.switch_tab(0)
                    if not self.click_next_page():
                        self.end_of_results = True
                    rows = self.get_rows_on_current_page()
                    if not rows:
                        self.end_of_results = True
                    
                # If the next row exists,
                if not self.end_of_results:
                    # Click the new row
                    self.click_row(rows)

                    # Open program in worker[worker_idx]
                    buttons = utils.safe_find(self.driver, By.CLASS_NAME, 'bt-button.bt-tertiary.bt-program-page-redirect', num_results=1)
                    if buttons:
                        btn_html = buttons[0].get_attribute('outerHTML')
                        btn_path = utils.find_value_in_html(btn_html, left='href="', right='" ng-click', width=100)
                        btn_url = f'https://www.tvg.com{btn_path[0]}'
                        self.driver.get(btn_url)
                    else:
                        print(f'Error finding button to program page. Skipping race on page {self.page_idx}, row {self.row_idx}.')

                    self.workers[self.worker_idx] = ProgramReader()
            
            self.worker_idx = (self.worker_idx + 1) % self.num_workers

            # if workers[worker_idx] is inactive (None)
                # if is_end == False
                    # row_idx += 1
                    # if row_idx > number of rows on the page, go to the next page, page_idx += 1, row_idx = 0
                    # check if the row exists.
                    # if the row exists, add a worker (ProgramReader) for it. increment active_workers.
                    # if it doesn't exist, set is_end = True. decrement active_workers.
                # cycle to the next worker

                    

            
            # if (not elif) workers[worker_idx] is active (ProgramReader), then check if it's ready
                # if it's ready, get the program.
                # if not, check if the worker is older than 10 seconds. If so, kill it. Otherwise,
                #     cycle to the next worker.






def main():
    browser, date_path = setup()
    time.sleep(20) # 20 seconds to log in before script starts.
    page_idx = 0
    
    has_next = True
    while has_next:
        get_page(browser, date_path, page_idx)
        page_idx += 1

        next_pages = utils.safe_find(browser, By.CSS_SELECTOR, "a[ng-click='selectPage(page + 1, $event)']:not([disabled='disabled'])", num_results=1, retries=1) # https://devqa.io/selenium-css-selectors/
        if not next_pages:
            print(f'Cannot find next page ({page_idx}). Exiting...')
            has_next = False
            return
        next_pages[0].click()
        new_items = utils.safe_find(browser, By.CLASS_NAME, 'replay-list__item-line', num_results=None, retries=3)
        if not new_items:
            print('Error find results when returning to results page. Stopping now.')
            break
        actions = ActionChains(browser)
        actions.move_to_element(new_items[0]).perform()
        new_items[0].click()

    browser.close()

if __name__ == '__main__':
    main()
