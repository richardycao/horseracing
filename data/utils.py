from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
import datetime as dt
import re

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

def get_race_winner(r):
    csvs = [c for c in listdir(r) if isfile(join(r, c))]

    # Skips races with missing files
    missing_csv = False
    for n in ['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
              'racecard_pace','racecard_jock']:
        if f'{n}.csv' not in csvs:
            missing_csv = True
    if missing_csv:
        return

    results = pd.read_csv(f'{r}/results.csv')
    return results['horse number'][0]

def get_race_data(r, on_row):
    csvs = [c for c in listdir(r) if isfile(join(r, c))]

    # Skips races with missing files
    missing_csv = False
    for n in ['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
              'racecard_pace','racecard_jock']:
        if f'{n}.csv' not in csvs:
            missing_csv = True
    if missing_csv:
        return

    # Get race time
    race_parts = r.split('/')[-1].split('_')
    datetime_row = [r.split('/')[3]] + [' '.join([p for p in reversed(race_parts[:2])])]

    # Get details
    details = pd.read_csv(f'{r}/details.csv')
    details_row = details.iloc[0,1:].values.flatten()

    # Get results
    results = pd.read_csv(f'{r}/results.csv')
    ranked_horse_numbers = set(results['horse number'].values)

    # Racecard
    # 1. Get the list of horses from racecard_left_number.
    # 2. Iterate through all pairs of horses.
    # 3. For each pair, check that at least 1 horse is present in results_horsenumber.
    # 4. For each horse in the pair, get all the values in that list and put it into a row.
    # 5. For each pair, combine race_time_row, details_row, and pair_row into 1 sample in df.
    racecard_left = pd.read_csv(f'{r}/racecard_left.csv')
    racecard_left = racecard_left[racecard_left['runner odds'] != '-']
    num_horses = racecard_left.shape[0]
    # for horse i and horse j
    for i in range(num_horses):
        for j in range(num_horses):
            i_num = racecard_left.iloc[i]['number']
            j_num = racecard_left.iloc[j]['number']
            if i != j and (i_num in ranked_horse_numbers or 
                           j_num in ranked_horse_numbers):
                racecard_summ = pd.read_csv(f'{r}/racecard_summ.csv')
                racecard_snap = pd.read_csv(f'{r}/racecard_snap.csv')
                racecard_spee = pd.read_csv(f'{r}/racecard_spee.csv')
                racecard_pace = pd.read_csv(f'{r}/racecard_pace.csv')
                racecard_jock = pd.read_csv(f'{r}/racecard_jock.csv')

                i_row = pd.concat([racecard_left.iloc[i,1:], racecard_summ.iloc[i,1:], racecard_snap.iloc[i,1:], racecard_spee.iloc[i,1:], racecard_pace.iloc[i,1:], racecard_jock.iloc[i,1:]])
                j_row = pd.concat([racecard_left.iloc[j,1:], racecard_summ.iloc[j,1:], racecard_snap.iloc[j,1:], racecard_spee.iloc[j,1:], racecard_pace.iloc[j,1:], racecard_jock.iloc[j,1:]])

                i_rank = results.loc[results['horse number'] == i_num]['ranking'].values[0] if i_num in ranked_horse_numbers else None
                j_rank = results.loc[results['horse number'] == j_num]['ranking'].values[0] if j_num in ranked_horse_numbers else None

                y_row = -1
                if i_rank == None and j_rank != None:
                    y_row = 1
                elif i_rank != None and j_rank == None:
                    y_row = 0
                elif i_rank != None and j_rank != None:
                    y_row = 0 if i_rank < j_rank else 1

                row = [*datetime_row, *details_row, *i_row, *j_row, *[y_row]]
                on_row(row)

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
    X['date_cos'] = date_time.apply(lambda x: nth_day_to_cycle(date_to_nth_day(x))[0])
    X['date_sin'] = date_time.apply(lambda x: nth_day_to_cycle(date_to_nth_day(x))[1])
    def mins_to_cycle(mins):
        radians = mins*(2*np.pi)/(60*24)
        return np.cos(radians), np.sin(radians)
    X['time_cos'] = date_time.apply(lambda x: mins_to_cycle(x.hour*60 + x.minute)[0])
    X['time_sin'] = date_time.apply(lambda x: mins_to_cycle(x.hour*60 + x.minute)[1])
    X.drop(['date','time'], axis=1, inplace=True)

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
    X.drop(['race_distance'], axis=1, inplace=True)

    # race_type - one-hot encode
    def fixed_one_hot(df, column, categories):
        for c in categories:
            df[c] = (df[column] == c)*1
    fixed_one_hot(X, 'race_type', ['Thoroughbred', 'Harness', 'Mixed', 'QuarterHorse', 'Arabian'])
    X.drop(['race_type'], axis=1, inplace=True)

    # race_class (TODO)
    X.drop(['race_class'], axis=1, inplace=True)

    # surface_name - one-hot encode
    fixed_one_hot(X, 'surface_name', ['Turf', 'Dirt', 'Synthetic', 'Downhill Turf', 'Steeplechase'])
    X.drop(['surface_name'], axis=1, inplace=True)

    # default_condition (TODO - see if there's a relationship e.g. good > good to soft > soft)
    X.drop(['default_condition'], axis=1, inplace=True)

    for i in ['1','2']:
        # horse number (TODO - normalize somehow. also has ints and strings.)
        X.drop(['horse_number_'+i], axis=1, inplace=True)

        # runner odds - drop
        X.drop(['runner_odds_'+i], axis=1, inplace=True)

        # morning odds - drop
        X.drop(['morning_odds_'+i], axis=1, inplace=True)

        # horse name (TODO)
        X.drop(['horse_name_'+i], axis=1, inplace=True)

        # horse age - as is

        # horse gender (TODO - a bunch of different "genders")
        X.drop(['horse_gender_'+i], axis=1, inplace=True)

        # horse siredam
        X.drop(['horse_siredam_'+i], axis=1, inplace=True)

        # horse med - drop
        X.drop(['horse_med_'+i], axis=1, inplace=True)

        # horse trainer (TODO)
        X.drop(['trainer_'+i], axis=1, inplace=True)

        # horse weight - convert to int and fill na with mean.
        def str_is_float(x):
            try:
                float(x)
                return True
            except ValueError:
                return False
        def str_to_float(x):
            return float(x) if str_is_float(x) else np.nan
        weight_ints = X['horse_weight_'+i].apply(lambda x: str_to_float((x if isinstance(x, str) else str(x)).replace(' ','')))
        X['jockey_weight_'+i] = weight_ints.fillna(weight_ints.mean())
        X.drop(['horse_weight_'+i], axis=1, inplace=True)

        # horse jockey (TODO)
        X.drop(['jockey_'+i], axis=1, inplace=True)

        # horse power rating - convert to int and fill na with mean.
        power_ints = X['horse_power_rating_'+i].apply(lambda x: str_to_float((x if isinstance(x, str) else str(x)).replace(' ','')))
        X['horse_power_rating_'+i] = power_ints.fillna(power_ints.mean())

        # horse wins/starts (TODO - handle confidence with increasing number of starts)
        X.drop(['horse_wins/starts_'+i], axis=1, inplace=True)

        # horse days off - convert to int and fill na with mean.
        days_off_ints = X['horse_days_off_'+i].apply(lambda x: str_to_float((x if isinstance(x, str) else str(x)).replace(' ','')))
        X['horse_days_off_'+i] = days_off_ints.fillna(days_off_ints.mean())

        # avg speed - convert to int and fill na with mean.
        avg_speed_ints = X['horse_avg_speed_'+i].apply(lambda x: str_to_float((x if isinstance(x, str) else str(x)).replace(' ','')))
        X['horse_avg_speed_'+i] = avg_speed_ints.fillna(avg_speed_ints.mean())

        # avg distance - convert to int and fill na with mean.
        avg_distance_ints = X['horse_avg_distance_'+i].apply(lambda x: str_to_float((x if isinstance(x, str) else str(x)).replace(' ','')))
        X['horse_avg_distance_'+i] = avg_distance_ints.fillna(avg_distance_ints.mean())

        # high speed - convert to int and fill na with mean.
        high_speed_ints = X['horse_high_speed_'+i].apply(lambda x: str_to_float((x if isinstance(x, str) else str(x)).replace(' ','')))
        X['horse_high_speed_'+i] = high_speed_ints.fillna(high_speed_ints.mean())

        # avg class - convert to int and fill na with mean.
        avg_class_ints = X['horse_avg_class_'+i].apply(lambda x: str_to_float((x if isinstance(x, str) else str(x)).replace(' ','')))
        X['horse_avg_class_'+i] = avg_class_ints.fillna(avg_class_ints.mean())

        # last class - convert to int and fill na with mean.
        last_class_ints = X['horse_last_class_'+i].apply(lambda x: str_to_float((x if isinstance(x, str) else str(x)).replace(' ','')))
        X['horse_last_class_'+i] = last_class_ints.fillna(last_class_ints.mean())

        # num races - as is

        # early - as is

        # middle - as is

        # finish - as is

        # starts - as is

        # 1st - as is

        # 2nd - as is

        # 3rd - as is

    return X, y
