from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import datetime as dt
import re
import sys
import traceback

##### utils functions #####

def safe_find(driver, by, value, num_results, retries=2, retry_delay=1, verbose=True, err_msg='safe_find encountered error.', on_err=None):
    for r in range(retries + 1):
        elements = driver.find_elements(by=by, value=value)
        
        if len(elements) > 0:
            if num_results:
                return elements[:num_results]
            return elements
        if verbose:
            print(f"Retrying safe find for value {value}. Attempts remaining: {retries - r}")
        time.sleep(retry_delay)

    print(err_msg)
    if not on_err:
        exit(1)
    return on_err()

def find_value_in_html(html, left, right, width=50):
    return [[html[i.end():i.end()+j.start()] for j in re.finditer(right, html[i.end(): i.end() + width])][0] for i in re.finditer(left, html)]

def safe_click(component, actions, label, move=True, retries=2, retry_delay=1, verbose=True, on_err=None):
    if move:
        actions.move_to_element(component).perform()
    for r in range(retries + 1):
        try:
            component.click()
            return
        except Exception:
            if retries - r == 0:
                if verbose:
                    traceback.print_exc()
                if not on_err:
                    exit(1)
                return on_err()
            if verbose:
                print(f'Retrying click on {label}. Attempts remaining: {retries - r}')
            time.sleep(retry_delay)
    exit(1)

##### helper functions #####

def setup():
    # today = date.today()
    # date_string = today.strftime("%Y-%m-%d")
    # date_path = f'./history/{date_string}'
    # if not os.path.exists(date_path):
    #     os.makedirs(date_path)

    options = Options()
    # Add all these params to bypass bot detection: https://stackoverflow.com/questions/53039551/selenium-webdriver-modifying-navigator-webdriver-flag-to-prevent-selenium-detec
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    actions = ActionChains(driver)
    driver.get("https://www.tvg.com/results")
    
    # Refresh the page to bypass the promotion popup
    driver.refresh()

    # Unhide results
    # switch = safe_find(driver, By.CLASS_NAME, 'switch__control.thumb', num_results=1, err_msg='Error finding switch. Stopping')
    # actions.move_to_element(switch[0]).perform()
    # safe_click(switch[0])

    # # Refresh the page to load first results
    # driver.refresh()
    
    return driver, actions

def find_current_month_year(driver):
    my = safe_find(driver, By.CSS_SELECTOR, "button[id^='datepicker-']", num_results=1, err_msg='Error finding month and year of calendar. Stopping.')
    html = my[0].get_attribute('innerHTML')
    month_year = find_value_in_html(html, left='<strong>', right='</strong>')[0]
    return month_year

def get_tracks_list(driver):
    tracks = safe_find(driver, By.CSS_SELECTOR, 'select[qa-label="raceReplaysTrackList"]', num_results=1, err_msg='Error finding tracks. Stopping.')
    html = tracks[0].get_attribute('innerHTML')
    tracks = find_value_in_html(html, left='<option label=\".{1,60}\" value=\".{1,15}\"( selected="selected")?>', right='</option>', width=60)
    return tracks

def month_year_only(d):
    return d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def click_calendar(driver, actions):
    calendar = safe_find(driver, By.CLASS_NAME, 'tvg-icon-calendar', num_results=1, err_msg='Error finding calendar. Stopping.')
    safe_click(calendar[0], actions, 'calendar')

def click_track_dropdown(driver, actions):
    track_dropdown = safe_find(driver, By.CSS_SELECTOR, 'select[qa-label="raceReplaysTrackList"]', num_results=1, err_msg='Error finding track_dropdown. Stopping.')
    safe_click(track_dropdown[0], actions, 'track dropdown')

def click_previous_month(driver, actions):
    left = safe_find(driver, By.CLASS_NAME, "tvg-icon-arrow-left", num_results=1, err_msg='Error finding left arrow. Stopping.')
    safe_click(left[0], actions, 'previous month button', move=False)

def click_day(driver, actions, day):
    days = safe_find(driver, By.CSS_SELECTOR, "span[ng-class=\"::{'text-muted': dt.secondary, 'text-info': dt.current}\"]:not([class='text-muted']", num_results=None, err_msg='Error finding days in calendar. Stopping.')
    safe_click(days[day - 1], actions, 'calendar day', move=False)

def travel_back(driver, actions, open_calendar=True, target=None, num_days=None):
    if not target and not num_days:
        print('Must provide at least one of target date or num_days. Stopping.')
        exit(1)

    # assumes the calendar is already open
    def find_current_day(driver):
        days = safe_find(driver, By.CLASS_NAME, "btn.btn-default.btn-sm.btn-info.active", num_results=None, err_msg='Error finding month and year of calendar. Stopping.')
        html = days[0].get_attribute('innerHTML')
        day = find_value_in_html(html, left='">', right='</span>')[0]
        return day
    
    if open_calendar:
        click_calendar(driver, actions)
    
    month_year = find_current_month_year(driver)
    day = find_current_day(driver)
    cur_date = dt.datetime.strptime(f'{day} {month_year}', "%d %B %Y")

    # (TODO) Create a directory for this date, if it doesn't already exist.

    if target:
        if target > cur_date:
            print('Target date is in the future. Stopping.')
            exit(1)
        cur_my = dt.datetime.strptime(month_year, "%B %Y")
        target_my = month_year_only(target)
        while cur_my > target_my:
            click_previous_month(driver, actions)
            month_year = find_current_month_year(driver)
            cur_my = dt.datetime.strptime(month_year, "%B %Y")
        target_day = target.day
        click_day(driver, actions, target_day)
    elif num_days:
        if num_days < 0:
            print('num_days must be a positive integer. Stopping.')
            exit(1)
        
        new_target = cur_date - dt.timedelta(days=num_days)
        travel_back(driver, actions, open_calendar=False, target=new_target)

def get_race_date_time(driver, row_idx):
    info = safe_find(driver, By.CLASS_NAME, 'replay-list__item-line', num_results=None, err_msg='Error finding row of race. Skipping race #' + str(row_idx))
    html = info[row_idx].get_attribute('innerHTML')
    dt = find_value_in_html(html, left='<span class="replay-list__cell col-date" qa-label="raceReplay-date">', right='</span>')
    track = find_value_in_html(html, left='<span ng-if="HandicappingRaceReplays.events.showTrackColumn\(\)" class="replay-list__cell col-track" qa-label="raceReplay-track".{0,10}>', right='</span>')
    racenum = find_value_in_html(html, left='<span class="replay-list__cell col-race__number" qa-label="raceReplay-raceNumber">', right='</span>')
    print(dt, track, racenum)

    rp = '_'.join([_ for _ in reversed(dt[0].split(' ')[1:])]) + '_' + track[0].replace(' ', '_') + '_' + racenum[0]
    return rp

def click_show_race_card(driver, actions):
    btn = safe_find(driver, By.CSS_SELECTOR, "button[qa-label=\"showFullCardBtn\"]", num_results=1, err_msg='Error finding show race card button. Stopping.')
    safe_click(btn[0], actions, 'show race card button')

def get_results(driver, actions):
    pass

def get_racecard(driver, actions):
    pass

def get_page(driver, actions, track_name):
    # (TODO) For each race, create a directory, if it doesn't already exist, for time + race_park_name + race_number, 
    # under the date directory.
    # get the date and time from the first row. get the track name from 
    # cur_date_str = cur_date.strftime("%Y-%m-%d")
    # date_path = f'./historical_results/{cur_date_str}'
    # if not os.path.exists(date_path):
    #     os.makedirs(date_path)

    print(f'    {track_name}')
    def on_empty_page():
        return []
    def on_stale_row():
        return False

    row_retries = 2
    for r in range(row_retries + 1):
        rows = safe_find(driver, By.CLASS_NAME, 'replay-list__item-line', num_results=None, 
                            err_msg='Error find results on results page.',on_err=on_empty_page)
        if not rows:
            print(f'Found empty page for track {track_name}. Skipping.')
            return
        is_successful = safe_click(rows[0], actions, f'{track_name} row 0 (check if loaded)', move=False, verbose=True, on_err=on_stale_row)
        if is_successful:
            print('is successful')
            break
    if not is_successful:
        print('was not successful')
        return

    for i in range(len(rows)):
        # (TODO)
        # click_show_race_card(driver, actions)
        # get_results(driver, actions)
        # get_racecard(driver, actions)

        new_rows = safe_find(driver, By.CLASS_NAME, 'replay-list__item-line', num_results=None, verbose=False,
                            err_msg='Error find results on results page.', on_err=on_empty_page)
        if not new_rows:
            print(f'Found empty page for track {track_name}. Skipping.')
            return
        
        if i < len(new_rows) - 1:
            safe_click(new_rows[i+1], actions, f'{track_name} row {i+1}', move=False)
            time.sleep(0.5)

def iterate_through_tracks(driver, actions, on_track):
    tracks = get_tracks_list(driver)
    # Reference for selectors: https://selenium-python.readthedocs.io/navigating.html#filling-in-forms
    dropdown = safe_find(driver, By.CSS_SELECTOR, 'select[qa-label="raceReplaysTrackList"]', num_results=1, err_msg='Error finding tracks dropdown. Stopping.')
    all_options = safe_find(dropdown[0], By.TAG_NAME, 'option', num_results=None, err_msg='Error finding options in track dropdown. Stopping.')
    for i, option in enumerate(all_options):
        # print("Value is: %s" % option.get_attribute("value"))
        safe_click(option, actions, 'track {tracks[i]}', move=False)
        on_track(driver, actions, tracks[i])


##### main code #####

def main(start_str, end_str):
    driver, actions = setup()
    start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
    if start_date > dt.datetime.today():
        print('Start date is in the future. Stopping.')
        exit(1)

    travel_back(driver, actions, target=start_date)

    num_days = (start_date - end_date).days + 1
    cur_date = start_date
    for d in range(num_days):
        cur_date_str = cur_date.strftime("%Y-%m-%d")
        date_path = f'./historical_results/{cur_date_str}'
        if not os.path.exists(date_path):
            os.makedirs(date_path)

        print(f'========== {cur_date_str} ==========')
        time.sleep(2) # (just keep it here for now) usually we won't need this sleep since it will check rows 
                      # first before clicking on the tracks dropdown so the contents will be updated by then.
        iterate_through_tracks(driver, actions, on_track=get_page)

        cur_date = cur_date - dt.timedelta(days=1)
        travel_back(driver, actions, num_days=1)

    """
    Steps for bot:
    1. click on the date box.
    2. read the month and year. read the date from the highlighted box.
    3. if the date is ahead of the starting point, click the back arrow until we're at the 
        right month. then click on the right day.
    4. the first track is already selected.
        i. the first row is already selected.
            - click the "show race card" button.
            - download the results table into a csv.
            - download the racecard table into a csv (mainly just the horse number and odds)
        ii. select the next row, if our index is less than the length of the rows list. repeat.
    5. click on the track dropdown. press the down key. press enter. this will take us to the
        next track. We'll know if there are tracks left since they show as <option/> in the html.
        repeat this for all tracks.
    6. decrement our date. click the calendar and check it against the month,day,year. if it's present
        click on the previous day box. if it's not present, click the back arrow to go back a month.
        then click the day box. repeat from step 1.
    """

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args[0], args[1])