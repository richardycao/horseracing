import os
import datetime as dt
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

def get_row(path, csv_writer):
    path_parts = path.split('/')
    race_number = path_parts[-1]
    track_id = path_parts[-2]
    date = path_parts[-3]
    race_dt = dt.datetime.strptime(date, '%Y-%m-%d')

    details = pd.read_csv(f'{path}/details.csv')
    dist_to_meters = {'f': 201.168,
                      'mtr': 1,     # mtr (meter) comes before m (mile) in search
                      'm': 1609.34,
                      'y': 0.9144}
    # details.loc[0,'distance'] = details.loc[0,'distance'] * dist_to_meters[details.loc[0,'distance_unit'].lower()]
    details = details[['distance','distance_unit','purse','surface_name','race_type_code','race_class']]
    csv_writer.writerow(details.loc[0])

def main(output_file, start_str, end_str):
    start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
    output = StringIO()
    csv_writer = writer(output)

    for path, subdir, files in tqdm(os.walk("../network_read/hist_data")):
        if len(files) > 0:
            if 'details.csv' in files:
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
    main(args[0], args[1], args[2])