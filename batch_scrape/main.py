"""
Batch scrape doesn't work any better than normal scrape. It takes forever to load each webpage.
"""

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

class Coordinator:
    def __init__(self, batch_size=10):
        self.driver, self.date_path = self.setup()
        self.actions = ActionChains(self.driver)

        self.page_idx, self.row_idx = 0, 0
        self.batch_size = batch_size

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
        driver.get("https://www.tvg.com/results")
        
        driver.refresh()
        
        return driver, date_path

    def get_rows_on_current_page(self):
        rows = utils.safe_find(self.driver, By.CLASS_NAME, 'replay-list__item-line', num_results=None, retries=3)
        if not rows:
            print(f'Error finding results on page {self.page_idx + 1}. Skipping to the next page.')
            return False
        return rows

    def get_race_path(self, row_idx):
        info = utils.safe_find(self.driver, By.CLASS_NAME, 'replay-list__item-line', num_results=None)
        if not info:
            print('Error finding info row of race. Skipping race #' + str(row_idx))
            return ''
        html = info[row_idx].get_attribute('innerHTML')
        dt = utils.find_value_in_html(html, left='<span class="replay-list__cell col-date" qa-label="raceReplay-date">', right='</span>')
        track = utils.find_value_in_html(html, left='<span ng-if="HandicappingRaceReplays.events.showTrackColumn\(\)" class="replay-list__cell col-track" qa-label="raceReplay-track".{0,10}>', right='</span>')
        racenum = utils.find_value_in_html(html, left='<span class="replay-list__cell col-race__number" qa-label="raceReplay-raceNumber">', right='</span>')

        rp = '_'.join([_ for _ in reversed(dt[0].split(' ')[1:])]) + '_' + track[0].replace(' ', '_') + '_' + racenum[0]
        return rp

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

    def open_tab(self, url):
        self.driver.execute_script(f"window.open('{url}');")

    def switch_tab(self, idx):
        self.driver.switch_to.window(self.driver.window_handles[idx])

    def close_current_tab(self):
        self.driver.close()

    def run(self):
        rows = self.get_rows_on_current_page()

        is_end = False
        while not is_end:
            race_paths = []
            program_urls = []

            print('getting urls')
            # Get a batch of program urls
            for _ in range(self.batch_size):
                self.switch_tab(0)
                # Try to get the next row, if it exists.
                self.row_idx += 1
                if self.row_idx > len(rows):
                    self.page_idx += 1
                    self.row_idx = 0
                    
                    if not self.click_next_page():
                        is_end = True
                    rows = self.get_rows_on_current_page()
                    if not rows:
                        is_end = True
                
                # If the next row exists,
                if not is_end:
                    rp = self.get_race_path(self.row_idx)
                    race_path = f'{self.date_path}/{rp}'
                    if not os.path.exists(race_path):
                        os.makedirs(race_path)
                    race_paths.append(race_path)

                    # Click the new row
                    self.click_row(rows)

                    buttons = utils.safe_find(self.driver, By.CLASS_NAME, 'bt-button.bt-tertiary.bt-program-page-redirect', num_results=1)
                    if buttons:
                        btn_html = buttons[0].get_attribute('outerHTML')
                        btn_path = utils.find_value_in_html(btn_html, left='href="', right='" ng-click', width=100)
                        btn_url = f'https://www.tvg.com{btn_path[0]}'
                        program_urls.append(btn_url)
                    else:
                        print(f'Error finding button to program page. Skipping race on page {self.page_idx}, row {self.row_idx}.')
            
            print('opening urls')
            # Open a batch of programs
            for url in program_urls:
                self.open_tab(url)

            print('getting info')
            # Get info from each program
            for i, url in enumerate(program_urls):
                self.switch_tab(1)
                program.get_race(self.driver, race_paths[i])
                self.close_current_tab()
            
def main():
    c = Coordinator(batch_size=1)
    time.sleep(20)
    c.run()

if __name__ == '__main__':
    main()
