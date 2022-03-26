import pandas as pd
from sklearn.metrics import confusion_matrix
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
    def __init__(self, model_file, start_str, end_str, avgs, obs, scoring):
        self.model_file = model_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
        self.avgs = pd.read_csv(avgs)
        self.obs_file = obs
        self.scoring = scoring

        self.columns = utils.get_columns()

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
        self.csv_writer.writerow(['date','time','winner','predicted_winner','num_horses','winner_odds', 'confidence','pool_size','winner_pool_size'])

        self.required_files = set(['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
                                    'racecard_pace','racecard_jock','pools'])

    def run(self):
        def on_row(row):
            self.df.loc[0 if pd.isnull(self.df.index.max()) else self.df.index.max() + 1] = row
        
        correct_predictions = 0
        model = joblib.load(self.model_file)
        # observations = pd.DataFrame(columns=['date','time','winner','predicted_winner','num_horses','winner_odds', 'confidence','pool_size','winner_pool_size'])
        for r in tqdm(self.races):
            csvs = [c for c in listdir(r) if isfile(join(r, c))]

            # Skips races with missing files
            missing_csv = False
            for n in self.required_files:
                if f'{n}.csv' not in csvs:
                    missing_csv = True
            if missing_csv:
                self.skipped_races += 1
                continue
            
            self.df = pd.DataFrame(columns=self.columns)
            race_stats = utils.get_race_stats(r)

            #####
            # for random predictions
            # predicted_winner = np.random.choice(utils.get_racecard_left_df(r)['number'])
            # confidence = 0
            
            utils.get_race_data(r, on_row, mode='test')

            horse_pairs = pd.concat([self.df['horse_number_1'], self.df['horse_number_2']], axis=1)
            X, y = utils.preprocess_dataset(self.df)
            X.fillna({ k:v[0] for k,v in self.avgs.to_dict().items() }, inplace=True)
            if X.shape[0] == 0:
                self.skipped_races += 1
                continue
            
            if self.scoring == '0':
                preds = model.predict(X)
                horse_score = defaultdict(lambda: 0)
                for i in range(len(preds)):
                    if preds[i] == 0:
                        horse_score[utils.to_str(horse_pairs['horse_number_1'][i])] += 1
                    else:
                        horse_score[utils.to_str(horse_pairs['horse_number_2'][i])] += 1
            elif self.scoring == '1':
                preds = model.predict_proba(X)
                horse_score = defaultdict(lambda: 1)
                for i in range(len(preds)):
                    horse_score[utils.to_str(horse_pairs['horse_number_1'][i])] *= preds[i][0]
                    horse_score[utils.to_str(horse_pairs['horse_number_2'][i])] += preds[i][1]
            
            sorted_horse_score = sorted(horse_score.items(), key=lambda x: -x[1])
            predicted_winner = sorted_horse_score[0][0]
            confidence = utils.softmax([hw[1] for hw in sorted_horse_score])[0]
            #####
            
            winner = race_stats['winner']
            if winner == predicted_winner:
                correct_predictions += 1

            self.csv_writer.writerow([
                race_stats['date'],
                race_stats['time'],
                winner,
                predicted_winner, 
                race_stats['num_horses'], 
                race_stats['winner_odds'],
                confidence,
                race_stats['pool_size'],
                race_stats['winner_pool_size'],
            ])
            
        print('win rate:', correct_predictions/(len(self.races) - self.skipped_races))
        print('correct predictions:', correct_predictions)
        print('total races:', len(self.races))
        print('skipped races:', self.skipped_races)
        # observations.to_csv(self.obs_file, index=False)
        self.output.seek(0)
        df = pd.read_csv(self.output)
        df.to_csv(self.obs_file, index=False)

def main(model_file, start, end, avgs, obs, scoring):
    p = PredictRaces(model_file, start, end, avgs, obs, scoring)
    p.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2], args[3], args[4], args[5])
