# https://medium.com/swlh/introduction-to-selenium-create-a-web-bot-with-python-cd59a741fdae

"""
TODO:
parallelize by opening multiple tabs at once.
use webdriver wait instead of time.sleep() https://stackoverflow.com/questions/56119289/element-not-interactable-selenium
"""

# from tkinter import N
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
import re
import pandas as pd

import config

def safe_find(browser, by, value, num_results, retries=2, delay=1):
    for r in range(retries + 1):
        elements = browser.find_elements(by=by, value=value)
        
        if len(elements) > 0:
            if num_results:
                return elements[:num_results]
            return elements
        print("Retrying for value", value)
        time.sleep(delay)
    return None

def find_value_in_html(html, left, right, width=50):
    return [[html[i.end():i.end()+j.start()] for j in re.finditer(right, html[i.end(): i.end() + width])][0] for i in re.finditer(left, html)]

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
    # browser.maximize_window()
    browser.get("https://www.tvg.com/results")

    # Refresh the page to bypass the promotion popup
    browser.refresh()

    # login(browser)
    
    return browser, date_path

def check_and_close_login_popup(browser):
    login_headers = browser.find_elements(by=By.CLASS_NAME, value='styled-components__TitleAtom-sc-1njzr4m-0.styled-components-sc-1njzr4m-1.styled-components__Title-sc-12hkef7-5.ZkNAE.cjGtIh.eOcmRs')
    if len(login_headers) > 0:
        browser.find_element(by=By.CLASS_NAME, value='default-styled-sc-1xv0x-0.RJxHr.styled-components__HeaderButton-sc-12hkef7-2.joFbFy').click()

def get_race_path(browser, item_idx):
    info = safe_find(browser, By.CLASS_NAME, 'replay-list__item-line', num_results=None, retries=1)
    if not info:
        print('Error finding info row of race. Skipping race #' + str(item_idx))
        return False
    html = info[item_idx].get_attribute('innerHTML')
    dt = find_value_in_html(html, left='<span class="replay-list__cell col-date" qa-label="raceReplay-date">', right='</span>')
    track = find_value_in_html(html, left='<span ng-if="HandicappingRaceReplays.events.showTrackColumn\(\)" class="replay-list__cell col-track" qa-label="raceReplay-track".{0,10}>', right='</span>')
    racenum = find_value_in_html(html, left='<span class="replay-list__cell col-race__number" qa-label="raceReplay-raceNumber">', right='</span>')
    print(dt, track, racenum)
    # racetype = find_value_in_html(html, left='<span class="replay-list__cell col-race__type" qa-label="raceReplay-class">', right='</span>')
    # distance = find_value_in_html(html, left='<span class="replay-list__cell col-distance" qa-label="raceReplay-distance">', right='</span>')
    # breed = find_value_in_html(html, left='<span class="replay-list__cell col-breed" qa-label="raceReplay-breed">', right='</span>')

    rp = '_'.join([_ for _ in reversed(dt[0].split(' ')[1:])]) + '_' + track[0].replace(' ', '_') + '_' + racenum[0]
    return rp

def get_details(browser, race_path):
    details = safe_find(browser, By.CLASS_NAME, 'pp-header_race-details_list', num_results=1, retries=3)
    if not details:
        print('Error finding details. Skipping this section for path:', race_path)
        return

    html = details[0].get_attribute('innerHTML')
    dist = find_value_in_html(html, left='<li ng-bind="data.distance">', right='</li>')
    racetype = find_value_in_html(html, left='<li ng-if="!\$root.isGreyhoundRace" ng-bind="data.raceType.Name">', right='</li>')
    raceclass = find_value_in_html(html, left='<span ng-bind="data.currentRace.raceClass">', right='</span>')
    surface = find_value_in_html(html, left='<li ng-if="!\$root.isGreyhoundRace" ng-bind="data.currentRace.surfaceName">', right='</li>')
    condition = find_value_in_html(html, left='<li ng-if="!\$root.isGreyhoundRace" ng-bind="data.currentRace.defaultCondition">', right='</li>')
    df = pd.DataFrame({
        'distance': dist,
        'race type': racetype,
        'race class': raceclass,
        'surface name': surface,
        'default condition': condition,
    })
    df.to_csv(f'{race_path}/details.csv')

def get_results(browser, race_path):
    results = safe_find(browser, By.CLASS_NAME, 'table.race-results.no-margin', num_results=1, retries=1)
    if not results:
        print('Error finding results. Skipping this section for path:', race_path)
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

def get_race_card(browser, race_path):
    tabs = ['Summary', 'Snapshot', 'Speed & Class', 'Pace', 'Jockey/Trainer Stats']

    for i, t in enumerate(tabs):
        tabs = safe_find(browser, By.LINK_TEXT, t, num_results=1, retries=1)
        if not tabs:
            print(f'Error finding element tab {t}. Skipping this section for path:', race_path)
            return
        tabs[0].click()

        tables = safe_find(browser, By.CLASS_NAME, 'race-handicapping-results', num_results=1, retries=1)
        if not tables:
            print(f'Error finding data for tab {t}. Skipping this section for path:', race_path)
            return

        html = tables[0].get_attribute('innerHTML')
        if i == 0:
            scratched = find_scratched(html, query='<strong ng-class="\{.{0,20}: runner.scratched\}" class="h5.{0,20}" qa-label="horse-name">')

            number = find_value_in_html(html, left='<span class="horse-number-label" ng-style="\{.{1,20}: runner.numberColor\}" style="color: rgb(.{1,20})\;">', right='</span></div></td>')
            runner_odds = find_value_in_html(html, left='<strong ng-if="!runner.scratched" class="race-current-odds.{0,20}" ng-class="\{.{1,20} : runner.favorite === true\}">', right='</strong>')
            race_morning_odds = find_value_in_html(html, left='<span ng-if="!runner\.scratched" class="race-morning-odds">', right='</span>')
            name = find_value_in_html(html, left='<strong ng-class="\{.{0,20}: runner.scratched\}" class="h5.{0,20}" qa-label="horse-name">', right='</strong>', width=50)
            age = find_value_in_html(html, left='<span qa-label="age">', right='</span>')
            gender = find_value_in_html(html, left='<span qa-label="gender">', right='</span>')
            sire_dam = find_value_in_html(html, left='<span qa-label="sire-dam">', right='</span>', width=70)

            # damsire and owner name aren't present for japanese races. leave these out for now.
            # damsire = find_value_in_html(html, left='<span qa-label="damsire" ng-if="runner\.damSire \&amp\;\&amp\; runner\.damSire !== .{0,5}"><strong>by</strong>', right='</span>', width=50)
            # owner_name = find_value_in_html(html, left='<span qa-label="owner-name">', right='</span>', width=70)
            df = pd.DataFrame({
                'number': number,
                'runner odds': apply_scratched(runner_odds, scratched),
                'race morning odds': apply_scratched(race_morning_odds, scratched),
                'name': name,
                'age': age,
                'gender': gender,
                'sire dam': sire_dam,
                # 'damsire': damsire,
                # 'owner name': owner_name,
            })
            df.to_csv(f'{race_path}/racecard_left.csv')

            med_weight = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            trainer = find_value_in_html(html, left='<strong qa-label="trainer-name">', right='</strong>', width=50)
            jockey = find_value_in_html(html, left='<strong qa-label="jockey-name">', right='</strong>', width=50)
            df = pd.DataFrame({
                'med': [m for i, m in enumerate(med_weight) if i % 2 == 0],
                'trainer': trainer,
                'weight': [m for i, m in enumerate(med_weight) if i % 2 == 1],
                'jockey': jockey,
            })
            df.to_csv(f'{race_path}/racecard_summ.csv')
        elif i == 1:
            power_wins_daysoff = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            print(power_wins_daysoff)
            df = pd.DataFrame({
                'power rating': [p for i, p in enumerate(power_wins_daysoff) if i % 3 == 0],
                'wins/starts': [p for i, p in enumerate(power_wins_daysoff) if i % 3 == 1],
                'days off': [p for i, p in enumerate(power_wins_daysoff) if i % 3 == 2],
            })
            df.to_csv(f'{race_path}/racecard_snap.csv')
        elif i == 2:
            as_ad_hs_ac_lc = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            df = pd.DataFrame({
                'avg speed': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 0],
                'avg distance': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 1],
                'high speed': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 2],
                'avg class': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 3],
                'last class': [a for i, a in enumerate(as_ad_hs_ac_lc) if i % 5 == 4],
            })
            df.to_csv(f'{race_path}/racecard_spee.csv')
        elif i == 3:
            races_early_mid_fin = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            df = pd.DataFrame({
                'num races': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 0],
                'early': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 1],
                'middle': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 2],
                'finish': [r for i, r in enumerate(races_early_mid_fin) if i % 4 == 3],
            })
            df.to_csv(f'{race_path}/racecard_pace.csv')
        elif i == 4:
            starts_1_2_3 = find_value_in_html(html, left='<strong ng-if="!runner\.scratched &amp;&amp; column\.property">', right='</strong>')
            df = pd.DataFrame({
                'starts': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 0],
                '1st': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 1],
                '2nd': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 2],
                '3rd': [r for i, r in enumerate(starts_1_2_3) if i % 4 == 3],
            })
            df.to_csv(f'{race_path}/racecard_jock.csv')

# Only works if the default selection is $1 Exacta. Doesn't work for others yet.
def get_probables(browser, race_path):
    probables = safe_find(browser, By.CLASS_NAME, 'scroll-x', num_results=1, retries=1)
    if not probables:
        print('Error finding probables. Skipping this section for path:', race_path)
        return

    html = probables[0].get_attribute('innerHTML')
    probables = find_value_in_html(html, left='<span ng-bind="betCombo.payout">', right='</span>')
    length = int(len(probables) ** 0.5)
    df = pd.DataFrame({
        str(l+1): [r for i, r in enumerate(probables) if i % length == l] for l in range(length)
    })
    df.to_csv(f'{race_path}/probables.csv')

# Doesn't work for now
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

    html = pools[0].get_attribute('innerHTML')
    win = find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.winPayoff != undefined" ng-bind="runners\.winPayoff">\$', right='</span>')
    place = find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.placePayoff != undefined" ng-bind="runners\.placePayoff">\$', right='</span>')
    show = find_value_in_html(html, left='<span class="amounts text-centered td" ng-if="runners\.showPayoff != undefined" ng-bind="runners\.showPayoff">\$', right='</span>')
    df = pd.DataFrame({
        'win': win,
        'place': place,
        'show': show
    })
    df.to_csv(f'{race_path}/pools.csv')   

def get_race(browser, race_path):
    get_details(browser, race_path)
    get_results(browser, race_path)
    get_race_card(browser, race_path)
    # get_probables(browser, race_path)
    # get_willpays(browser, race_path)
    get_pools(browser, race_path)

def get_page(browser, date_path, page_idx):
    items = safe_find(browser, By.CLASS_NAME, 'replay-list__item-line', num_results=None, retries=3)
    if not items:
        print(f'Error finding results on page {page_idx}. Skipping to the next page.')
        return

    actions = ActionChains(browser)
    
    item_idx = 0
    while item_idx < len(items):
        rp = get_race_path(browser, item_idx)
        if rp:
            race_path = f'{date_path}/{rp}'
            if not os.path.exists(race_path):
                os.makedirs(race_path)
            
                buttons = safe_find(browser, By.CLASS_NAME, 'bt-button.bt-tertiary.bt-program-page-redirect', num_results=1, retries=1)
                if buttons:
                    # time.sleep(1)
                    btn_html = buttons[0].get_attribute('outerHTML')
                    btn_path = find_value_in_html(btn_html, left='href="', right='" ng-click', width=100)
                    btn_url = f'https://www.tvg.com{btn_path[0]}'
                    browser.execute_script(f"window.open(\"{btn_url}\");")
                    browser.switch_to.window(browser.window_handles[1])
                    get_race(browser, race_path)
                    browser.close()
                    browser.switch_to.window(browser.window_handles[0])
                else:
                    print('Error finding button to program page. Skipping race #' + str(item_idx))
            else:
                print(f'Directory {race_path} already exists. Skipping.')
        else:
            print('Error finding info row. Skipping race #' + str(item_idx))
        
        item_idx += 1

        new_items = safe_find(browser, By.CLASS_NAME, 'replay-list__item-line', num_results=None, retries=3)
        if not new_items:
            print('Error find results when returning to results page.')
            break

        if item_idx < len(new_items):
            # actions = ActionChains(browser)
            actions.move_to_element(new_items[item_idx]).perform()
            new_items[item_idx].click()
        else:
            break

def main():
    browser, date_path = setup()
    time.sleep(20) # 20 seconds to log in before script starts.
    page_idx = 0
    
    has_next = True
    while has_next:
        get_page(browser, date_path, page_idx)
        page_idx += 1

        next_pages = safe_find(browser, By.CSS_SELECTOR, "a[ng-click='selectPage(page + 1, $event)']:not([disabled='disabled'])", num_results=1, retries=1) # https://devqa.io/selenium-css-selectors/
        if not next_pages:
            print(f'Cannot find next page ({page_idx}). Exiting...')
            has_next = False
            return
        next_pages[0].click()
        # time.sleep(2)
        # browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
        new_items = safe_find(browser, By.CLASS_NAME, 'replay-list__item-line', num_results=None, retries=3)
        if not new_items:
            print('Error find results when returning to results page. Stopping now.')
            break
        actions = ActionChains(browser)
        actions.move_to_element(new_items[0]).perform()
        new_items[0].click()

    browser.close()

if __name__ == '__main__':
    main()
