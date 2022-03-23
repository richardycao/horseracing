from os import listdir
from os.path import isfile, join
import pandas as pd
from tqdm import tqdm
from io import StringIO
from csv import writer
import datetime as dt

start_date = dt.datetime(2022,3,21,0,0,0)
end_date = dt.datetime(2022,3,23,0,0,0)

#################################

def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

per_horse_columns = [
    'horse_number','runner_odds','morning_odds','horse_name','horse_age','horse_gender','horse_siredam','trainer',
    'horse_med','horse_weight','jockey','horse_power_rating','horse_wins/starts','horse_days_off','horse_avg_speed',
    'horse_avg_distance','horse_high_speed','horse_avg_class','horse_last_class','horse_num_races','early','middle',
    'finish','jockey_trainer_starts','jockey_trainer_1st','jockey_trainer_2nd','jockey_trainer_3rd'
]

horse1_cols = [c+'_1' for c in per_horse_columns]
horse2_cols = [c+'_2' for c in per_horse_columns]

csv_columns_row = [
    'date','time','race_distance','race_type','race_class','surface_name','default_condition',
    *horse1_cols, *horse2_cols, 'result'
]

path = '../../scrape/results'
dates = [f for f in listdir(path) if not isfile(join(path, f))]
output = StringIO()
csv_writer = writer(output)

csv_writer.writerow(csv_columns_row)

races = []
for d in dates:
    if time_in_range(start_date, end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
        races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

for r in tqdm(races):
    csvs = [c for c in listdir(r) if isfile(join(r, c))]

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
                csv_writer.writerow(row)
output.seek(0)
df = pd.read_csv(output)
df.to_csv('raw_test_data.csv', index=False)