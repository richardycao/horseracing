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

class PredictRaces:
    def __init__(self, model_file, start_str, end_str, avgs, obs):
        self.model_file = model_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")
        self.avgs = pd.read_csv(avgs)
        self.obs_file = obs

        self.columns = utils.get_columns()

        path = '../scrape/results'
        dates = [f for f in listdir(path) if not isfile(join(path, f))]
        self.races = []
        self.skipped_races = 0
        for d in dates:
            if utils.time_in_range(self.start_date, self.end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
                print(d)
                self.races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

    def run(self):
        def on_row(row):
            self.df.loc[0 if pd.isnull(self.df.index.max()) else self.df.index.max() + 1] = row
        
        correct_predictions = 0
        model = joblib.load(self.model_file)
        observations = pd.DataFrame(columns=['winner', 'predicted_winner', 'num_horses', 'winner_odds', 'confidence'])
        for r in tqdm(self.races):
            csvs = [c for c in listdir(r) if isfile(join(r, c))]

            # Skips races with missing files
            missing_csv = False
            for n in ['details','results','racecard_left','racecard_summ','racecard_snap','racecard_spee',
                    'racecard_pace','racecard_jock']:
                if f'{n}.csv' not in csvs:
                    missing_csv = True
            if missing_csv:
                self.skipped_races += 1
                continue
            
            self.df = pd.DataFrame(columns=self.columns)
            race_stats = utils.get_race_stats(r)

            #####
            # for random predictions
            # predicted_winner = np.random.randint(race_stats['num_horses']) + 1
            # confidence = 0

            utils.get_race_data(r, on_row)

            horse_pairs = pd.concat([self.df['horse_number_1'], self.df['horse_number_2']], axis=1)
            X, y = utils.preprocess_dataset(self.df)
            X.fillna({ k:v[0] for k,v in self.avgs.to_dict().items() }, inplace=True)
            if X.shape[0] == 0:
                self.skipped_races += 1
                continue
            preds = model.predict(X)
            
            horse_wins = defaultdict(lambda: 0)
            for i in range(len(preds)):
                if preds[i] == 0:
                    horse_wins[utils.to_str(horse_pairs['horse_number_1'][i])] += 1
                else:
                    horse_wins[utils.to_str(horse_pairs['horse_number_2'][i])] += 1
            sorted_horse_wins = sorted(horse_wins.items(), key=lambda x: -x[1])
            predicted_winner = sorted_horse_wins[0][0]
            confidence = utils.softmax([hw[1] for hw in sorted_horse_wins])[0]
            #####
            
            winner = race_stats['winner']
            if winner == predicted_winner:
                correct_predictions += 1

            observations.loc[0 if pd.isnull(observations.index.max()) else observations.index.max() + 1] = [
                winner,
                predicted_winner, 
                race_stats['num_horses'], 
                race_stats['winner_odds'],
                confidence
            ]
            
        print('win rate:', correct_predictions/(len(self.races) - self.skipped_races))
        print('correct predictions:', correct_predictions)
        print('total races:', len(self.races))
        print('skipped races:', self.skipped_races)
        observations.to_csv(self.obs_file, index=False)

def main(model_file, start, end, avgs, obs):
    p = PredictRaces(model_file, start, end, avgs, obs)
    p.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2], args[3], args[4])
