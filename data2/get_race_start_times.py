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

def get_row(path, csv_writer):
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

    pools = pd.DataFrame.from_dict([extract_dict(d) for d in live.iloc[-1,1:].tolist()])
    if 'Win' not in pools.columns:
        return

    race_end_idx = live.shape[0] - 1
    while race_end_idx > 0:
        inequality = np.sum((live.iloc[race_end_idx,1:] != live.iloc[race_end_idx-1,1:])*1)
        if inequality != 0:
            break
        race_end_idx -= 1

    postTime_file = f'../network_read/hist_data_v2/{date}/{track_id}/{race_number}/details.csv'
    if not os.path.exists(postTime_file):
        return
    details = pd.read_csv(postTime_file)
    post_time = details.iloc[0,1]

    row = [date, track_id, race_number, live.iloc[0, 0], live.iloc[race_end_idx, 0], post_time]
    
    csv_writer.writerow(row)

def main(args):
    output_file, start_str, end_str = args
    start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
    output = StringIO()
    csv_writer = writer(output)
    csv_writer.writerow(['date','track_id','race_number','recording_start_time','race_start_time','post_time'])

    for path, subdir, files in tqdm(os.walk("../../s3_data/v1")):
        if len(files) > 0:
            if 'static_bi.csv' in files and 'live.csv' in files:
                path_parts = path.split('/')
                date = path_parts[-3]
                race_dt = dt.datetime.strptime(date, '%Y-%m-%d')
                if utils.is_time_in_range(start_date, end_date, race_dt):
                    get_row(path, csv_writer)
    output.seek(0)
    df = pd.read_csv(output)
    df.to_csv(f'./{output_file}', index=False)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)