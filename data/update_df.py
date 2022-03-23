import csv
import os
from tqdm import tqdm
import pandas as pd

####### Modify here #######

dates = ['2022-03-15']
data_csv = "data_x.csv"

####### Modify above #######

path = '../scrape/results'
races = []
for d in dates:
    races.extend([f'{path}/{d}/{r}' for r in os.listdir(f'{path}/{d}') if not os.path.isfile(os.path.join(f'{path}/{d}', r))])

for r in tqdm(races):
    csvs = [c for c in os.listdir(r) if os.path.isfile(os.path.join(r, c))]

    # Skips races with missing files
    missing_csv = False
    for n in ['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
              'racecard_pace','racecard_jock']:
        if f'{n}.csv' not in csvs:
            missing_csv = True
    if missing_csv:
        continue

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
                with open(data_csv, 'a') as f:
                    writer = csv.writer(f)
                    writer.writerow(row)