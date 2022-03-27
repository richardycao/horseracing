from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
import datetime as dt
import re

def get_park_name(r):
    return ' '.join(r.split('/')[-1].split('_')[2:-1])
def get_details_df(r):
    return pd.read_csv(f'{r}/details.csv')
def get_results_df(r):
    results = pd.read_csv(f'{r}/results.csv')
    results['horse number'] = results['horse number'].apply(lambda x: to_str(x)).astype(str)
    return results
def get_racecard_left_df(r):
    racecard_left = pd.read_csv(f'{r}/racecard_left.csv')
    racecard_left = racecard_left[racecard_left['runner odds'] != '-']
    racecard_left['number'] = racecard_left['number'].apply(lambda x: to_str(x)).astype(str)
    return racecard_left
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
def get_pools_df(r):
    def clean_pool_vals(x):
        if isinstance(x, int) or isinstance(x, float) or isinstance(x, np.int64):
            return int(x)
        else:
            return int(x.replace(',',''))

    pools = pd.read_csv(f'{r}/pools.csv')
    for c in pools.columns:
        pools[c] = pools[c].apply(clean_pool_vals)
    pools = pools[pools['win'] != 0]
    return pools
def get_takeout_estimates_df():
    takeouts = pd.read_csv('takeout_estimates.csv')
    return takeouts

def get_columns():
    per_horse_columns = [
        'horse_number','runner_odds','morning_odds','horse_name','horse_age','horse_gender','horse_siredam','trainer',
        'horse_med','horse_weight','jockey','horse_power_rating','horse_wins/starts','horse_days_off','horse_avg_speed',
        'horse_avg_distance','horse_high_speed','horse_avg_class','horse_last_class','horse_num_races','early','middle',
        'finish','jockey_trainer_starts','jockey_trainer_1st','jockey_trainer_2nd','jockey_trainer_3rd'
    ]

    horse1_cols = [c+'_1' for c in per_horse_columns]
    horse2_cols = [c+'_2' for c in per_horse_columns]

    return [
        'date','time','race_distance','race_type','race_class','surface_name','default_condition',
        *horse1_cols, *horse2_cols, 'result'
    ]

def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

def to_str(x):
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        return str(int(x))
    if isinstance(x, str):
        return str(x)
    if isinstance(x, np.int64):
        return str(x)
    return str(x)

def eval_frac(x):
    if isinstance(x, int) or isinstance(x, float) or isinstance(x, np.int64):
        return float(x)
    if "/" in x:
        parts = x.split("/")
        if float(parts[1]) == 0:
            return 0
        return float(parts[0]) / float(parts[1])
    return float(x)

def normalize(x, u, s):
    return (x - u)/s

def get_race_date_time(r):
    race_parts = r.split('/')[-1].split('_')
    d = r.split('/')[3]
    t = ' '.join([p for p in reversed(race_parts[:2])])
    return d, t

def remove_dupes(arr):
    seen = set()
    result = []
    for i in arr:
        if i not in seen:
            result.append(i)
            seen.add(i)
    return result

def horse_number_digits_only(n):
    return n if n[-1].isdigit() else n[:-1]

# returns { '<horse_number>': <ranking 1 to n>, ... }
def get_odds_ranks(r):
    pools = get_pools_df(r)
    pools['horse_number_int'] = pools.index + 1
    sorted_pools = pools.sort_values('win', key=lambda x: -x).reset_index(drop=True)
    sorted_pools['odds_rank'] = sorted_pools.index + 1
    sorted_pools = sorted_pools.sort_values('horse_number_int').reset_index(drop=True)[['horse_number_int','odds_rank']]
    return { sorted_pools['horse_number_int'][i]:sorted_pools['odds_rank'][i] for i in range(sorted_pools.shape[0])}

def get_odds_probs():
    odds_rank_winners = pd.read_csv('odds_ranks.csv')
    odds_probs = (odds_rank_winners['odds_rank'].value_counts() / odds_rank_winners.shape[0]).to_list()
    return odds_probs

# gets group stats of a race
def get_race_stats(r):
    # csvs = [c for c in listdir(r) if isfile(join(r, c))]

    # # Skips races with missing files
    # missing_csv = False
    # for n in ['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
    #           'racecard_pace','racecard_jock','pools']:
    #     if f'{n}.csv' not in csvs:
    #         missing_csv = True
    # if missing_csv:
    #     return

    stats = {}
    park = get_park_name(r)
    results = get_results_df(r)
    left = get_racecard_left_df(r)
    pools = get_pools_df(r)
    takeouts = get_takeout_estimates_df()
    d, t = get_race_date_time(r)

    stats['date'] = d
    stats['time'] = t
    stats['winner'] = results['horse number'][0]
    # stats['winner_odds'] = left[left['number'] == stats['winner']]['runner odds'].iloc[0]
    stats['num_horses'] = left.shape[0]
    stats['pool_size'] = pools['win'].sum()
    stats['takeout'] = takeouts[takeouts['park'] == park]['takeout'].values[0]

    # pool_idx = left[left['number'] == stats['winner']].index[0]
    # stats['winner_pool_size'] = pools.iloc[pool_idx,:]['win']

    # stats['winner_pool_size'] = pools['win'][(int(stats['winner']) if stats['winner'][-1].isdigit() else int(stats['winner'][:-1])) - 1]
    stats['numbers'] = left['number'].to_list()
    nums_only = remove_dupes([n if n[-1].isdigit() else n[:-1] for n in left['number'].to_list()])
    stats['pools_i'] = { str(k):v for k,v in zip(nums_only, pools['win'].to_list()) }

    return stats

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

# converts a race into 1v1s
def get_race_data(r, on_row, mode="train"):
    csvs = [c for c in listdir(r) if isfile(join(r, c))]

    # Skips races with missing files
    missing_csv = False
    for n in ['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
              'racecard_pace','racecard_jock','pools']:
        if f'{n}.csv' not in csvs:
            missing_csv = True
    if missing_csv:
        return

    # Get race time
    d, t = get_race_date_time(r)
    datetime_row = [d, t]

    # Get details
    details = get_details_df(r)
    details_row = details.iloc[0,1:].values.flatten()

    # Get results
    results = get_results_df(r)
    ranked_horse_numbers = set(results['horse number'].values)

    # Racecard
    # 1. Get the list of horses from racecard_left_number.
    # 2. Iterate through all pairs of horses.
    # 3. For each pair, check that at least 1 horse is present in results_horsenumber.
    # 4. For each horse in the pair, get all the values in that list and put it into a row.
    # 5. For each pair, combine race_time_row, details_row, and pair_row into 1 sample in df.
    racecard_left = get_racecard_left_df(r)
    num_horses = racecard_left.shape[0]
    if num_horses != len(ranked_horse_numbers) and mode == 'test':
        return False
    # for horse i and horse j
    for i in range(num_horses):
        for j in range(num_horses):
            i_num = racecard_left.iloc[i]['number']
            j_num = racecard_left.iloc[j]['number']
            if i != j and ((i_num in ranked_horse_numbers or j_num in ranked_horse_numbers) if mode == 'train' else True):
                racecard_summ = get_racecard_summ_df(r)
                racecard_snap = get_racecard_snap_df(r)
                racecard_spee = get_racecard_spee_df(r)
                racecard_pace = get_racecard_pace_df(r)
                racecard_jock = get_racecard_jock_df(r)

                i_row = pd.concat([racecard_left.iloc[i,1:], racecard_summ.iloc[i,1:], racecard_snap.iloc[i,1:], racecard_spee.iloc[i,1:], racecard_pace.iloc[i,1:], racecard_jock.iloc[i,1:]])
                j_row = pd.concat([racecard_left.iloc[j,1:], racecard_summ.iloc[j,1:], racecard_snap.iloc[j,1:], racecard_spee.iloc[j,1:], racecard_pace.iloc[j,1:], racecard_jock.iloc[j,1:]])

                i_rank = results.loc[results['horse number'] == i_num]['ranking'].values[0] if i_num in ranked_horse_numbers else None
                j_rank = results.loc[results['horse number'] == j_num]['ranking'].values[0] if j_num in ranked_horse_numbers else None

                if i_rank == None and j_rank != None:
                    y_row = 1
                elif i_rank != None and j_rank == None:
                    y_row = 0
                elif i_rank != None and j_rank != None:
                    y_row = 0 if i_rank < j_rank else 1

                row = [*datetime_row, *details_row, *i_row, *j_row, *[y_row]]
                on_row(row)
    return True

def preprocess_dataset(data):
    X = data.iloc[:,:-1]
    y = data['result']

    # date, time - convert to cycles
    date_time = (X['date'] + ' ' + X['time']).apply(lambda x: dt.datetime.strptime(
        x, '%Y-%m-%d %I:%M %p'))
    def date_to_nth_day(date):
        new_year_day = pd.Timestamp(year=date.year, month=1, day=1)
        return (date - new_year_day).days + 1
    def nth_day_to_cycle(n):
        radians = n*(2*np.pi)/(365.25)
        return np.cos(radians), np.sin(radians)
    # X['date_cos'] = date_time.apply(lambda x: nth_day_to_cycle(date_to_nth_day(x))[0])
    # X['date_sin'] = date_time.apply(lambda x: nth_day_to_cycle(date_to_nth_day(x))[1])
    def mins_to_cycle(mins):
        radians = mins*(2*np.pi)/(60*24)
        return np.cos(radians), np.sin(radians)
    X['time_cos'] = date_time.apply(lambda x: mins_to_cycle(x.hour*60 + x.minute)[0])
    X['time_sin'] = date_time.apply(lambda x: mins_to_cycle(x.hour*60 + x.minute)[1])
    X = X.drop(['date','time'], axis=1)

    # race_distance - standardize units to meters
    def conv_dist(dist):
        dist_to_meters = {'f': 201.168,
                            'mtr': 1,     # mtr (meter) comes before m (mile) in search
                            'm': 1609.34,
                            'y': 0.9144}
        for k,v in dist_to_meters.items():
            if k in dist:
                return float(dist[:-len(k)]) * v
    X['race_distance_meters'] = X['race_distance'].apply(lambda x: conv_dist(x))
    X = X.drop(['race_distance'], axis=1)

    # race_type - one-hot encode
    def fixed_one_hot(df, column, categories):
        for c in categories:
            df[c] = (df[column] == c)*1
    fixed_one_hot(X, 'race_type', ['Thoroughbred', 'Harness', 'Mixed', 'QuarterHorse', 'Arabian'])
    X = X.drop(['race_type'], axis=1)

    # race_class (TODO)
    X = X.drop(['race_class'], axis=1)

    # surface_name - one-hot encode
    fixed_one_hot(X, 'surface_name', ['Turf', 'Dirt', 'Synthetic', 'Downhill Turf', 'Steeplechase'])
    X = X.drop(['surface_name'], axis=1)

    # default_condition (TODO - see if there's a relationship e.g. good > good to soft > soft)
    X = X.drop(['default_condition'], axis=1)

    for i in ['1','2']:
        # horse number - drop
        X = X.drop(['horse_number_'+i], axis=1)

        # runner odds - convert to decimal
        X['runner_odds_'+i] = X['runner_odds_'+i].apply(lambda x: eval_frac(x))
        # X = X.drop(['runner_odds_'+i], axis=1)

        # morning odds - convert to decimal
        X['morning_odds_'+i] = X['morning_odds_'+i].apply(lambda x: eval_frac(x))
        # X = X.drop(['morning_odds_'+i], axis=1)

        # horse name - drop
        X = X.drop(['horse_name_'+i], axis=1)

        # horse age
        def str_is_float(x):
            try:
                float(x)
                return True
            except ValueError:
                return False
        def str_to_float(x):
            return float(x) if str_is_float(x) else np.nan
        def stf(x):
            return str_to_float((x if isinstance(x, str) else str(x)).replace(' ',''))
        
        # print(X['horse_age_'+i])
        # print(X['horse_age_'+i].apply(stf).apply(lambda x: np.log(x)))
        # print(normalize(X['horse_age_'+i].apply(stf).apply(lambda x: np.log(x)), 1.611, 0.3770))
        X['horse_age_'+i] = normalize(np.log(X['horse_age_'+i].apply(stf)), 1.611, 0.3770).fillna(0)

        # horse gender - a bunch of different "genders" as categories
        fixed_one_hot(X, 'horse_gender_'+i, ['G', 'M', 'F', 'H', 'C', 'R', 'S', 'B'])
        X = X.drop(['horse_gender_'+i], axis=1)

        # horse siredam
        X = X.drop(['horse_siredam_'+i], axis=1)

        # horse med - drop
        X = X.drop(['horse_med_'+i], axis=1)

        # horse trainer (TODO)
        X = X.drop(['trainer_'+i], axis=1)

        # horse weight - convert to int. log everything to reduce the positive skew.
        #                normalize it with hardcoded mean and std. fill na with 0.    
        # weight_ints = X['horse_weight_'+i].apply(lambda x: stf(x))
        X['jockey_weight_'+i] = normalize(np.log(X['horse_weight_'+i].apply(stf)), 4.856, 0.09278).fillna(0)
        X = X.drop(['horse_weight_'+i], axis=1)

        # horse jockey (TODO)
        X = X.drop(['jockey_'+i], axis=1)

        # horse power rating - convert to int. square everything to reduce the negative skew.
        #                      normalize it with hardcoded mean and std. fill na with 0.
        # power_ints = X['horse_power_rating_'+i].apply(lambda x: stf(x))
        X['horse_power_rating_'+i] = normalize(np.power(X['horse_power_rating_'+i].apply(stf), 2), 5016, 1796).fillna(0)

        # horse wins/starts - convert to decimal and get fraction parts. various types of skew reduction.
        #                     normalize it with hardcoded mean and std. fill na with 0.
        def frac_top(x):
            parts = x.replace(' ','').split('/')
            return float(parts[0])
        def frac_bot(x):
            parts = x.replace(' ','').split('/')
            return float(parts[1])
        X['horse_winrate_'+i] = normalize(np.power(X['horse_wins/starts_'+i].apply(lambda x: eval_frac(x)), 1/3), 0.1889, 0.2712).fillna(0)
        X['horse_wins'+i] = normalize(np.power(X['horse_wins/starts_'+i].apply(lambda x: frac_top(x)), 1/3), 0.6365, 0.9833).fillna(0)
        X['horse_starts'+i] = normalize(np.power(X['horse_wins/starts_'+i].apply(lambda x: frac_bot(x)), 1/3), 1.317, 1.802).fillna(0)
        X = X.drop(['horse_wins/starts_'+i], axis=1)

        # horse days off - convert to int. log transform to reduce positive skew.
        #                  normalize with hardcoded mean and std. fill na with 0.
        # days_off_ints = X['horse_days_off_'+i].apply(lambda x: stf(x))
        X['horse_days_off_'+i] = normalize(np.log(X['horse_days_off_'+i].apply(stf)), 2.884, 1.020).fillna(0)

        # avg speed - convert to int. square everything to reduce the negative skew.
        #             normalize it with hardcoded mean and std. fill na with 0.
        # avg_speed_ints = X['horse_avg_speed_'+i].apply(lambda x: stf(x))
        X['horse_avg_speed_'+i] = normalize(np.power(X['horse_avg_speed_'+i].apply(stf), 2), 4935, 1986).fillna(0)

        # avg distance - convert to int. square everything to reduce the negative skew.
        #                normalize it with hardcoded mean and std. fill na with 0.
        # avg_distance_ints = X['horse_avg_distance_'+i].apply(lambda x: stf(x))
        X['horse_avg_distance_'+i] = normalize(np.power(X['horse_avg_distance_'+i].apply(stf), 2), 4242, 2175).fillna(0)

        # high speed - convert to int. square everything to reduce the negative skew.
        #              normalize it with hardcoded mean and std. fill na with 0.
        # high_speed_ints = X['horse_high_speed_'+i].apply(lambda x: stf(x))
        X['horse_high_speed_'+i] = normalize(np.power(X['horse_high_speed_'+i].apply(stf), 2), 5979, 2074).fillna(0)

        # avg class - convert to int, normalize, and fill na with 0.
        # avg_class_ints = X['horse_avg_class_'+i].apply(lambda x: stf(x))
        X['horse_avg_class_'+i] = normalize(X['horse_avg_class_'+i].apply(stf), 77.11, 10.52).fillna(0)

        # last class - convert to int, normalize, and fill na with 0.
        # last_class_ints = X['horse_last_class_'+i].apply(lambda x: stf(x))
        X['horse_last_class_'+i] = normalize(X['horse_last_class_'+i].apply(stf), 78.22, 11.47).fillna(0)

        # num races - as is
        

        # early - unskew all nonzero values, leave the zeros as they are. normalize.
        X['early_'+i] = normalize(np.sqrt(X['early_'+i].apply(stf).replace(0, np.nan)).fillna(0), 1.472, 0.4165)

        # middle - unskew all nonzero values, leave the zeros as they are. normalize.
        X['middle_'+i] = normalize(np.sqrt(X['middle_'+i].apply(stf).replace(0, np.nan)).fillna(0), 2.119, 0.3866)

        # finish - unskew all nonzero values, leave the zeros as they are. normalize.
        X['finish_'+i] = normalize(np.sqrt(X['finish_'+i].apply(stf).replace(0, np.nan)).fillna(0), 2.086, 0.3503)

        # starts - unskew all nonzero values, leave the zeros as they are. normalize.
        X['jockey_trainer_starts_'+i] = normalize(np.log(X['jockey_trainer_starts_'+i].apply(stf).replace(0, np.nan)).fillna(0), 2.927, 1.659)

        # 1st - unskew all nonzero values, leave the zeros as they are. normalize.
        X['jockey_trainer_1st_'+i] = normalize(np.log(X['jockey_trainer_1st_'+i].apply(stf).replace(0, np.nan)).fillna(0), 1.795, 1.386)

        # 2nd - unskew all nonzero values, leave the zeros as they are. normalize.
        X['jockey_trainer_2nd_'+i] = normalize(np.log(X['jockey_trainer_2nd_'+i].apply(stf).replace(0, np.nan)).fillna(0), 1.733, 1.328)

        # 3rd - unskew all nonzero values, leave the zeros as they are. normalize.
        X['jockey_trainer_3rd_'+i] = normalize(np.log(X['jockey_trainer_3rd_'+i].apply(stf).replace(0, np.nan)).fillna(0), 1.661, 1.303)

    return X, y
