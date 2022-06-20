from cProfile import run
import api
import os
import datetime as dt
import numpy as np
import pandas as pd
import json
from collections import defaultdict
from tqdm import tqdm
import math

def safe_get(d: dict, keys: list):
    result = d
    for k in keys:
        if isinstance(result, dict) and k in result:
            result = result[k]
        else:
            return None
    return result
def safe_float(s):
    try:
        return float(s)
    except ValueError:
        return None
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

def get_latest_races(mtp_threshold=5):
    resp = api.getRacesMtpStatus()
    if resp == None:
        return None
    return [(r['trackCode'], r['number']) for r in resp['data']['mtpRaces'] if r['mtp'] <= mtp_threshold]

# Uses on_row to update the open_race. Returns value indicating if the results are out yet.
def get_live_data(track_id: str, race_number: str):
    resp = api.getRaceProgram(track_id=track_id, race_number=race_number, live=True)
    if resp == None:
        err('getRaceProgram failed.', track_id, race_number)
        return None, None, False
    race = safe_get(resp, ['data','race'])
    if race == None:
        err('race is missing.', track_id, race_number)
        return None, None, False
    if should_skip_race(race):
        err('race has 1A. skipping.', track_id, race_number)
        return None, None, False

    row = {}
    row['datetime'] = [dt.datetime.now()]

    wagerType_limits = set(['Win','Place','Show'])
    wagerType_id_name = {}
    wagerTypes = safe_get(race, ['wagerTypes'])
    if wagerTypes == None:
        err('wager types is missing.', track_id, race_number)
        return None, None, False
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

    bis = {}
    bettingInterests = safe_get(race, ['bettingInterests'])
    if not isinstance(bettingInterests, list):
        err("betting interests is not a list.", track_id, race_number)
        return None, None, False
    if bettingInterests == None:
        err("betting interests is missing.", track_id, race_number)
        return None, None, False
    for bi in bettingInterests:
        bi_num = safe_get(bi, ['biNumber'])
        if bi_num == None:
            err('biNumber is missing.', track_id, race_number)
            return None, None, False
        if bi_num not in bis:
            bis[bi_num] = {}
        biRunners = safe_get(bi, ['runners'])
        if biRunners == None:
            err('static bi runners is missing.', track_id, race_number)
            continue
        for bi_horse in biRunners:
            bis[bi_num]['runnerId'] = safe_get(bi_horse, ['runnerId'])
            bis[bi_num]['scratched'] = safe_get(bi_horse, ['scratched'])
            bis[bi_num]['winProbability'] = safe_get(bi_horse, ['winProbability'])
            break # break since we only take 1 runner for each bi - ignore races with 1As.
        biPools = safe_get(bi, ['biPools'])
        if biPools == None:
            err('missing biPools.', track_id, race_number)
            return None, None, False

        bi_data = [(wagerType_id_name[bip['wagerType']['id']], bip['poolRunnersData'][0]['amount']) for bip in bi['biPools'] if safe_get(bip, ['wagerType','id']) in wagerType_id_name]
        row[f'bi{bi_num}'] = [json.dumps(dict(bi_data))]

    bis = pd.DataFrame.from_dict(bis, orient='index')
    pools = pd.DataFrame.from_dict(row)
    return bis, pools, True

def pack_data(track_id, bis, live, takeouts, use_missing='Some'):
    horse_limit = 20
    race_dt = dt.datetime.now()

    bis = bis[bis['scratched'] == False].copy()
    not_scratched_idxs = (bis[bis['scratched'] == False].index - 1).tolist()
    num_horses = bis.shape[0]

    to_keep = [
            'runnerId','winProbability'
            ]
    bis = bis[to_keep]
    
    pools = pd.DataFrame.from_dict([extract_dict(d) for i, d in enumerate(live.iloc[0,1:].copy().tolist()) if i in not_scratched_idxs])
    if 'Win' not in pools.columns:
        return None, False
    
    omega = pools['Win'].sum()
    takeout_row = takeouts[takeouts.iloc[:,0] == track_id]
    if takeout_row.shape[0] == 0:
        return None, False
    s = 1 - takeout_row.iloc[0,1]
    
    bis['omega_rt'] = pools['Win'].tolist()

    row = [num_horses, live.iloc[0,:]['datetime'], omega, s, 0] # index 0 is a a placeholder value. can be replaced with something useful later.
    bis_list = bis.to_dict('records')
    for h in range(horse_limit):
        if h < len(bis_list):
            row.append(json.dumps(bis_list[h]))
        else:
            row.append(None)
    return pd.DataFrame([row]), True

def extract_dict(dict_str):
    try:
        return json.loads(dict_str)
    except:
        return None

def get_bis_features_matrix(bi_list, num_horse_features=1):
    matrix = []
    fill_na = np.nan
    for bi_idx, bi in enumerate(bi_list):
        if bi == None:
            matrix.append([0 for _ in range(num_horse_features)])
        else:
            matrix.append([
                bi.get('winProbability',fill_na)
            ][:num_horse_features])
    return matrix, None

def get_bis_features_extras(bi_list):
    row = []
    for bi_idx, bi in enumerate(bi_list):
        if bi == None:
            row.append([0,0])
        else:
            row.append([
                  bi.get('horseName',0),
                  bi.get('omega_rt',0),
                  bi.get('runnerId','-')
            ])
    return row

def preprocess(df, num_horses, num_race_features=5): # features is [num race features, num horses, features per horse]
    num_horses = df.iloc[0,0]
    X = [] # 3d matrix
    extras = [] # 2d matrix

    bi_lists = [extract_dict(d) for d in df.iloc[0,num_race_features:num_race_features+num_horses].to_list()]
    race_matrix, _ = get_bis_features_matrix(bi_lists)
        
    extra = get_bis_features_extras(bi_lists)
    X.append(race_matrix)
    extras.append(extra)
    X = np.array(X)
    X[np.isnan(X)] = 0

    return X, None, extras

def b_star(omega, omega_i, s, p_i):
    if p_i <= omega_i/(s*omega):
        return 0
    root = np.sqrt((omega_i**2)*(s*p_i-1)**2 - (s*p_i-1)*(s*p_i*omega*omega_i - (omega_i**2)) )
    options = [b for b in [-omega_i + root/(s*p_i-1), -omega_i - root/(s*p_i-1)]]
    return np.max(options)

def truncate(number, decimals=0):
    """
    Returns a value truncated to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer.")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more.")
    elif decimals == 0:
        return math.trunc(number)

    factor = 10.0 ** decimals
    return math.trunc(number * factor) / factor

def predict(data_sim, race_id):
  money = [300]

  for r in range(1):
    num_horses = data_sim.iloc[r,0]
    if num_horses > 10:
        return
    s = data_sim.iloc[r,3]
    X_sim, _, extras = preprocess(data_sim.iloc[r:r+1,:], num_horses)
    pools_rt = [[ec[1] for ec in er] for er in extras]
    runnerIds = [[ec[2] for ec in er] for er in extras]
    omega_rt = np.sum(pools_rt[0])
    if omega_rt == 0:
        return
    
    print('\a')
    print(f'\n=============={race_id}============== posted at {dt.datetime.now()}')

    preds = X_sim.reshape((1,-1))
    all_same = True
    for i in preds[0]:
        if i != preds[0][0]:
            all_same = False
    if all_same:
        continue
    bs = np.array([[b_star(omega_rt, pools_rt[preds_r][preds_c], s, preds[preds_r][preds_c]) for preds_c in range(preds.shape[1])] for preds_r in range(preds.shape[0])])
    odds_list = []
    for sim_r in range(X_sim.shape[0]):
      candidates = []
      for i, omega_i in enumerate(pools_rt[sim_r]):
        p_i = preds[sim_r][i]
        if p_i < 0.1:
            continue
        b_i = bs[sim_r][i]
        if b_i > 0:
          b_i = min(b_i, money[-1]*0.01)
          odds_i = s*(omega_rt+b_i) / (omega_i+b_i) - 1
          odds_list.append(odds_i)
          Er_i = odds_i*b_i*p_i - b_i*(1-p_i)
          if odds_i > 1/p_i - 1:
            candidates.append([Er_i, b_i, odds_i, p_i, i, runnerIds[sim_r][i]])
        else:
          odds_list.append(0)

      if len(candidates) > 0:
        sorted_candidates = sorted(candidates, key=lambda x: -x[0])
        
        for sc in sorted_candidates:
            Er, b, odds, p, choice, id = sc
            print(f'Id: {id}, bet amount: {truncate(b,0)}, E[r]: ${truncate(Er,2)}, p: {truncate(p,3)}, odds: {truncate(odds,1)}')

def wait(start_time, duration_seconds):
    while dt.datetime.now() - start_time <= dt.timedelta(seconds=duration_seconds):
        pass

def main():
    delay = 300 # 300
    open_races = {}
    wait_time = 12
    takeouts = pd.read_csv('takeout_estimates_s3.csv')

    while True:
        # Get new races
        start_time = dt.datetime.now()

        # need to add a timeout for each race incase it never ggets removed. timeout = 30 minutes, whic is 12*30=360 data points.
        # postTime is when the race starts!!!
        races_list = get_latest_races()
        if races_list == None:
            print("  couldn't find latest races. skipping this cycle.")
            wait(start_time, wait_time)
            continue
        # a race may be removed from this list before results arrive. Need to get results after that.
        did_open_races_change = False
        for track_id, race_number in races_list:
            race_id = f"{track_id}-{race_number}"
            if race_id not in open_races:
                open_races[race_id] = { 'start_time': dt.datetime.now(), 'end_time': None }
                did_open_races_change = True
        if did_open_races_change:
            print(open_races.keys())

        # Get data for each race
        races_to_remove = []
        for race_id in open_races.keys():
            if dt.datetime.now() - open_races[race_id]['start_time'] < dt.timedelta(seconds=delay):
                continue
            if open_races[race_id]['end_time'] != None and dt.datetime.now() - open_races[race_id]['end_time'] > dt.timedelta(minutes=30):
                races_to_remove.append(race_id)
                continue
            if open_races[race_id]['end_time'] != None:
                continue
            track_id, race_number = race_id.split('-')
            bis, pools, success = get_live_data(track_id, race_number)
            if success:
                dataset, success = pack_data(track_id, bis, pools, takeouts)
                # pd.set_option('display.max_columns', None)
                # print(dataset)
                if success:
                    predict(dataset, race_id)
            open_races[race_id]['end_time'] = dt.datetime.now()
            
        for race_id in races_to_remove:
            open_races.pop(race_id, None)
        wait(start_time, wait_time)

if __name__ == "__main__":
    main()
