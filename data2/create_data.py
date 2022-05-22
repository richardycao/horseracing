import utils
from os import listdir
from os.path import isfile, join
from tqdm import tqdm
from io import StringIO
from csv import writer
import datetime as dt
import pandas as pd
import sys

class CreateData:
    def __init__(self, output_file, start_str, end_str, mode, use_missing, num_horses):
        self.output_file = output_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
        self.mode = mode
        self.use_missing = use_missing
        self.num_horses = int(num_horses)

        path = '../scrape/results'
        dates = [f for f in listdir(path) if not isfile(join(path, f))]
        self.output = StringIO()
        self.csv_writer = writer(self.output)

        self.races = []
        for d in dates:
            if utils.is_time_in_range(self.start_date, self.end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
                print(d)
                self.races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

    def run(self):
        def on_row(row):
            self.csv_writer.writerow(row)
        
        if self.mode == 'v1':
            csv_columns_row = utils.get_columns(num_horses=self.num_horses)
            self.csv_writer.writerow(csv_columns_row)
            for r in tqdm(self.races):
                s = utils.create_data(r, on_row, num_horses_limit=self.num_horses)
        elif self.mode == 'v2':
            csv_columns_row = utils.get_columns2(num_horses=self.num_horses)
            self.csv_writer.writerow(csv_columns_row)
            for r in tqdm(self.races):
                s = utils.create_data2(r, on_row, num_horses_limit=self.num_horses)
        elif self.mode == 'v3':
            csv_columns_row = utils.get_columns3(num_horses=self.num_horses)
            self.csv_writer.writerow(csv_columns_row)
            for r in tqdm(self.races):
                # print(r)
                s = utils.create_data3(r, on_row, num_horses_limit=self.num_horses, exact=False)
        elif self.mode == 'v4':
            for r in tqdm(self.races):
                s = utils.create_data4(r, on_row, num_horses_limit=self.num_horses, exact=True, use_missing=self.use_missing)
            self.output.seek(0)
            df = pd.read_csv(self.output, header=None)
            df.to_csv(self.output_file, index=False, header=False)
            return
        else:
            print(f'Invalid mode: {self.mode}')
            return

        self.output.seek(0)
        df = pd.read_csv(self.output)
        df.to_csv(self.output_file, index=False)

def main(output_file, start, end, mode, use_missing, num_horses):
    c = CreateData(output_file, start, end, mode, use_missing, num_horses)
    c.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2], args[3], args[4], args[5])
