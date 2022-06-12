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

def get_row(path):
    path_parts = path.split('/')
    track_id = path_parts[-2]

    bis = pd.read_csv(f'{path}/static_bi.csv')
    live = pd.read_csv(f'{path}/live.csv')

    winning_row = bis[bis['finishPosition'] == 1]
    if winning_row.shape[0] != 1:
        return None, None
    winning_index = winning_row.index[0]
    winPayoff = bis.iloc[winning_index,:]['winPayoff']
    betAmount = bis.iloc[winning_index,:]['betAmount']

    pools = pd.DataFrame.from_dict([extract_dict(d) for d in live.iloc[-1,2:].tolist()])
    if 'Win' not in pools.columns:
        return None, None
    
    omega = pools['Win'].sum()
    omega_i = pools.iloc[winning_index,:]['Win']

    if betAmount == 0 or omega == 0:
        return None, None

    s = ((winPayoff-betAmount)/betAmount*omega_i + omega_i)/omega
    return track_id, 1 - s

def main(output_file, start_str, end_str):
    start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
    output = StringIO()
    csv_writer = writer(output)

    takeout_samples = {}
    for path, subdir, files in tqdm(os.walk("../../s3_data/v1")):
        if len(files) > 0:
            if 'static_race.csv' in files and 'static_bi.csv' in files and 'live.csv' in files:
                path_parts = path.split('/')
                date = path_parts[-3]
                race_dt = dt.datetime.strptime(date, '%Y-%m-%d')
                if utils.is_time_in_range(start_date, end_date, race_dt):
                    track_id, s = get_row(path)
                    if track_id == None or s == None:
                        continue
                    if track_id == 'PAL':
                        print(race_dt)
                    if track_id not in takeout_samples:
                        takeout_samples[track_id] = []
                    takeout_samples[track_id].append(s)
    for track_id, samples in takeout_samples.items():
        row = [track_id, np.median(samples), len(samples)]
        csv_writer.writerow(row)
    output.seek(0)
    df = pd.read_csv(output, header=None)
    df = df.sort_values([0])
    # df.to_csv(f'./{output_file}', index=False)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2])