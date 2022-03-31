from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import datetime as dt
import re
import sys
import traceback
import pandas as pd

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
                if not on_err:
                    traceback.print_exc()
                    exit(1)
                return on_err()
            if verbose:
                print(f'Retrying click on {label}. Attempts remaining: {retries - r}')
            time.sleep(retry_delay)
    exit(1)

def pad_or_trunc_list(arr, target_len):
    return arr[:target_len] + ['-']*(target_len - len(arr))

def apply_scratched(arr, scratched):
    i = 0
    result = []
    for s in scratched:
        if not s:
            result.append(arr[i])
            i += 1
        else:
            result.append('-')
    return result

def find_scratched(html, query):
    return [len([k for k in re.finditer('class="h5 text-scratched"', j)]) for j in [html[i.start():i.end()] for i in re.finditer(query, html)]]

##### helper functions #####

def setup():
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
    # After midnight, the switch isn't visible until more race results are shown. I need to switch
    # to another calendar day to flip the switch.
    temp_date = dt.datetime.strptime('2022-03-30', "%Y-%m-%d")
    travel_back(driver, actions, target=temp_date)
    switch = safe_find(driver, By.CLASS_NAME, 'switch__control.thumb', num_results=1, err_msg='Error finding switch. Stopping')
    safe_click(switch[0], actions, 'hide results switch', move=True)

    # # Refresh the page to load first results
    driver.refresh()
    
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

def scroll_to_top(driver):
    body = safe_find(driver, By.TAG_NAME, 'body', num_results=1, err_msg='Error finding body. Stopping.')
    body[0].send_keys(Keys.CONTROL + Keys.HOME)

def click_calendar(driver, actions):
    scroll_to_top(driver)
    calendar = safe_find(driver, By.CLASS_NAME, 'tvg-icon-calendar', num_results=1, err_msg='Error finding calendar. Stopping.')
    safe_click(calendar[0], actions, 'calendar', move=True)

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

    # find_current_day assumes the calendar is already open
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
    safe_click(btn[0], actions, 'show race card button', move=True, retries=4 ,verbose=False)

def get_results(driver, actions, race_path):
    def on_missing_results():
        return False
    results = safe_find(driver, By.CLASS_NAME, 'table.race-results.no-margin', num_results=1, err_msg=f'Error finding results for path: {race_path}. Skipping.', on_err=on_missing_results)
    if results == False:
        return

    html = results[0].get_attribute('innerHTML')
    number = find_value_in_html(html, left='runner\.bettingInterestNumber" style="color: rgb\(.{1,20}\)\;">', right='</span></div>')
    name = find_value_in_html(html, left='ng-bind="runner.runnerName">', right='</strong></td>')
    win = pad_or_trunc_list(find_value_in_html(html, left='winPayoff\)">\$', right='</td>'), len(number))
    place = pad_or_trunc_list(find_value_in_html(html, left='placePayoff\)">\$', right='</td>'), len(number))
    show = pad_or_trunc_list(find_value_in_html(html, left='showPayoff\)">\$', right='</td>'), len(number))
    df = pd.DataFrame({
        'ranking': [_ for _ in range(1, len(number) + 1)],
        'horse number': number,
        'horse name': name,
        'win': win,
        'place': place,
        'show': show
    })
    df.to_csv(f'{race_path}/results.csv')

def get_racecard(driver, actions, race_path):
        def on_missing_results():
            return False
        left = safe_find(driver, By.CLASS_NAME, 'race-handicapping-results', num_results=1, err_msg=f'Error finding racecard left for path: {race_path}. Skipping.', on_err=on_missing_results)
        if left == False:
            return
        html = left[0].get_attribute('innerHTML')
        scratched = find_scratched(html, query='<strong ng-class="\{.{0,20}: runner.scratched\}" class="h5.{0,20}" qa-label="horse-name">')

        number = find_value_in_html(html, left='<span class="horse-number-label" ng-style="\{.{1,20}: runner.numberColor\}" style="color: rgb(.{1,20})\;">', right='</span></div></td>')
        runner_odds = find_value_in_html(html, left='<strong ng-if="!runner.scratched" class="race-current-odds.{0,20}" ng-class="\{.{1,20} : runner.favorite === true\}">', right='</strong>')
        race_morning_odds = find_value_in_html(html, left='<span ng-if="!runner\.scratched" class="race-morning-odds">', right='</span>')
        name = find_value_in_html(html, left='<strong ng-class="\{.{0,20}: runner.scratched\}" class="h5.{0,20}" qa-label="horse-name">', right='</strong>', width=50)
        age = find_value_in_html(html, left='<span qa-label="age">', right='</span>')
        gender = find_value_in_html(html, left='<span qa-label="gender">', right='</span>')
        sire_dam = find_value_in_html(html, left='<span qa-label="sire-dam">', right='</span>', width=70)

        df = pd.DataFrame({
            'number': number,
            'runner odds': apply_scratched(runner_odds, scratched),
            'race morning odds': apply_scratched(race_morning_odds, scratched),
            'name': name,
            'age': age,
            'gender': gender,
            'sire dam': sire_dam,
        })
        df.to_csv(f'{race_path}/racecard_left.csv')

def get_page(driver, actions, track_name):
    def on_empty_page():
        return []
    def on_stale_row():
        return False

    row_retries = 3
    for r in range(row_retries + 1):
        rows = safe_find(driver, By.CLASS_NAME, 'replay-list__item-line', num_results=None, 
                            err_msg='Error finding results on results page.',on_err=on_empty_page)
        if not rows:
            print(f'Found empty page for track {track_name}. Skipping.')
            return
        is_successful = safe_click(rows[0], actions, f'{track_name} row 0 (check if loaded)', move=False, verbose=False, on_err=on_stale_row)
        if is_successful == False:
            continue
        else:
            break
    if is_successful == False:
        return

    for i in range(len(rows)):
        new_rows = safe_find(driver, By.CLASS_NAME, 'replay-list__item-line', num_results=None, 
                            err_msg='Error finding rows on results page.')

        # Create folder for the race
        html = new_rows[i].get_attribute('innerHTML')
        dt = find_value_in_html(html, left='<span class="replay-list__cell col-date" qa-label="raceReplay-date">', right='</span>')
        racenum = find_value_in_html(html, left='<span class="replay-list__cell col-race__number" qa-label="raceReplay-raceNumber">', right='</span>')
        d = dt[0].split(' ')[0].split('-')
        d = '-'.join([d[2], d[0], d[1]])
        t = '_'.join([_ for _ in reversed(dt[0].split(' ')[1:])])
        folder_name = '_'.join([t, track_name.strip().replace(' ','_'), racenum[0]])
        race_path = f'./historical_results/{d}/{folder_name}'
        if os.path.exists(race_path):
            continue
        os.makedirs(race_path)

        # Get race data
        safe_click(new_rows[i], actions, f'{track_name} row {i}', move=False)
        click_show_race_card(driver, actions)
        get_results(driver, actions, race_path)
        get_racecard(driver, actions, race_path)
        
def iterate_through_tracks(driver, actions, on_track):
    tracks = get_tracks_list(driver)
    # Reference for selectors: https://selenium-python.readthedocs.io/navigating.html#filling-in-forms
    dropdown = safe_find(driver, By.CSS_SELECTOR, 'select[qa-label="raceReplaysTrackList"]', num_results=1, err_msg='Error finding tracks dropdown. Stopping.')
    all_options = safe_find(dropdown[0], By.TAG_NAME, 'option', num_results=None, err_msg='Error finding options in track dropdown. Stopping.')
    for i, option in enumerate(all_options):
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

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args[0], args[1])