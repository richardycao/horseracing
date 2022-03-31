import utils
from os import listdir
from os.path import isfile, join
from tqdm import tqdm
from io import StringIO
from csv import writer
import datetime as dt
import pandas as pd
import sys

class EstimateTakeouts:
    def __init__(self, output_file, start_str, end_str):
        self.output_file = output_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")

        path = '../scrape/results'
        dates = [f for f in listdir(path) if not isfile(join(path, f))]
        self.output = StringIO()
        self.csv_writer = writer(self.output)

        self.csv_writer.writerow(['park', 'takeout_hat'])

        self.races = []
        for d in dates:
            if utils.time_in_range(self.start_date, self.end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
                print(d)
                self.races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

    def run(self):
        def on_row(row):
            self.csv_writer.writerow(row)

        for r in tqdm(self.races):
            present = utils.are_all_csvs_present(r)
            if not present:
                return
            
            results = utils.get_results_df(r)
            pools = utils.get_pools_df(r)

            park = utils.get_park_name(r)

            w = float(results['win'][0])
            winning_horse_number = results['horse number'][0]
            h0 = pools[pools.iloc[:,0] == int(utils.horse_number_digits_only(winning_horse_number))-1]['win']
            if len(h0) == 0:
                continue
            h0 = h0.values[0]
            pool = pools['win'].sum()

            estimated_takeout = 1 - w*h0/(2*pool)

            on_row([park, estimated_takeout])

        self.output.seek(0)
        et = pd.read_csv(self.output)

        df = pd.concat([et.groupby('park').count(), et.groupby('park').median()], axis=1)
        df.columns = ['count', 'takeout']
        df = df.sort_values('takeout')

        df.to_csv(self.output_file, index=False)

def main(output_file, start, end):
    c = EstimateTakeouts(output_file, start, end)
    c.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2])
