import time
import json
import gzip, zlib
import datetime as dt
import pandas as pd
from tqdm import tqdm

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup():
    options = Options()
    # Add all these params to bypass bot detection: https://stackoverflow.com/questions/53039551/selenium-webdriver-modifying-navigator-webdriver-flag-to-prevent-selenium-detec
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    # driver.get("https://www.tvg.com/racetracks/ROS/rosecroft-raceway?race=5")
    driver.get("https://www.tvg.com/races")
    driver.refresh()
    return driver

# getRaceProgram - for pools data
# getRacesMtpStatus - for MTP updates on the schedule

def open_url_in_new_tab(driver, url, state):
    state['num_tabs'] += 1
    driver.execute_script(f"window.open(\"{url}\");")
def switch_to_tab(driver, tab_idx):
    driver.switch_to.window(driver.window_handles[tab_idx])
def close_current_tab(driver, state):
    state['num_tabs'] -= 1
    driver.close()

def get_request_body(request):
    return json.loads(str(request.body,'utf-8'))
def get_response_headers(request):
    return request.response.headers
def get_response_body(request):
    return json.loads(str(zlib.decompress(bytes(request.response.body), 15+32), 'utf-8'))

def get_latest_races(driver, races_info, state, mtp_threshold=5):
    print('=== get latest races ===')
    found_races_for_this_interval = False
    num_requests = len(driver.requests)
    while state['schedule_requests_idx'] < num_requests:
        request = driver.requests[state['schedule_requests_idx']]
        state['schedule_requests_idx'] += 1
        if found_races_for_this_interval:
            state['schedule_requests_idx'] = num_requests
            break
        if request.response:
            if 'service.tvg.com/graph/v2/query' in request.url:
                operationName = get_request_body(request)['operationName']
                if operationName == 'getRacesMtpStatus':
                    body = get_response_body(request)
                    races = body['data']['mtpRaces']
                    for race in races:
                        race_id = f"{race['trackCode']}-{race['number']}"
                        if race['mtp'] <= mtp_threshold and race_id not in races_info:
                            print(f'new race: {race_id}, mtp: {race["mtp"]}')
                            track_name = ''.join(race['trackName'].lower().split(' '))
                            races_info[race_id] = {
                                'status': 'new',
                                'url': f"https://www.tvg.com/racetracks/{race['trackCode']}/{track_name}?race={race['number']}",
                                'time_of_last_data': None,
                                'tab_idx': None,
                            }
                    found_races_for_this_interval = True

# I need to keep track of the order of races in tabs.
def open_latest_tabs(driver, races_info, state):
    print('=== open latest tabs ===')
    for race_id, info in races_info.items():
        if info['status'] == 'new':
            print('opened tab for race_id:', race_id, info['url'])
            open_url_in_new_tab(driver, info['url'], state)
            races_info[race_id]['status'] = 'open'
            state['tabs_to_raceId'].append(race_id)
            # races_info[race_id]['tab_idx'] = state['num_tabs'] - 1
    switch_to_tab(driver, 0)

"""
issues:
gets pools from other races for some reason. they are duplicates too.
closes races that aren't finished.

do all tabs share the same requests list? I think so.
- I need to map race_id to tab_idx.
- for polling, I only need to loop through all the driver.requests once, since they're all shared.
- when I find a race that needs to be closed, I record the race_id.
- at the end, I'll get the tab_idx's to be closed from the list of race_id's.

need 1 requests_idx.
{ race_id: { tab_idx, time_of_last_data, } }

when I close a tab, I need to update the tab_idx somehow. It's better to maintain
a list of tabs.

It's slowing down the longer I go. probably because the requests are adding up.
If I close a tab, do the requests stay? Or do they get deleted and I have to update the 
    poll_requests_index?
    - seems like they stay because they were showing up even after I deleted the tab since was some
      delay between registering the tab to be deleted and actually deleting it.

I can try making the request myself (unlikely to work). Ok it works now.
- I don't have to be authenticated, so what's blocking me from making the request?
I can try 
"""
def poll_data(driver, races_info, state):
    print('=== polling data ===')
    tabs_to_close = []

    num_requests = len(driver.requests)
    print(f"k: {state['poll_requests_idx']}, num_requests: {num_requests}")
    for k in range(state['poll_requests_idx'], num_requests):
        request = driver.requests[k]
        if request.response:
            if 'service.tvg.com/graph/v2/query' in request.url:
                operationName = get_request_body(request)['operationName']
                if operationName == 'getRaceResults':
                    body = get_response_body(request)
                    race_id = f"{body['data']['race']['track']['code']}-{body['data']['race']['number']}"
                    # add this race_id to race_ids_closed
                    if races_info[race_id]['status'] == 'open':
                        races_info[race_id]['status'] = 'closed'
                        # add tab_idx to the to-close list
                        for t, tab_race_id in enumerate(state['tabs_to_raceId']):
                            if tab_race_id == race_id:
                                tabs_to_close.append(t+1)
                                break
                        # tabs_to_close.append(races_info[race_id]['tab_idx'])
                if operationName == 'getRaceProgram':
                    body = get_response_body(request)
                    race = body['data']['race']
                    race_id = f"{race['track']['code']}-{race['number']}"
                    races_info[race_id]['time_of_last_data'] = dt.datetime.now()
                    if race['racePools'] == None:
                        continue
                    pools = {}
                    # get 'win' id
                    win_id = -1
                    for rp in race['racePools']:
                        if rp['wagerType']['name'] == 'Win':
                            win_id = rp['wagerType']['id']
                    # get win pool for each horse
                    for horse in race['bettingInterests']:
                        horse_number = horse['biNumber']
                        if horse['biPools'] == None:
                            continue
                        horse_pool = 0
                        for bp in horse['biPools']:
                            if bp['wagerType']['id'] == win_id:
                                horse_pool = bp['poolRunnersData'][0]['amount']
                        pools[horse_number] = horse_pool
                    resp_headers = get_response_headers(request)
                    resp_dt = dt.datetime.strptime(resp_headers['Date'].split(', ')[1][:-4], '%d %b %Y %H:%M:%S') - dt.timedelta(hours=7)
                    print(f"    {resp_dt} | {race['track']['name']} | {k}")
                    print(f"    {pools}")
    state['poll_requests_idx'] = num_requests
    
    for tab_idx in sorted(tabs_to_close, key=lambda x: -x):
        print('closing,', tab_idx)
        switch_to_tab(driver, tab_idx)
        close_current_tab(driver, state)
    switch_to_tab(driver, 0)

"""
maintain a tabs_list that maps tab_idx to race_id
whenever I encounter getRaceResults, get the race_id
"""

def main():
    driver = setup()

    races_info = {}
    state = {
        'num_tabs': 1,
        'tabs_to_raceId': [],
        'schedule_requests_idx': 0,
        'poll_requests_idx': 0,
    }
    while True:
        start_time = dt.datetime.now()
        get_latest_races(driver, races_info, state)
        open_latest_tabs(driver, races_info, state)
        poll_data(driver, races_info, state)
        while dt.datetime.now() - start_time < dt.timedelta(seconds=15):
            pass

if __name__ == "__main__":
    main()