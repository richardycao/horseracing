import requests
import tvg_requests
import json
import datetime as dt

"""
Periodically make requests to get the most recent races.
Make pool requests to each of the open races.

"""

def get_latest_races():
    url = 'https://service.tvg.com/graph/v2/query'
    resp = requests.post(url, data=json.dumps(tvg_requests.getRacesMtpStatus_payload))
    resp = json.loads(resp.text)
    return [(r['trackCode'], r['number']) for r in resp['data']['mtpRaces'] if r['mtp'] <= 5]
def poll_data(latest_races):
    for track_id, race_number in latest_races:
        url = 'https://service.tvg.com/graph/v2/query'
        resp = requests.post(url, data=json.dumps(tvg_requests.getRaceProgram_payload(track_id, race_number)))
        resp = json.loads(resp.text)
        race = resp['data']['race']

        win_id = -1
        for rp in race['racePools']:
            if rp['wagerType']['name'] == 'Win':
                win_id = rp['wagerType']['id']
                break
        
        if win_id != -1:
            horse_pools = {}
            for bi in race['bettingInterests']:
                for bi_pool in bi['biPools']:
                    if bi_pool['wagerType']['id'] == win_id:
                        horse_pools[bi['biNumber']] = bi_pool['poolRunnersData'][0]['amount']

            print(track_id, race_number)
            print(horse_pools)

def time_padded_run(function, seconds):
    start_time = dt.datetime.now()
    function()
    while dt.datetime.now() - start_time <= dt.timedelta(seconds=seconds):
        pass

def cycle():

    latest_races = get_latest_races()
    print('latest races:', latest_races)

    for i in range(12):
        time_padded_run(poll_data(latest_races), 5)

def main():
    for i in range(10):
        time_padded_run(cycle(), 60)

if __name__ == "__main__":
    main()
