import time
import json
import gzip, zlib
import datetime as dt
import pandas as pd

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

def open_url_in_new_tab(driver, url):
    driver.execute_script(f"window.open(\"{url}\");")
def switch_to_tab(driver, tab_idx):
    driver.switch_to.window(driver.window_handles[tab_idx])
def close_current_tab(driver):
    driver.close()

def get_request_body(request):
    return json.loads(str(request.body,'utf-8'))
def get_response_headers(request):
    return request.response.headers
def get_response_body(request):
    return json.loads(str(zlib.decompress(bytes(request.response.body), 15+32), 'utf-8'))

# def poll_data_v1(driver, timeout=30):
#     i = 0
#     start_time = dt.datetime.now()
#     while dt.datetime.now() - start_time <= dt.timedelta(minutes=timeout):
#         while i < len(driver.requests):
#             request = driver.requests[i]
#             if request.response:
#                 if 'service.tvg.com/graph/v2/query' in request.url:
#                     operationName = get_request_body(request)['operationName']
#                     if operationName == 'getRaceResults':
#                         # close the tab
#                         # add this race_id to race_ids_closed
#                         return
#                     if operationName == 'getRaceProgram':
#                         body = get_response_body(request)
#                         race = body['data']['race']
#                         if race['racePools'] == None:
#                             continue
#                         pools = {}
#                         # get 'win' id
#                         win_id = -1
#                         for rp in race['racePools']:
#                             if rp['wagerType']['name'] == 'Win':
#                                 win_id = rp['wagerType']['id']
#                         # get win pool for each horse
#                         for horse in race['bettingInterests']:
#                             horse_number = horse['biNumber']
#                             if horse['biPools'] == None:
#                                 continue
#                             horse_pool = 0
#                             for bp in horse['biPools']:
#                                 if bp['wagerType']['id'] == win_id:
#                                     horse_pool = bp['poolRunnersData'][0]['amount']
#                             pools[horse_number] = horse_pool
#                         print(dt.datetime.now())
#                         print(pools)
#             i += 1
#         time.sleep(5)

def get_latest_races(driver, i, races_info, mtp_threshold=5):
    print('=== get latest races ===')
    found_races_for_this_interval = False
    num_requests = len(driver.requests)
    while i[0] < num_requests:
        request = driver.requests[i[0]]
        i[0] += 1
        if found_races_for_this_interval:
            i[0] = num_requests
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
                            print('new race:', race_id)
                            track_name = ''.join(race['trackName'].lower().split(' '))
                            races_info[race_id] = {
                                'status': 'new',
                                'url': f"https://www.tvg.com/racetracks/{race['trackCode']}/{track_name}?race={race['number']}",
                            }
                    found_races_for_this_interval = True

# I need to keep track of the order of races in tabs.
def open_latest_tabs(driver, races_info, tabs_list):
    print('=== open latest tabs ===')
    for race_id, info in races_info.items():
        if info['status'] == 'new':
            print('opened tab for race_id:', race_id)
            open_url_in_new_tab(driver, info['url'])
            tabs_list.append({
                'requests_idx': 0,
                'race_id': race_id,
                'time_of_last_data': None,
            })
            races_info[race_id]['status'] = 'open'
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
"""

# add timeout after last datapoint if getRaceResults doesn't show up.
# def poll_data_v2(driver, races_info, tabs_list, timeout=5):
#     print('=== polling data ===')
#     tabs_to_close = []
#     for t in range(len(tabs_list)):
#         tab_idx = t + 1
#         if tabs_list[t]['time_of_last_data'] == None:
#             tabs_list[t]['time_of_last_data'] = dt.datetime.now()
#         if dt.datetime.now() - tabs_list[t]['time_of_last_data'] > dt.timedelta(minutes=timeout):
#             # add this race_id to race_ids_closed
#             race_id = tabs_list[t]['race_id']
#             races_info[race_id]['status'] = 'closed'
#             # add tab_idx to the to-close list
#             tabs_to_close.append(tab_idx)
#             continue
        
#         print('tab:', tab_idx)
#         switch_to_tab(driver, tab_idx)
#         num_requests = len(driver.requests)
#         print('num requests:', num_requests)
#         for k in range(tabs_list[t]['requests_idx'], num_requests):
#             request = driver.requests[k]
#             if request.response:
#                 if 'service.tvg.com/graph/v2/query' in request.url:
#                     operationName = get_request_body(request)['operationName']
#                     if operationName == 'getRaceResults':
#                         # add this race_id to race_ids_closed
#                         race_id = tabs_list[t]['race_id']
#                         races_info[race_id]['status'] = 'closed'
#                         # add tab_idx to the to-close list
#                         tabs_to_close.append(tab_idx)
#                         break
#                     if operationName == 'getRaceProgram':
#                         tabs_list[t]['time_of_last_data'] = dt.datetime.now()
#                         body = get_response_body(request)
#                         race = body['data']['race']
#                         if race['racePools'] == None:
#                             continue
#                         pools = {}
#                         # get 'win' id
#                         win_id = -1
#                         for rp in race['racePools']:
#                             if rp['wagerType']['name'] == 'Win':
#                                 win_id = rp['wagerType']['id']
#                         # get win pool for each horse
#                         for horse in race['bettingInterests']:
#                             horse_number = horse['biNumber']
#                             if horse['biPools'] == None:
#                                 continue
#                             horse_pool = 0
#                             for bp in horse['biPools']:
#                                 if bp['wagerType']['id'] == win_id:
#                                     horse_pool = bp['poolRunnersData'][0]['amount']
#                             pools[horse_number] = horse_pool
#                         resp_headers = get_response_headers(request)
#                         resp_dt = dt.datetime.strptime(resp_headers['Date'].split(', ')[1][:-4], '%d %b %Y %H:%M:%S') - dt.timedelta(hours=7)
#                         print('   ', resp_dt, '|', race['track']['name'])
#                         print('   ', pools)
#         tabs_list[t]['requests_idx'] = num_requests
    
#     for tab_idx in reversed(tabs_to_close):
#         del tabs_list[tab_idx-1]
#         print('closing,', tab_idx)
#         switch_to_tab(driver, tab_idx)
#         close_current_tab(driver)
#     switch_to_tab(driver, 0)

"""
need 1 requests_idx.
{ race_id: { tab_idx, time_of_last_data, } }
"""
def poll_data(driver, races_info, tabs_list, timeout=5):
    print('=== polling data ===')
    tabs_to_close = []
    for t in range(len(tabs_list)):
        tab_idx = t + 1
        if tabs_list[t]['time_of_last_data'] == None:
            tabs_list[t]['time_of_last_data'] = dt.datetime.now()
        if dt.datetime.now() - tabs_list[t]['time_of_last_data'] > dt.timedelta(minutes=timeout):
            # add this race_id to race_ids_closed
            race_id = tabs_list[t]['race_id']
            races_info[race_id]['status'] = 'closed'
            # add tab_idx to the to-close list
            tabs_to_close.append(tab_idx)
            continue
        
        print('tab:', tab_idx)
        switch_to_tab(driver, tab_idx)
        num_requests = len(driver.requests)
        print('num requests:', num_requests)
        for k in range(tabs_list[t]['requests_idx'], num_requests):
            request = driver.requests[k]
            if request.response:
                if 'service.tvg.com/graph/v2/query' in request.url:
                    operationName = get_request_body(request)['operationName']
                    if operationName == 'getRaceResults':
                        # add this race_id to race_ids_closed
                        race_id = tabs_list[t]['race_id']
                        races_info[race_id]['status'] = 'closed'
                        # add tab_idx to the to-close list
                        tabs_to_close.append(tab_idx)
                        break
                    if operationName == 'getRaceProgram':
                        tabs_list[t]['time_of_last_data'] = dt.datetime.now()
                        body = get_response_body(request)
                        race = body['data']['race']
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
                        print('   ', resp_dt, '|', race['track']['name'])
                        print('   ', pools)
        tabs_list[t]['requests_idx'] = num_requests
    
    for tab_idx in reversed(tabs_to_close):
        del tabs_list[tab_idx-1]
        print('closing,', tab_idx)
        switch_to_tab(driver, tab_idx)
        close_current_tab(driver)
    switch_to_tab(driver, 0)

def main():
    driver = setup()
    # poll_data(driver)

    # find new races
    # open a new tab for each race
    # loop through each tab to get updates.

    schedule_requests_idx = [0]

    # for each tab, store the request index, the race_id, and the time of last data point.
    tabs_list = []
    # new, open, closed
    races_info = {}
    while True:
        start_time = dt.datetime.now()
        get_latest_races(driver, schedule_requests_idx, races_info)
        open_latest_tabs(driver, races_info, tabs_list)
        poll_data(driver, races_info, tabs_list)
        while dt.datetime.now() - start_time < dt.timedelta(seconds=5):
            pass

if __name__ == "__main__":
    main()