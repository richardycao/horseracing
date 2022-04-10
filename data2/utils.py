from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
import datetime as dt
import re
from scipy.stats import rankdata

def get_race_date_time(r):
    race_parts = r.split('/')[-1].split('_')
    d = r.split('/')[3]
    t = ' '.join([p for p in reversed(race_parts[:2])])
    return d, t
def get_park_name(r):
    return ' '.join(r.split('/')[-1].split('_')[2:-1])
def get_details_df(r):
    return pd.read_csv(f'{r}/details.csv')
def get_results_df(r):
    results = pd.read_csv(f'{r}/results.csv')
    results['horse number'] = results['horse number'].apply(lambda x: str(x)).astype(str)
    results['horse numeric'] = results['horse number'].apply(lambda x: horse_number_digits_only(x))
    return results
def get_racecard_left_df(r):
    left = pd.read_csv(f'{r}/racecard_left.csv')
    left = left[left['runner odds'] != '-']
    left['number'] = left['number'].apply(lambda x: str(x)).astype(str)
    left['numeric'] = left['number'].apply(lambda x: horse_number_digits_only(x))
    left['runner odds'] = left['runner odds'].apply(lambda x: eval_frac(x))
    left['runner odds rank'] = rankdata(left['runner odds'])
    return left
def get_racecard_summ_df(r):
    return pd.read_csv(f'{r}/racecard_summ.csv')
def get_racecard_snap_df(r):
    return pd.read_csv(f'{r}/racecard_snap.csv')
def get_racecard_spee_df(r):
    return pd.read_csv(f'{r}/racecard_spee.csv')
def get_racecard_pace_df(r):
    return pd.read_csv(f'{r}/racecard_pace.csv')
def get_racecard_jock_df(r):
    return pd.read_csv(f'{r}/racecard_jock.csv')
def get_pools_df(r, hist=False):
    def clean_pool_vals(x):
        if isinstance(x, int) or isinstance(x, float) or isinstance(x, np.int64):
            return int(x)
        else:
            return int(x.replace(',',''))
    if not hist:
        pools = pd.read_csv(f'{r}/pools.csv')
        for c in pools.columns:
            pools[c] = pools[c].apply(clean_pool_vals)
        pools['numeric'] = pools.index + 1
        pools['win_rank'] = rankdata(-pools['win'])
        pools['place_rank'] = rankdata(-pools['place'])
        pools['show_rank'] = rankdata(-pools['show'])
        pools = pools[pools['win'] != 0]
        return pools
    else:
        park = get_park_name(r)
        left = get_racecard_left_df(r)
        takeouts = get_takeout_estimates_df()
        pools = pd.DataFrame()
        pools['numeric'] = uniques(left['numeric'])
        takeout_vals = takeouts[takeouts['park'] == park]['takeout'].values
        takeout = takeout_vals[0] if len(takeout_vals) > 0 else 0.2
        random_pool_size = min(10000*np.exp(np.random.normal()), 100000) # pool_size is lognormal with max of 100k
        seen_nums = set()
        unique_horse_nums = [] # get 1 horse for each number. 1,1A,2A,3 becomes 1,2A,3.
        for num in left['number']:
            digits_only = horse_number_digits_only(num)
            if digits_only not in seen_nums:
                unique_horse_nums.append(num)
                seen_nums.add(digits_only)
        pools['win'] = left[left['number'].isin(unique_horse_nums)]['runner odds'].apply(lambda x: 1/((1-takeout)*(eval_frac(x) + 1))).to_numpy()
        pools['win'] = random_pool_size * pools['win'] / pools['win'].sum()
        pools['win_rank'] = rankdata(-pools['win'])
        return pools
def get_takeout_estimates_df():
    takeouts = pd.read_csv('takeout_estimates.csv')
    return takeouts
def are_all_csvs_present(r):
    csvs = [c for c in listdir(r) if isfile(join(r, c))]
    for n in ['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
              'racecard_pace','racecard_jock','pools']:
        if f'{n}.csv' not in csvs:
            return False
    return True
def are_historical_csvs_present(r):
    csvs = [c for c in listdir(r) if isfile(join(r, c))]
    for n in ['results','racecard_left']:
        if f'{n}.csv' not in csvs:
            return False
    return True

def get_columns():
    per_horse_columns = [
        'horse_number','runner_odds','morning_odds','horse_name','horse_age','horse_gender','horse_siredam','horse_med',
        'trainer','horse_weight','jockey','horse_power_rating','horse_wins/starts','horse_days_off','horse_avg_speed',
        'horse_avg_distance','horse_high_speed','horse_avg_class','horse_last_class','horse_num_races','early','middle',
        'finish','jockey_trainer_starts','jockey_trainer_1st','jockey_trainer_2nd','jockey_trainer_3rd','pool_frac'
    ]

    horse1_cols = [c+'_1' for c in per_horse_columns]
    horse2_cols = [c+'_2' for c in per_horse_columns]

    return [
        'date','time','race_distance','race_type','race_class','surface_name','default_condition',
        *horse1_cols, *horse2_cols, 'result'
    ]

def is_time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
def horse_number_digits_only(n):
    return n if n[-1].isdigit() else n[:-1]
def numerator(x):
        parts = x.replace(' ','').split('/')
        return float(parts[0])
def denominator(x):
    parts = x.replace(' ','').split('/')
    return float(parts[1])
def eval_frac(x):
    if isinstance(x, int) or isinstance(x, float) or isinstance(x, np.int64):
        return float(x)
    if "/" in x:
        parts = x.split("/")
        if float(parts[1]) == 0:
            return 0
        return float(parts[0]) / float(parts[1])
    return float(x)
def uniques(arr):
    seen = set()
    result = []
    for i in arr:
        if i not in seen:
            result.append(i)
            seen.add(i)
    return result
def pad_or_truncate(some_list, target_len, filler_value=0):
    return some_list[:target_len] + [filler_value]*(target_len - len(some_list))

def get_columns(num_horses=9):
    general = ['date','time','s','omega']
    return [*general, *[f'omega_{i}' for i in range(num_horses)],'result']
def create_data(r, on_row, num_horses_limit):
    present = are_all_csvs_present(r)
    if not present:
        return
    d, t = get_race_date_time(r)
    park = get_park_name(r)
    pools = get_pools_df(r)
    if pools.shape[0] > num_horses_limit or pools.shape[0] == 0:
        return
    results = get_results_df(r)
    takeouts = get_takeout_estimates_df()
    takeout_vals = takeouts[takeouts['park'] == park]['takeout'].values
    s = takeout_vals[0] if len(takeout_vals) > 0 else 0.2

    reset_idx_pools = pools.reset_index(drop=True)
    winner_horse_index = reset_idx_pools[reset_idx_pools['numeric'] == int(results['horse numeric'][0])].index[0]
    pool_size = pools['win'].sum()
    omega_i_list = pad_or_truncate(pools['win'].to_list(), num_horses_limit)
    
    on_row([d, t, s, pool_size, *omega_i_list, winner_horse_index])

def get_columns2(num_horses=9):
    general = ['date','time','s','omega']
    return [*general, *[f'horse_{i}' for i in range(num_horses)], 'result']
def create_data2(r, on_row, num_horses_limit):
    present = are_all_csvs_present(r)
    if not present:
        return
    # General
    d, t = get_race_date_time(r)
    park = get_park_name(r)
    pools = get_pools_df(r)
    if pools.shape[0] > num_horses_limit or pools.shape[0] == 0:
        return
    results = get_results_df(r)
    takeouts = get_takeout_estimates_df()
    takeout_vals = takeouts[takeouts['park'] == park]['takeout'].values
    s = (1-takeout_vals[0]) if len(takeout_vals) > 0 else 0.8
    left = get_racecard_left_df(r)

    reset_idx_pools = pools.reset_index(drop=True)
    winner_horse_index = reset_idx_pools[reset_idx_pools['numeric'] == int(results['horse numeric'][0])].index[0]
    pool_size = pools['win'].sum()

    # Per horse
    omega_i_list = pad_or_truncate(pools['win'].to_list(), num_horses_limit)
    odds_i_list = [(s*pool_size - oi)/oi if oi > 0 else 0 for oi in omega_i_list]
    age_i_list = pad_or_truncate(left['age'].to_list(), num_horses_limit)
    horse_i_list = [ {
        'omega_i': h1,
        'odds_i': h2,
        'age_i': h3,
        } for h1, h2, h3 in zip(omega_i_list, odds_i_list, age_i_list)]
    
    on_row([d, t, s, pool_size, *horse_i_list, winner_horse_index])

def get_columns3(num_horses=9):
    general = ['date','time','s','omega']
    return [*general, *[f'horse_{i}' for i in range(num_horses)], 'result']
def create_data3(r, on_row, num_horses_limit, exact=False):
    present = are_all_csvs_present(r)
    if not present:
        return
    # General
    d, t = get_race_date_time(r)
    park = get_park_name(r)
    pools = get_pools_df(r)
    if pools.shape[0] > num_horses_limit or pools.shape[0] == 0:
        return
    if exact and pools.shape[0] != num_horses_limit:
        return
    results = get_results_df(r)
    snap = get_racecard_snap_df(r)
    spee = get_racecard_spee_df(r)
    pace = get_racecard_pace_df(r)
    jock = get_racecard_jock_df(r)
    takeouts = get_takeout_estimates_df()
    takeout_vals = takeouts[takeouts['park'] == park]['takeout'].values
    s = (1-takeout_vals[0]) if len(takeout_vals) > 0 else 0.8
    left = get_racecard_left_df(r)

    reset_idx_pools = pools.reset_index(drop=True)
    winner_horse_index = reset_idx_pools[reset_idx_pools['numeric'] == int(results['horse numeric'][0])].index[0]
    pool_size = pools['win'].sum()

    # Per horse
    """
    exclude:
    omega(pool),odds

    always include:
    morning odds,age,horse wins,horse starts,horse winrate,num races,early,middle,
    finish,jockey starts,1st rate,2nd rate,3rd rate,

    if partially missing, fill with mean of horses in the race. if all missing, fill 
    with universal mean of the dataset:
    power rating,days off,avg speed,avg dist,high speed,avg class,last class.
    """
    omega = pad_or_truncate(pools['win'].to_list(), num_horses_limit)
    odds = [(s*pool_size - oi)/oi if oi > 0 else 0 for oi in omega]

    morning_odds = pad_or_truncate(left['race morning odds'].apply(eval_frac).to_list(), num_horses_limit)
    age = pad_or_truncate(left['age'].to_list(), num_horses_limit)
    # print(snap['wins/starts'].apply(numerator))
    wins = pad_or_truncate(snap['wins/starts'].apply(numerator).to_list(), num_horses_limit)
    starts = pad_or_truncate(snap['wins/starts'].apply(denominator).to_list(), num_horses_limit)
    winrate = pad_or_truncate(snap['wins/starts'].apply(eval_frac).to_list(), num_horses_limit)
    num_races = pad_or_truncate(pace['num races'].to_list(), num_horses_limit)
    early = pad_or_truncate(pace['early'].to_list(), num_horses_limit)
    middle = pad_or_truncate(pace['middle'].to_list(), num_horses_limit)
    finish = pad_or_truncate(pace['finish'].to_list(), num_horses_limit)
    jockey_starts = pad_or_truncate(jock['starts'].to_list(), num_horses_limit)
    jockey_1st_rate = pad_or_truncate(jock['1st'].to_list(), num_horses_limit)
    jockey_2nd_rate = pad_or_truncate(jock['2nd'].to_list(), num_horses_limit)
    jockey_3rd_rate = pad_or_truncate(jock['3rd'].to_list(), num_horses_limit)

    power_rating = pad_or_truncate(snap['power rating'].replace('- ', np.nan).to_list(), num_horses_limit)
    days_off = pad_or_truncate(snap['days off'].replace('- ', np.nan).to_list(), num_horses_limit)
    avg_speed = pad_or_truncate(spee['avg speed'].replace('- ', np.nan).to_list(), num_horses_limit)
    avg_distance = pad_or_truncate(spee['avg distance'].replace('- ', np.nan).to_list(), num_horses_limit)
    high_speed = pad_or_truncate(spee['high speed'].replace('- ', np.nan).to_list(), num_horses_limit)
    avg_class = pad_or_truncate(spee['avg class'].replace('- ', np.nan).to_list(), num_horses_limit)
    last_class = pad_or_truncate(spee['last class'].replace('- ', np.nan).to_list(), num_horses_limit)

    labels = ['omega','odds',
              ###
              'morning_odds','age','wins','starts','winrate','num_races','early','middle','finish',
              'jockey_starts','jockey_1st_rate','jockey_2nd_rate','jockey_3rd_rate',
              ###
              'power_rating','days_off','avg_speed','avg_distance','high_speed','avg_class','last_class']

    horse_i_list = [ 
        {
            labels[i]: f for i, f in enumerate(features)
        } for features in zip(
            omega,odds,
            ###
            morning_odds,age,wins,starts,winrate,num_races,early,middle,finish,
            jockey_starts,jockey_1st_rate,jockey_2nd_rate,jockey_3rd_rate,
            ###
            power_rating,days_off,avg_speed,avg_distance,high_speed,avg_class,last_class
        )]
    
    on_row([d, t, s, pool_size, *horse_i_list, winner_horse_index])
