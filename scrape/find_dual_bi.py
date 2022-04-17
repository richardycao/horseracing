from os import listdir
from os.path import isfile, join
import pandas as pd
from tqdm import tqdm

path = '../scrape/results'
dates = [f for f in listdir(path) if not isfile(join(path, f))]

races = []
for d in dates:
    races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

for r in races:
    csvs = [c for c in listdir(r) if isfile(join(r, c))]
    if 'results.csv' not in csvs:
        continue
    
    results = pd.read_csv(f'{r}/results.csv')
    if '1A' in results['horse number'].to_list():
        print(r)
