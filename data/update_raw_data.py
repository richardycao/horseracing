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
    def __init__(self, output_file, start_str, end_str):
        self.output_file = output_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")

        path = '../scrape/results'
        dates = [f for f in listdir(path) if not isfile(join(path, f))]

        self.races = []
        for d in dates:
            if utils.time_in_range(self.start_date, self.end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
                print(d)
                self.races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

    def run(self):
        def on_row(row):
            self.csv_writer.writerow(row)

        with open(self.output_file, 'a') as f:
            self.csv_writer = writer(f)

            for r in tqdm(self.races):
                utils.get_race_data(r, on_row)

def main(output_file, start, end):
    c = CreateRawData(output_file, start, end)
    c.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2])
