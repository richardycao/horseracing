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
    to_keep = ['winProbability','finishPosition']
    bis = bis[to_keep]

    pools = pd.DataFrame.from_dict([extract_dict(d) for d in live.iloc[-1,1:].tolist()])
    if 'Win' not in pools.columns:
        return
    
    omega = pools['Win'].sum()
    takeout_row = takeouts[takeouts.iloc[:,0] == track_id]
    if takeout_row.shape[0] == 0:
        return
    s = 1 - takeout_row.iloc[0,1]
    winning_row = bis[bis['finishPosition'] == 1]
    if winning_row.shape[0] != 1:
        return
    winning_index = winning_row.index[0]

    race_end_idx = live.shape[0] - 1
    while race_end_idx > 0:
        inequality = np.sum((live.iloc[race_end_idx,1:] != live.iloc[race_end_idx-1,1:])*1)
        if inequality != 0:
            break
        race_end_idx -= 1
    live = live.iloc[:race_end_idx,:]
    if live.shape[0] == 0:
        return
    live_after_delay = live[live['datetime'] > live['datetime'][0] + dt.timedelta(minutes=5, seconds=0)]
    if live_after_delay.shape[0] == 0:
        return

    bis['omega'] = pools['Win'].tolist()
    bis['odds'] = (omega*s - bis['omega']) / bis['omega']

    omega_rt_i_list = [ns for ns in [extract_dict(d).get('Win', 0) for d in live_after_delay.iloc[0,1:].to_list()]]
    omega_rt = np.sum(omega_rt_i_list)
    bis['omega_rt'] = omega_rt_i_list
    bis['odds_rt'] = (omega_rt*s - bis['omega_rt']) / bis['omega_rt']

    row = [live_after_delay.iloc[0,:]['datetime']]
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

    for path, subdir, files in tqdm(os.walk("../../s3_data/v2")):
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