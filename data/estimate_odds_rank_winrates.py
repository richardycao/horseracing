import utils
from os import listdir
from os.path import isfile, join
from tqdm import tqdm
from io import StringIO
from csv import writer
import datetime as dt
import pandas as pd
import sys

class EstimateOddsRanks:
    def __init__(self, output_file, start_str, end_str):
        self.output_file = output_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")

        path = '../scrape/results'
        dates = [f for f in listdir(path) if not isfile(join(path, f))]
        self.output = StringIO()
        self.csv_writer = writer(self.output)

        self.csv_writer.writerow(['odds_rank','num_horses'])

        self.races = []
        for d in dates:
            if utils.time_in_range(self.start_date, self.end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
                print(d)
                self.races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

    def run(self):
        def on_row(row):
            self.csv_writer.writerow(row)

        for r in tqdm(self.races):
            csvs = [c for c in listdir(r) if isfile(join(r, c))]

            # Skips races with missing files
            missing_csv = False
            for n in ['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
                    'racecard_pace','racecard_jock','pools']:
                if f'{n}.csv' not in csvs:
                    missing_csv = True
            if missing_csv:
                continue
            
            results = utils.get_results_df(r)
            left = utils.get_racecard_left_df(r)
            pools = utils.get_pools_df(r)
            pools['horse_number'] = pools.index + 1

            # for the winning horse, find where it stands in terms of odds.

            winning_horse_number = int(utils.horse_number_digits_only(results['horse number'][0]))
            odds_ranks = utils.get_odds_ranks(r)
            
            if winning_horse_number in odds_ranks:
                on_row([odds_ranks[winning_horse_number], left.shape[0]])

        self.output.seek(0)
        df = pd.read_csv(self.output)

        low, high = 1, 20
        result = pd.DataFrame(columns=[str(i) for i in range(low, high)])
        for i in range(low, high):
            dist = df[df['num_horses']==i]
            probs = (dist.value_counts()/dist.shape[0]).to_list()
            probs = probs + [0]*(high-low - len(probs))
            result.loc[0 if pd.isnull(result.index.max()) else result.index.max() + 1] = probs
        
        result.to_csv(self.output_file, index=False)

def main(output_file, start, end):
    c = EstimateOddsRanks(output_file, start, end)
    c.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2])
