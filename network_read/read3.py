import api
import datetime as dt
import pandas as pd
from pathlib import Path
import enum
import json
from io import StringIO  # python3 (or BytesIO for python2)
import boto3
import os

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
def create_date_path(race_dt):
    return race_dt.strftime('%Y-%m-%d')
def create_race_path(date, track_id, race_number):
    return f"v1/{date}/{track_id}/{race_number}"
def should_skip_race(race):
    # Checks if race has 1A
    bis = safe_get(race, ['bettingInterests'])
    if bis == None:
        return True
    if bis != None:
        for bi in bis:
            if len(bi['runners']) > 1:
                return True
    return False
def err(msg, track_id, race_number):
    print(f'    Error on {track_id}-{race_number}: {msg}')
def df_to_s3(s3, path, df):
    bucket = 'richardycao-horseracing'
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    if 'AWS_ACCESS_KEY' not in os.environ or 'AWS_SECRET_ACCESS_KEY' not in os.environ:
        print('    Error: AWS credentials not found in environment variables.')
        exit(1)
    s3.Object(bucket, path).put(Body=csv_buffer.getvalue())

def get_latest_races(mtp_threshold=5):
    resp = api.getRacesMtpStatus()
    if resp == None:
        return None
    return [(r['trackCode'], r['number']) for r in resp['data']['mtpRaces'] if r['mtp'] <= mtp_threshold]

class RaceStatus(enum.Enum):
    open = 1
    closed = 2
    skip = 3
# Uses on_row to update the open_race. Returns value indicating if the results are out yet.
def get_live_race_data(track_id: str, race_number: str, open_race):
    resp = api.getRaceProgram(track_id=track_id, race_number=race_number, live=True)
    if resp == None:
        err('getRaceProgram failed.', track_id, race_number)
        return None, RaceStatus.open
    race = safe_get(resp, ['data','race'])
    if race == None:
        err('race is missing.', track_id, race_number)
        return None, RaceStatus.open
    if should_skip_race(race):
        err('race has 1A. skipping.', track_id, race_number)
        return None, RaceStatus.skip

    row = {}
    row['datetime'] = [dt.datetime.now()]

    wagerType_limits = set(['Win','Place','Show'])
    wagerType_id_name = {}
    wagerTypes = safe_get(race, ['wagerTypes'])
    if wagerTypes == None:
        err('wager types is missing.', track_id, race_number)
        return None, RaceStatus.open
    for wt in race['wagerTypes']:
        # Only do traditional bets, since the exotic ones have low probability so it's
        # going to be hard to test them in simulation.
        name = safe_get(wt, ['type','name'])
        if name == None:
            err('wager type name is missing.', track_id, race_number)
            continue
        if name in wagerType_limits:
            id = safe_get(wt, ['type','id'])
            if id == None:
                err('wager type id is missing.', track_id, race_number)
                continue
            wagerType_id_name[wt['type']['id']] = name

    # Don't need pool amounts if we can calculate that from race['bettingInterests']
    # for wt in race['racePools']:
    #     id = wt['wagerType']['id']
    #     row[f'{wagerType_id_name[id]}_pool_size'] = wt['amount']
    bettingInterests = safe_get(race, ['bettingInterests'])
    if not isinstance(bettingInterests, list):
        err("betting interests is not a list.", track_id, race_number)
        return None, RaceStatus.open
    if bettingInterests == None:
        err("betting interests is missing.", track_id, race_number)
        return None, RaceStatus.open
    for bi in bettingInterests:
        bi_num = safe_get(bi, ['biNumber'])
        if bi_num == None:
            err('biNumber is missing.', track_id, race_number)
            return None, RaceStatus.open
        biPools = safe_get(bi, ['biPools'])
        if biPools == None:
            err('missing biPools.', track_id, race_number)
            return None, RaceStatus.open

        bi_data = [
            ('odds_numerator', safe_get(bi, ['currentOdds','numerator'])),
            ('odds_denominator', safe_get(bi, ['currentOdds','denominator'])),
            # Each bip corresponds to a different type of pools: win, show, etc.
            # poolRunnersData has a list of pool sizes for each horse.
            *[(wagerType_id_name[bip['wagerType']['id']], bip['poolRunnersData'][0]['amount']) for bip in bi['biPools'] if safe_get(bip, ['wagerType','id']) in wagerType_id_name]
        ]
        row[f'bi{bi_num}'] = [json.dumps(dict(bi_data))]

    # Don't need probables if I'm only using win/place/show.
    # race['probables']
    # print(f'{track_id} {race_number}')
    # print(row.keys())

    if 'df' not in open_race:
        open_race['df'] = pd.DataFrame(columns=row.keys())
    open_race['df'] = pd.concat([open_race['df'], pd.DataFrame.from_dict(row)], axis=0)

    if race['results'] != None:
        post_time_str = safe_get(race, ['postTime'])
        if post_time_str == None:
            err('postTime is missing.', track_id, race_number)
            return dt.datetime.now(), RaceStatus.closed
        post_dt = dt.datetime.strptime(post_time_str, '%Y-%m-%dT%H:%M:%SZ')
        return post_dt, RaceStatus.closed
    return None, RaceStatus.open

def get_static_race_data(track_id: str, race_number: str, race_path: str, s3):
    resp = api.getRaceProgram(track_id=track_id, race_number=race_number, live=False)
    if resp == None:
        err('static getRaceProgram failed.', track_id, race_number)
        return
    race = safe_get(resp, ['data','race'])
    if race == None:
        err('static race is missing.', track_id, race_number)
        return

    # race info
    race_data = {
        'distance': [safe_get(race, ['distance'])],
        'purse': [safe_get(race, ['purse'])],
        'numRunners': [safe_get(race, ['numRunners'])],
        'surface_name': [safe_get(race, ['surface','name'])],
        'surface_defaultCondition': [safe_get(race, ['surface','defaultCondition'])],
        'race_type_code': [safe_get(race, ['type','code'])],
        'race_type_name': [safe_get(race, ['type','name'])],
        'claimingPrice': [safe_get(race, ['claimingPrice'])],
        'race_class': [safe_get(race, ['raceClass','name'])],
    }
    # wagerTypes indicates the min and max bet size for each type (win, show, etc.
    # It also shows the default list of bet sizes, but I think I can make my own size anyway.
    # I'm mainly focused on win/place/show, but it doesn't hurt to get all of them.
    wagerTypes = safe_get(race, ['wagerTypes'])
    if wagerTypes == None:
        err('static wager types is missing.', track_id, race_number)
        return
    for wt in wagerTypes:
        # id, code, and name indicate the type of wager (win/place/show/etc.)
        code = safe_get(wt, ['type','code'])
        race_data[f'{code}_id'] = [safe_get(wt, ['type','id'])]
        race_data[f'{code}_name'] = [safe_get(wt, ['type','name'])]
        race_data[f'{code}_maxWagerAmount'] = [safe_get(wt, ['maxWagerAmount'])]
        race_data[f'{code}_minWagerAmount'] = [safe_get(wt, ['minWagerAmount'])]
        # race_data[f'{code}_wagerAmounts'] = str([safe_get(wt, ['wagerAmounts'])]) # this is a list
    df_to_s3(s3, f'{race_path}/static_race.csv', pd.DataFrame(race_data))

    # horse info
    # get the number of horses
    # only use races without 1A, etc. It's rare enough that excluding them should be fine.
    # actually, that check should be done in get_live_race_data since that creates the first
    # csv for a race.

    # Each "betting interest" is a horse or group of horses for a number.
    # e.g. (1 and 1A) or (2)
    bis = {}
    bettingInterests = safe_get(race, ['bettingInterests'])
    if not isinstance(bettingInterests, list):
        err("static betting interests is not a list.", track_id, race_number)
        return
    if bettingInterests == None:
        err("static betting interests is missing.", track_id, race_number)
        return
    for bi in bettingInterests:
        biNum = safe_get(bi, ['biNumber'])
        if biNum == None:
            err('static biNumber is missing.', track_id, race_number)
            continue
        if biNum not in bis:
            bis[biNum] = {}
        bis[biNum]['morningLineOdds_numerator'] = safe_get(bi, ['morningLineOdds','numerator'])
        bis[biNum]['morningLineOdds_denominator'] = safe_get(bi, ['morningLineOdds','denominator'])
        biRunners = safe_get(bi, ['runners'])
        if biRunners == None:
            err('static bi runners is missing.', track_id, race_number)
            continue
        for bi_horse in biRunners:
            bis[biNum]['runnerId'] = safe_get(bi_horse, ['runnerId'])
            bis[biNum]['scratched'] = safe_get(bi_horse, ['scratched'])
            bis[biNum]['birthday'] = safe_get(bi_horse, ['dob'])
            bis[biNum]['horseName'] = safe_get(bi_horse, ['horseName'])
            bis[biNum]['jockey'] = safe_get(bi_horse, ['jockey'])
            bis[biNum]['trainer'] = safe_get(bi_horse, ['trainer'])
            bis[biNum]['owner'] = safe_get(bi_horse, ['ownerName'])
            bis[biNum]['weight'] = safe_get(bi_horse, ['weight'])
            bis[biNum]['med'] = safe_get(bi_horse, ['med'])
            bis[biNum]['sire'] = safe_get(bi_horse, ['sire'])
            bis[biNum]['damSire'] = safe_get(bi_horse, ['damSire'])
            bis[biNum]['dam'] = safe_get(bi_horse, ['dam'])
            bis[biNum]['age'] = safe_get(bi_horse, ['age'])
            bis[biNum]['sex'] = safe_get(bi_horse, ['sex'])
            bis[biNum]['powerRating'] = safe_get(bi_horse, ['handicapping','snapshot','powerRating'])
            bis[biNum]['daysOff'] = safe_get(bi_horse, ['handicapping','snapshot','daysOff'])
            bis[biNum]['horseWins'] = safe_get(bi_horse, ['handicapping','snapshot','horseWins'])
            bis[biNum]['horseStarts'] = safe_get(bi_horse, ['handicapping','snapshot','horseStarts'])
            bis[biNum]['avgClassRating'] = safe_get(bi_horse, ['handicapping','speedAndClass','avgClassRating'])
            bis[biNum]['highSpeed'] = safe_get(bi_horse, ['handicapping','speedAndClass','highSpeed'])
            bis[biNum]['avgSpeed'] = safe_get(bi_horse, ['handicapping','speedAndClass','avgSpeed'])
            bis[biNum]['lastClassRating'] = safe_get(bi_horse, ['handicapping','speedAndClass','lastClassRating'])
            bis[biNum]['avgDistance'] = safe_get(bi_horse, ['handicapping','speedAndClass','avgDistance'])
            bis[biNum]['numRaces'] = safe_get(bi_horse, ['handicapping','averagePace','numRaces'])
            bis[biNum]['early'] = safe_get(bi_horse, ['handicapping','averagePace','early'])
            bis[biNum]['middle'] = safe_get(bi_horse, ['handicapping','averagePace','middle'])
            bis[biNum]['finish'] = safe_get(bi_horse, ['handicapping','averagePace','finish'])
            bis[biNum]['starts'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','starts'])
            bis[biNum]['wins'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','wins'])
            bis[biNum]['places'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','places'])
            bis[biNum]['shows'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','shows'])
            bis[biNum]['jockeyName'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','jockeyName'])
            bis[biNum]['trainerName'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','trainerName'])
            break # break since we only take 1 runner for each bi - ignore races with 1As.

    # race['results']. it's null if the race hasn't finished yet.

    # race['results']['payoff'] - skip since it's redundant in race['result']['runners'].
    # for payoff in race['results']['payoff']:
    #     biNum = payoff['selections']['selection']
    #     wagerType = payoff['wagerType']['name']
    #     bis[biNum][f'{wagerType}_payoff'] = payoff['selections']['payoutAmount']
    #     bis[biNum]['wagerAmount'] = payoff['wagerAmount']

    runners = safe_get(race, ['results','runners'])
    if runners == None:
        err('static runners is missing.', track_id, race_number)
        return
    for runner in runners:
        biNum = safe_get(runner, ['biNumber'])
        if biNum == None:
            err('static runner biNumber is missing.', track_id, race_number)
            continue
        bis[biNum]['runnerNumber'] = safe_get(runner, ['runnerNumber'])
        bis[biNum]['runnerName'] = safe_get(runner, ['runnerName'])
        bis[biNum]['finishPosition'] = safe_get(runner, ['finishPosition'])
        bis[biNum]['betAmount'] = safe_get(runner, ['betAmount'])
        bis[biNum]['winPayoff'] = safe_get(runner, ['winPayoff'])
        bis[biNum]['placePayoff'] = safe_get(runner, ['placePayoff'])
        bis[biNum]['showPayoff'] = safe_get(runner, ['showPayoff'])

    # Each willpay has a type, indicated by a code. (e.g. daily double (DB), pick 3 (P3))
    # I only have to look out for these wager types: https://www.winningponies.com/help/wager-types.html
    # leave out willpays for now since it's for exotic bets.
    # for wp in race['willpays']:
    #     wp['wagerAmount']
    #     wp['payOffType']
    #     # id, code, name indicate the type of bet
    #     wp['type']['id']
    #     wp['type']['code']
    #     wp['type']['name']
    #     for leg in wp['legResults']:
    #         leg['legNumber']
    #         leg['winningBi']
    #     for bi in wp['payouts']:
    #         bi['bettingInterestNumber']
    #         bi['payoutAmount']
    df_to_s3(s3, f'{race_path}/static_bi.csv', pd.DataFrame.from_dict(bis, orient='index'))

def main():
    open_races = {}

    s3 = boto3.resource('s3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))

    while True:
        # Get new races
        start_time = dt.datetime.now()

        # need to add a timeout for each race incase it never ggets removed. timeout = 30 minutes, whic is 12*30=360 data points.
        # postTime is when the race starts!!!
        races_list = get_latest_races()
        if races_list == None:
            print("  couldn't find latest races. skipping this cycle.")
            return
        # a race may be removed from this list before results arrive. Need to get results after that.
        did_open_races_change = False
        for track_id, race_number in races_list:
            race_id = f"{track_id}-{race_number}"
            if race_id not in open_races:
                open_races[race_id] = { 'start_time': dt.datetime.now() }
                did_open_races_change = True
        if did_open_races_change:
            print(open_races.keys())

        # Get data for each race
        races_to_remove = []
        for race_id in open_races.keys():
            track_id, race_number = race_id.split('-')
            race_dt, status = get_live_race_data(track_id, race_number, open_races[race_id])
            # print(race_id, open_races[race_id])
            if status == RaceStatus.skip:
                races_to_remove.append(race_id)
                print(f'  skipping race {track_id} {race_number}')
            elif dt.datetime.now() - open_races[race_id]['start_time'] > dt.timedelta(minutes=30):
                races_to_remove.append(race_id)
                print(f'  race {track_id} {race_number} has timed out. skipping.')
            elif status == RaceStatus.closed:
                date_path = create_date_path(race_dt)
                race_path = create_race_path(date_path, track_id, race_number)
                df_to_s3(s3, f"{race_path}/live.csv", open_races[race_id]['df'])
                # call get_static_race_data and save that to race_path too.
                get_static_race_data(track_id, race_number, race_path, s3)
                # remove the race_id from open races.
                races_to_remove.append(race_id)
                print(f'  closing race {track_id} {race_number}')
        for race_id in races_to_remove:
            open_races.pop(race_id, None)
        while dt.datetime.now() - start_time <= dt.timedelta(seconds=15):
            pass

if __name__ == "__main__":
    main()
