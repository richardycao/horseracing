import utils
from os import listdir
from os.path import isfile, join
from tqdm import tqdm
from io import StringIO
from csv import writer
import datetime as dt
import pandas as pd
import sys
from scipy.stats import rankdata

class EstimateOddsRanks:
    def __init__(self, output_file, start_str, end_str, mode):
        self.output_file = output_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
        self.mode = mode

        if mode == 'daily':
            path = '../scrape/results'
        elif mode == 'hist':
            path = '../scrape/historical_results'
        dates = [f for f in listdir(path) if not isfile(join(path, f))]
        self.output = StringIO()
        self.csv_writer = writer(self.output)

        self.csv_writer.writerow(['odds_rank','num_horses'])

        self.races = []
        for d in dates:
            if utils.time_in_range(self.start_date, self.end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
                self.races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

    def run(self):
        def on_row(row):
            self.csv_writer.writerow(row)

        for r in tqdm(self.races):
            if self.mode == 'daily':
                present = utils.are_all_csvs_present(r)
                if not present:
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

            elif self.mode == 'hist':
                present = utils.are_historical_csvs_present(r)
                if not present:
                    continue
                results = utils.get_results_df(r)
                left = utils.get_racecard_left_df(r)

                winning_horse = utils.horse_number_digits_only(results['horse number'][0])

                nums_only = utils.remove_dupes([n if n[-1].isdigit() else n[:-1] for n in left['number'].to_list()])
                seen_nums = set()
                unique_horse_nums = [] # get 1 horse for each number. 1,1A,2A,3 becomes 1,2A,3.
                for num in left['number']:
                    digits_only = utils.horse_number_digits_only(num)
                    if digits_only not in seen_nums:
                        unique_horse_nums.append(num)
                        seen_nums.add(digits_only)
                odds_ranks = rankdata(left[left['number'].isin(unique_horse_nums)]['runner odds'].apply(lambda x: -utils.eval_frac(x)).to_numpy())

                if winning_horse in nums_only:
                    on_row([odds_ranks[nums_only.index(winning_horse)], left.shape[0]])

        self.output.seek(0)
        df = pd.read_csv(self.output)

        low, high = 1, 30
        result = pd.DataFrame(columns=[str(i) for i in range(low, high)])
        for i in range(low, high):
            dist = df[df['num_horses']==i]
            probs = (dist.value_counts()/dist.shape[0]).to_list()
            probs = probs + [0]*(high-low - len(probs))
            result.loc[0 if pd.isnull(result.index.max()) else result.index.max() + 1] = probs
        
        result.to_csv(self.output_file, index=False)

def main(output_file, start, end, mode):
    c = EstimateOddsRanks(output_file, start, end, mode)
    c.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2], args[3])
