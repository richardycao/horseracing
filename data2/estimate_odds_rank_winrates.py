import utils
import os
from tqdm import tqdm
import datetime as dt
import pandas as pd
import sys
from scipy.stats import rankdata
import numpy as np

def main(output_file, start_str, end_str):
    start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")

    horse_limit = 15
    win_counts = np.zeros((horse_limit,horse_limit))
    i = 0
    for path, subdir, files in tqdm(os.walk("../network_read/hist_data")):
        if len(files) > 0:
            if 'bis.csv' in files:
                path_parts = path.split('/')
                date = path_parts[-3]
                race_dt = dt.datetime.strptime(date, '%Y-%m-%d')
                if utils.is_time_in_range(start_date, end_date, race_dt):
                    bis = pd.read_csv(f'{path}/bis.csv')
                    bis = bis[bis['scratched'] == False].reset_index(drop=True)
                    if 1 not in bis['finishPosition'].to_list():
                        continue
                    num_horses = bis.shape[0]
                    if num_horses > horse_limit:
                        continue
                    odds = (bis['currentOdds_numerator'] / bis['currentOdds_denominator'].fillna(1)).to_list()
                    odds_ranks = rankdata(odds, method='ordinal')

                    winner_index = bis[bis['finishPosition'] == 1].index
                    win_counts[num_horses-1, odds_ranks[winner_index] - 1] += 1
    win_counts = win_counts/(np.sum(win_counts, axis=1)+1)[:, np.newaxis]

    df = pd.DataFrame(win_counts)
    df.to_csv(f'./{output_file}', index=False, header=False)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2])
