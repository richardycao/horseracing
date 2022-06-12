import os
import datetime as dt
import numpy as np
import pandas as pd
from io import StringIO
from csv import writer
from tqdm import tqdm
import json
import sys
import utils

def to_float(x):
    try:
        return float(x)
    except:
        return None

def extract_dict(dict_str):
    try:
        return json.loads(dict_str)
    except:
        return None

def get_row(path, csv_writer, takeouts, horse_limit=8, mode='not_exact', use_missing='False'):
    path_parts = path.split('/')
    race_number = path_parts[-1]
    track_id = path_parts[-2]
    date = path_parts[-3]
    race_dt = dt.datetime.strptime(date, '%Y-%m-%d')

    # remove later
    # if track_id != 'WBS' or race_number != '1':
    #     return

    details = pd.read_csv(f'{path}/static_race.csv')
    bis = pd.read_csv(f'{path}/static_bi.csv')
    live = pd.read_csv(f'{path}/live.csv')
    live['datetime'] = live['datetime'].apply(lambda x: dt.datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"))

    bis = bis[bis['scratched'] == False]
    not_scratched_idxs = bis[bis['scratched'] == False].index.tolist()
    live = live.iloc[:, np.array([-1]+ not_scratched_idxs)+2].copy() # -1 is datetime
    num_horses = bis.shape[0]

    if mode == 'exact':
        if bis.shape[0] != horse_limit:
            return
    else:
        if bis.shape[0] > horse_limit:
            return
    check_for_nans = ['powerRating','daysOff','horseWins','horseStarts','avgClassRating','highSpeed','avgSpeed','lastClassRating',
                    'avgDistance','numRaces','early','middle','finish','starts','wins','places','shows','finishPosition',
                    ]
    if use_missing == 'False':
        for col in check_for_nans:
            if bis[col].isna().sum() != 0:
                return
    missing_count = 0
    if use_missing == 'Some':
        for col in check_for_nans:
            missing_count += bis[col].isna().sum()
        if missing_count > num_horses:
            return
    bis.loc[:,'age'] = race_dt.year - bis.loc[:,'birthday']
    bis.loc[:,'winPayoff'] = bis.loc[:,'winPayoff'] / bis.loc[:,'betAmount']
    bis.loc[:,'placePayoff'] = bis.loc[:,'placePayoff'] / bis.loc[:,'betAmount']
    bis.loc[:,'showPayoff'] = bis.loc[:,'showPayoff'] / bis.loc[:,'betAmount']
    to_keep = [
            'horseName','jockey','trainer','owner','weight','sire','damSire','dam','age','sex','powerRating',
            'daysOff','horseWins','horseStarts','avgClassRating','highSpeed','avgSpeed','lastClassRating','avgDistance',
            'numRaces','early','middle','finish','starts','wins','places','shows',
            'finishPosition']
    bis = bis[to_keep]

    # print(f'live:\n{live.columns}')
    pools = pd.DataFrame.from_dict([extract_dict(d) for d in live.iloc[-1,1:].tolist()])
    if 'Win' not in pools.columns:
        return
    # pools = pools.iloc[not_scratched_idxs,:]
    # print(f'pools:\n{pools}')
    
    omega = pools['Win'].sum()
    takeout_row = takeouts[takeouts.iloc[:,0] == track_id]
    if takeout_row.shape[0] == 0:
        return
    s = 1 - takeout_row.iloc[0,1]
    winning_row = bis[bis['finishPosition'] == 1]
    if winning_row.shape[0] != 1:
        return
    winning_index = winning_row.index[0]
    # print(f'winning row:\n{winning_row}')
    # print(f'winning index: {winning_index}')

    race_end_idx = live.shape[0] - 1
    while race_end_idx > 0:
        inequality = np.sum((live.iloc[race_end_idx,1:] != live.iloc[race_end_idx-1,1:])*1)
        if inequality != 0:
            break
        race_end_idx -= 1
    # print(f'race_end_idx: {race_end_idx}')
    live = live.iloc[:race_end_idx,:]
    if live.shape[0] == 0:
        # print('live is too small.')
        return
    live_after_delay = live[live['datetime'] > live['datetime'][0] + dt.timedelta(minutes=5, seconds=0)]
    if live_after_delay.shape[0] == 0:
        # print('delay is after the end of the race.')
        return

    # print(f'pools again:\n{pools}')
    # print(f'pools win:\n{pools["Win"]}')
    bis['omega'] = pools['Win'].tolist()
    bis['odds'] = (omega*s - bis['omega']) / bis['omega']

    # print(f"bis omega: {bis['omega']}")
    # print(f"bis odds: {bis['odds']}")

    omega_rt_i_list = [ns for ns in [extract_dict(d).get('Win', 0) for d in live_after_delay.iloc[0,1:].to_list()]]
    omega_rt = np.sum(omega_rt_i_list)
    bis['omega_rt'] = omega_rt_i_list
    bis['odds_rt'] = (omega_rt*s - bis['omega_rt']) / bis['omega_rt']

    # print(f"bis omega rt: {bis['omega_rt']}")
    # print(f"bis odds rt: {bis['odds_rt']}")

    dist_to_meters = {'f': 201.168,
                      'mtr': 1,     # mtr (meter) comes before m (mile) in search
                      'm': 1609.34,
                      'y': 0.9144}
    def convert_distance(dist):
        if dist[-1].lower() in ['f','y','m']:
            return dist_to_meters[dist[-1]] * float(dist[:-1])
        return float(dist[:-3])
    details.loc[0,'distance'] = convert_distance(details.loc[0,'distance'])
    details = details[['distance','surface_name','race_type_code','race_class']]
    row = details.iloc[0,:].tolist() + [live_after_delay.iloc[0,:]['datetime']]
    # row = [num_horses, live_after_delay.iloc[0,:]['datetime'], omega, s, winning_index] # index 0 is a a placeholder value. can be replaced with something useful later.
    bis_list = bis.to_dict('records')
    for h in range(horse_limit):
        if h < len(bis_list):
            row.append(json.dumps(bis_list[h]))
        else:
            row.append(None)
    row.extend([num_horses, omega, s, winning_index])
    
    csv_writer.writerow(row)

def main(output_file, start_str, end_str, horse_limit, mode, use_missing):
    start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
    output = StringIO()
    csv_writer = writer(output)
    takeouts = pd.read_csv('takeout_estimates_s3.csv')

    for path, subdir, files in tqdm(os.walk("../../s3_data/v1")):
        if len(files) > 0:
            if 'static_race.csv' in files and 'static_bi.csv' in files and 'live.csv' in files:
                path_parts = path.split('/')
                date = path_parts[-3]
                race_dt = dt.datetime.strptime(date, '%Y-%m-%d')
                if utils.is_time_in_range(start_date, end_date, race_dt):
                    get_row(path, csv_writer, takeouts, int(horse_limit), mode, use_missing)
    output.seek(0)
    df = pd.read_csv(output)
    df.to_csv(f'./{output_file}', index=False)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2], args[3], args[4], args[5])