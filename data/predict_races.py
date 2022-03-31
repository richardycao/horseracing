import pandas as pd
import joblib
import sys
import datetime as dt
from os import listdir
from os.path import isfile, join
import utils
from tqdm import tqdm
from collections import defaultdict
import numpy as np
from io import StringIO
from csv import writer

class PredictRaces:
    def __init__(self, model_file, start_str, end_str, avgs, obs, mode):
        self.model_file = model_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
        self.obs_file = obs
        self.mode = mode
        if mode == '1v1' or mode == 'bayes' or mode == 'random':
            self.avgs = pd.read_csv(avgs)
            self.columns = utils.get_columns()
        elif mode == 'rank':
            self.columns = utils.get_columns_v2()

        path = '../scrape/results'
        dates = [f for f in listdir(path) if not isfile(join(path, f))]
        self.races = []
        self.skipped_races = 0
        for d in dates:
            if utils.time_in_range(self.start_date, self.end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
                print(d)
                self.races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

        self.output = StringIO()
        self.csv_writer = writer(self.output)
        self.csv_writer.writerow(['datetime','winner','num_horses','pool_size','takeout','scores','pools_i'])

        self.required_files = set(['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
                                    'racecard_pace','racecard_jock','pools'])

    def run(self):
        def on_row(row):
            self.df.loc[0 if pd.isnull(self.df.index.max()) else self.df.index.max() + 1] = row
        
        if self.mode == '1v1' or self.mode == 'rank':
            model = joblib.load(self.model_file)

        odds_probs = utils.get_odds_probs()
        for r in tqdm(self.races):
            present = utils.are_all_csvs_present(r)
            if not present:
                continue
            
            self.df = pd.DataFrame(columns=self.columns)
            race_stats = utils.get_race_stats(r)
            
            if self.mode == 'rank':
                left = utils.get_racecard_left_df(r)
                success = utils.get_race_data_v2(r, on_row)
                if not success:
                    continue

                X, y = utils.preprocess_dataset_v2(self.df)
                preds = model.predict_proba(X)
                scores = preds[:,1] / np.sum(preds[:,1])
                # scores = utils.softmax(preds[:,1])
                horse_score = { horse: score for horse, score in zip(left['number'], scores) }
            elif self.mode == '1v1':
                success = utils.get_race_data(r, on_row, mode='test')
                if not success:
                    continue
                
                horse_pairs = pd.concat([self.df['horse_number_1'], self.df['horse_number_2']], axis=1)
                X, y = utils.preprocess_dataset(self.df)
                X.fillna({ k:v[0] for k,v in self.avgs.to_dict().items() }, inplace=True)
                if X.shape[0] == 0:
                    self.skipped_races += 1
                    continue

                preds = model.predict_proba(X)
                horse_score = defaultdict(lambda: 1)
                for i in range(len(preds)):
                    horse_score[utils.to_str(horse_pairs['horse_number_1'][i])] += preds[i][0]
                    horse_score[utils.to_str(horse_pairs['horse_number_2'][i])] += preds[i][1]
                
                # scoring: softmax - this performs better
                horse_score = { k:v for k,v in zip(horse_score.keys(), utils.softmax([v for k,v in horse_score.items()])) }
                
                # scoring: raw probabilties - this performs very poorly for some reason.
                # total_score = np.sum([v for k,v in horse_score.items()])
                # for k in horse_score.keys():
                #     horse_score[k] /= total_score
                # horse_score = dict(horse_score)
            elif self.mode == 'bayes':
                left = utils.get_racecard_left_df(r)
                num_horses = len(left['number'])
                odds_ranks = utils.get_odds_ranks(r)
                horse_odds_ranks = {}
                rank_not_found = False
                for horse in left['number']:
                    horse_int = int(utils.horse_number_digits_only(horse))
                    if horse_int in odds_ranks:
                        horse_odds_ranks[horse] = odds_ranks[horse_int]
                    else:
                        rank_not_found = True
                if rank_not_found:
                    continue
                # horse_odds_ranks = { horse: odds_ranks[int(utils.horse_number_digits_only(horse))] for horse in left['number'] }
                horse_score = { horse: (odds_probs.iloc[num_horses-1, rank] if rank < odds_probs.shape[1] and num_horses-1 < odds_probs.shape[0] else 0) for horse, rank in horse_odds_ranks.items() }
            elif self.mode == 'random':
                left = utils.get_racecard_left_df(r)
                odds_ranks = utils.get_odds_ranks(r)
                horse_score = { str(horse): str(1/len(left['number'])) for horse in left['number'] }
            else:
                continue

            date_time =  dt.datetime.strptime(race_stats['date']+' '+race_stats['time'], '%Y-%m-%d %I:%M %p')
            self.csv_writer.writerow([
                date_time,
                race_stats['winner'],
                race_stats['num_horses'], 
                race_stats['pool_size'],
                race_stats['takeout'],
                horse_score,
                race_stats['pools_i'],
            ])
            # print([
            #     race_stats['date'],
            #     race_stats['time'],
            #     race_stats['winner'],
            #     race_stats['num_horses'], 
            #     race_stats['pool_size'],
            #     race_stats['takeout'],
            #     horse_score,
            #     race_stats['pools_i'],
            # ])
        # print('bye')
        self.output.seek(0)
        df = pd.read_csv(self.output)
        df.to_csv(self.obs_file, index=False)

def main(model_file, start, end, avgs, obs, mode):
    p = PredictRaces(model_file, start, end, avgs, obs, mode)
    p.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2], args[3], args[4], args[5])
