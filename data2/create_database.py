from sqlalchemy import create_engine, Table, Column, MetaData, Integer, String, Float, DateTime
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

def get_row(path, csv_writer, takeouts, horse_limit=8, mode='not_exact', use_missing='False'):
    path_parts = path.split('/')
    race_number = path_parts[-1]
    track_id = path_parts[-2]
    date = path_parts[-3]
    race_dt = dt.datetime.strptime(date, '%Y-%m-%d')

    details = pd.read_csv(f'{path}/details.csv')
    bis = pd.read_csv(f'{path}/bis.csv')

    bis = bis[bis['scratched'] == False]
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
    else:
        pass
        # this if statement doesn't actually change anything for some reason.
        # if bis['avgClassRating'].isna().sum() != 0:
        #     return
    bis.loc[:,'age'] = race_dt.year - bis.loc[:,'birthday']
    bis.loc[:,'winPayoff'] = bis.loc[:,'winPayoff'] / bis.loc[:,'betAmount']
    bis.loc[:,'placePayoff'] = bis.loc[:,'placePayoff'] / bis.loc[:,'betAmount']
    bis.loc[:,'showPayoff'] = bis.loc[:,'showPayoff'] / bis.loc[:,'betAmount']
    bis.loc[:,'currentOdds_denominator'] = bis.loc[:,'currentOdds_denominator'].replace(np.nan, 1)
    bis.loc[:,'odds'] = (bis.loc[:,'currentOdds_numerator'] / bis.loc[:,'currentOdds_denominator'])
    to_keep = ['runnerId',
            'horseName','jockey','trainer','owner','weight','sire','damSire','dam','age','sex','powerRating',
            'daysOff','horseWins','horseStarts','avgClassRating','highSpeed','avgSpeed','lastClassRating','avgDistance',
            'numRaces','early','middle','finish','starts','wins','places','shows',
            'finishPosition','odds','postRaceReport','accBeatenDistance']
    bis = bis[to_keep]

    dist_to_meters = {'f': 201.168,
                      'mtr': 1,     # mtr (meter) comes before m (mile) in search
                      'm': 1609.34,
                      'y': 0.9144}
    details.loc[0,'distance'] = details.loc[0,'distance'] * dist_to_meters[details.loc[0,'distance_unit'].lower()]
    
    # replacing race_class for s (1-takeout), to predict final odds #
    details = details[['distance','surface_name','race_type_code']]#,'race_class']]
    takeout_row = takeouts[takeouts.iloc[:,0]==track_id]
    s = 0.8
    if takeout_row.shape[0] > 0:
        s = 1 - takeouts[takeouts.iloc[:,0]==track_id].iloc[0,1]
    details.loc[:,'s'] = [s]
    # end of replace #

    details.loc[:,'race_path'] = [path]
    bis_list = bis.to_dict('records')
    for h in range(horse_limit):
        if h < len(bis_list):
            details.loc[0,f'bi{h}'] = json.dumps(bis_list[h])
        else:
            details.loc[0,f'bi{h}'] = None
    csv_writer.writerow(details.loc[0])

def main(output_file, start_str, end_str, horse_limit, mode, use_missing):
    engine = create_engine("postgresql://user:password@localhost:5432/horseracing")
    metadata = MetaData()
    bi_table = Table(
        "betting_interests", metadata,
        Column('id', Integer, primary_key=True),
        Column('race_id', Integer),
        Column('horse_id', Integer),
        Column('jockey', Integer),
        Column('trainer', Integer),
        Column('runnerId', Integer),
        Column('weight', Integer),
        Column('age', Integer),
        Column('powerRating', Float),
        Column('daysOff', Integer),
        Column('horseWins', Integer),
        Column('horseStarts', Integer),
        Column('avgClassRating', Float),
        Column('highSpeed', Float),
        Column('avgSpeed', Float),
        Column('lastClassRating', Float),
        Column('avgDistance', Float),
        Column('numRaces', Integer),
        Column('early', Float),
        Column('middle', Float),
        Column('finish', Float),
        Column('starts', Integer),
        Column('wins', Integer),
        Column('places', Integer),
        Column('shows', Integer),
        Column('finishPosition', Float),
        Column('odds', Float),
        Column('postRaceReport', String),
        Column('accBeatenDistance', Float),
    )
    race_table = Table(
        "races", metadata,
        Column('id', Integer, primary_key=True),
        Column('datetime', DateTime),
        Column('distance', Integer),
        Column('surface_name', String),
        Column('race_type_code', String),
        Column('race_class', String),
        Column('winningTime', Float),
    )
    horse_table = Table(
        "horses", metadata,
        Column('id', Integer, primary_key=True),
        Column('horseName', String),
        Column('owner', String),
        Column('sire', String),
        Column('damSire', String),
        Column('dam', String),
        Column('sex', String),
    )

    start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
    output = StringIO()
    csv_writer = writer(output)
    takeouts = pd.read_csv('takeout_estimates_s3.csv')

    for path, subdir, files in tqdm(os.walk("../network_read/hist_data_v2")):
        if len(files) > 0:
            # each bis+details pair becomes a row
            if 'bis.csv' in files and 'details.csv' in files:
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
