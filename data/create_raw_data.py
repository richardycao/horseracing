import utils
from os import listdir
from os.path import isfile, join
from tqdm import tqdm
from io import StringIO
from csv import writer
import datetime as dt
import pandas as pd
import sys

class CreateRawData:
    def __init__(self, output_file, start_str, end_str, mode):
        self.output_file = output_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
        self.mode = mode

        path = '../scrape/results'
        dates = [f for f in listdir(path) if not isfile(join(path, f))]
        self.output = StringIO()
        self.csv_writer = writer(self.output)

        self.races = []
        for d in dates:
            if utils.time_in_range(self.start_date, self.end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
                print(d)
                self.races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

    def run(self):
        def on_row(row):
            self.csv_writer.writerow(row)
        
        if self.mode == '1v1':
            csv_columns_row = utils.get_columns()
            self.csv_writer.writerow(csv_columns_row)
            for r in tqdm(self.races):
                s = utils.get_race_data(r, on_row, mode='train')
                if not s:
                    continue
        elif self.mode == 'rank':
            csv_columns_row = utils.get_columns_v2()
            self.csv_writer.writerow(csv_columns_row)
            for r in tqdm(self.races):
                # print(r)
                s = utils.get_race_data_v2(r, on_row)
                if not s:
                    continue
        else:
            print(f'Invalid mode: {self.mode}')
            return

        self.output.seek(0)
        df = pd.read_csv(self.output)
        df.to_csv(self.output_file, index=False)

def main(output_file, start, end, mode):
    c = CreateRawData(output_file, start, end, mode)
    c.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2], args[3])
