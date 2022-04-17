import requests
import api
import json
import datetime as dt
import pandas as pd
from pathlib import Path

"""
Periodically make requests to get the most recent races.
Make pool requests to each of the open races.

"""

def safe_get(d: dict, keys: list):
    result = d
    for k in keys:
        if isinstance(result, dict) and k in result:
            result = result[k]
        else:
            return None
    return result
def safe_makedir(path):
    Path(path).mkdir(parents=True, exist_ok=True)
def safe_float(s):
    try:
        return float(s)
    except ValueError:
        return None

def create_date_path(year, month, day):
    return f"{year}-{month}-{day}"
def create_race_path(date, track_id, race_number):
    return f"./{date}/{track_id}/{race_number}"

def get_latest_races(mtp_threshold=5) -> list[tuple]:
    resp = api.getRacesMtpStatus()
    return [(r['trackCode'], r['number']) for r in resp['data']['mtpRaces'] if r['mtp'] <= mtp_threshold]
# Uses on_row to update the live_race_df. Returns value indicating if the results are out yet.
def get_live_race_data(track_id: str, race_number: str, on_row, live_race_df):
    resp = api.getRaceProgram(track_id=track_id, race_number=race_number, live=True)
    race = resp['data']['race']

    # add these to a dataframe first, using a callback.
    # when it's time to close, use the postTime to get the date of the race for directory.
    # record postTime on every sample in the df, but don't use those for the directory.

    post_time_str = safe_get(race, ['postTime'])
    if not post_time_str:
        return
    post_dt = dt.datetime.strptime(post_time_str, '%Y-%m-%dT%H:%M:%SZ')
    results = safe_get(race, ['results'])
    if live_race_df['postTime'][-1] == post_dt and results == None:
        return None, False

    for wt in race['racePools']:
        # name and id indicate the type of wager (win/place/etc.)
        wt['wagerType']['name']
        wt['wagerType']['id']
        # amount is the pool size for this wager on this race.
        wt['amount']
    # live
    race['probables']

    for bi in race['bettingInterests']:
        # Each bip corresponds to a different type of pools: win, show, etc.
        for bip in bi['biPools']:
            # id indicates which type of pools it is.
            bip['wagerType']['id']
            # poolRunnersData has a list of pool sizes for each horse.
            [_ for prd in bip['poolRunnersData']]
        bi['currentOdds']['numerator']
        bi['currentOdds']['denominator'] # denominator is null if the odds isn't a fraction.

    if results != None:
        return post_dt, True
    return None, False

    ####### previous stuff #########
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
        return horse_pools
def get_static_race_data(track_id: str, race_number: str):
    resp = api.getRaceProgram(track_id=track_id, race_number=race_number, live=False)
    race = resp['data']['race']

    post_time_str = safe_get(race, ['postTime'])
    if not post_time_str:
        return
    post_dt = dt.datetime.strptime(post_time_str, '%Y-%m-%dT%H:%M:%SZ')

    # move this outside of this function and pass in the race_path
    # date_path = f"{race_dt.year}-{race_dt.month}-{race_dt.day}"
    # race_path = f"./data/{date_path}/{track_id}/{race_number}"
    # safe_makedir(race_path)

    # race info
    race_data = {
        'datetime': post_dt,
        'distance': safe_get(race, ['distance']),
        'purse': safe_get(race, ['purse']),
        'numRunners': safe_get(race, ['numRunners']),
        'surface_name': safe_get(race, ['surface','name']),
        'surface_defaultCondition': safe_get(race, ['surface','defaultCondition']),
        'race_type_code': safe_get(race, ['type','code']),
        'race_type_name': safe_get(race, ['type','name']),
        'claimingPrice': safe_get(race, ['claimingPrice']),
        'race_class': safe_get(race, ['raceClass','name']),
    }
    # wagerTypes indicates the min and max bet size for each type (win, show, etc.
    # It also shows the default list of bet sizes, but I think I can make my own size anyway.
    # I'm mainly focused on win/place/show, but it doesn't hurt to get all of them.
    for wt in race['wagerTypes']:
        # id, code, and name indicate the type of wager (win/place/show/etc.)
        code = safe_get(wt, ['type','code'])
        race_data[f'{code}_id'] = safe_get(wt, ['type','id'])
        race_data[f'{code}_name'] = safe_get(wt, ['type','name'])
        race_data[f'{code}_maxWagerAmount'] = safe_get(wt, ['maxWagerAmount'])
        race_data[f'{code}_minWagerAmount'] = safe_get(wt, ['minWagerAmount'])
        race_data[f'{code}_wagerAmounts'] = str(safe_get(wt, ['wagerAmounts'])) # this is a list
    # pd.DataFrame(race_data).to_csv(f'{race_path}/static_race_data.csv')

    # horse info
    # get the number of horses
    # only use races without 1A, etc. It's rare enough that excluding them should be fine.
    # actually, that check should be done in get_live_race_data since that creates the first
    # csv for a race.
    num_horses = safe_get(race, ['bettingInterests',''])
    df = pd.DataFrame()



    # Each "betting interest" is a horse or group of horses for a number.
    # e.g. (1 and 1A) or (2)
    for bi in race['bettingInterests']:
        bi['biNumber']
        bi['morningLineOdds']['numerator']
        bi['morningLineOdds']['denominator'] # denominator is null if the odds isn't a fraction.
        for bi_horse in bi['runners']:
            bi_horse['runnerId']
            bi_horse['scratched']
            bi_horse['dob']
            bi_horse['horseName']
            bi_horse['jockey']
            bi_horse['trainer']
            bi_horse['ownerName']
            bi_horse['weight']
            bi_horse['med']
            bi_horse['sire']
            bi_horse['damSire']
            bi_horse['dam']
            bi_horse['age']
            bi_horse['sex']
            bi_horse['handicapping']['snapshot']['powerRating']
            bi_horse['handicapping']['snapshot']['daysOff']
            bi_horse['handicapping']['snapshot']['horseWins']
            bi_horse['handicapping']['snapshot']['horseStarts']
            bi_horse['handicapping']['speedAndClass']['avgClassRating']
            bi_horse['handicapping']['speedAndClass']['highSpeed']
            bi_horse['handicapping']['speedAndClass']['avgSpeed']
            bi_horse['handicapping']['speedAndClass']['lastClassRating']
            bi_horse['handicapping']['speedAndClass']['avgDistance']
            bi_horse['handicapping']['averagePace']['numRaces']
            bi_horse['handicapping']['averagePace']['early']
            bi_horse['handicapping']['averagePace']['middle']
            bi_horse['handicapping']['averagePace']['finish']
            bi_horse['handicapping']['jockeyTrainer']['starts']
            bi_horse['handicapping']['jockeyTrainer']['wins']
            bi_horse['handicapping']['jockeyTrainer']['places']
            bi_horse['handicapping']['jockeyTrainer']['shows']
            bi_horse['handicapping']['jockeyTrainer']['jockeyName']
            bi_horse['handicapping']['jockeyTrainer']['trainerName']

    # race['results']. it's null if the race hasn't finished yet.
    for payoff in race['results']['payoff']:
        payoff['selections']['payoutAmount']
        payoff['selections']['selection'] # even if winner is 1A, the selection is 1 (the betting interest)
        payoff['wagerAmount']
        payoff['wagerType']['id']
        payoff['wagerType']['name']
    for runner in race['results']['runners']:
        runner['betAmount']
        runner['runnerNumber']
        runner['biNumber']
        runner['finishPosition']
        runner['winPayoff']
        runner['placePayoff']
        runner['showPayoff']
        runner['runnerName']

    # Each willpay has a type, indicated by a code. (e.g. daily double (DB), pick 3 (P3))
    # I only have to look out for these wager types: https://www.winningponies.com/help/wager-types.html
    for wp in race['willpays']:
        wp['wagerAmount']
        wp['payOffType']
        # id, code, name indicate the type of bet
        wp['type']['id']
        wp['type']['code']
        wp['type']['name']
        for leg in wp['legResults']:
            leg['legNumber']
            leg['winningBi']
        for bi in wp['payouts']:
            bi['bettingInterestNumber']
            bi['payoutAmount']

    return {}

#### 
def poll_data(latest_races):
    for track_id, race_number in latest_races:
        url = 'https://service.tvg.com/graph/v2/query'
        resp = requests.post(url, data=json.dumps(api.getRaceProgram_payload(track_id, race_number)))
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
    pass
    # latest_races = get_latest_races()
    # print('latest races:', latest_races)

    # for i in range(12):
    #     time_padded_run(poll_data(latest_races), 5)

def main():
    open_races = {}
    while True:
        # Get new races
        races_list = get_latest_races()
        for track_id, race_number in races_list:
            race_id = f"{track_id}-{race_number}"
            if race_id not in open_races:
                open_races[race_id] = pd.DataFrame()

        # Get data for each race
        def on_row(df, row):
            df.loc[0 if pd.isnull(df.index.max()) else df.index.max() + 1] = row
        for race_id, df in open_races.items():
            track_id, race_number = race_id.split('-')
            race_dt, done = get_live_race_data(track_id, race_number, on_row, df)
            if done:
                date_path = create_date_path(race_dt.year, race_dt.month, race_dt.day)
                race_path = create_race_path(date_path, track_id, race_number)
                safe_makedir(race_path)
                # write the df to race_path.
                df.to_csv(f"{race_path}/live.csv")
                # call get_static_race_data and save that to race_path too.
                get_static_race_data(track_id, race_number, race_path)
                # remove the race_id from open races.
                open_races.pop(race_id, None)
        

    # resp = get_race_program('TAM','5')
    # print(resp)
    # for i in range(10):
    #     time_padded_run(cycle(), 60)

if __name__ == "__main__":
    main()
