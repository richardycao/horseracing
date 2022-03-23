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

class PredictRaces:
    def __init__(self, model_file, start_str, end_str):
        self.model_file = model_file
        self.start_date = dt.datetime.strptime(start_str, "%Y-%m-%d")
        self.end_date = dt.datetime.strptime(end_str, "%Y-%m-%d")

        self.columns = utils.get_columns()

        path = '../scrape/results'
        dates = [f for f in listdir(path) if not isfile(join(path, f))]
        self.races = []
        for d in dates:
            if utils.time_in_range(self.start_date, self.end_date, dt.datetime.strptime(d, "%Y-%m-%d")):
                self.races.extend([f'{path}/{d}/{r}' for r in listdir(f'{path}/{d}') if not isfile(join(f'{path}/{d}', r))])

    def run(self):
        def on_row(row):
            self.df.loc[0 if pd.isnull(self.df.index.max()) else self.df.index.max() + 1] = row

        self.df = pd.DataFrame(columns=self.columns)
        correct_predictions = 0
        for r in tqdm(self.races):
            utils.get_race_data(r, on_row)
            # print(r)
            horse_pairs = pd.concat([self.df['horse_number_1'], self.df['horse_number_2']], axis=1)
            # print(horse_pairs)
        
            X, y = utils.preprocess_dataset(self.df)
            rf_model = joblib.load(self.model_file)
            preds = rf_model.predict(X)
            # print(preds)
            horse_wins = defaultdict(lambda: 0)
            for i in range(len(preds)):
                if preds[i] == 0:
                    horse_wins[horse_pairs['horse_number_1'][i]] += 1
                else:
                    horse_wins[horse_pairs['horse_number_2'][i]] += 1
            # print('horse_wins', horse_wins)
            predicted_winner = sorted(horse_wins.items(), key=lambda x: -x[1])[0][0]
            # print('predicted winner:', predicted_winner)
            
            winner = utils.get_race_winner(r)
            # print('winner:', winner)
            # print(winner == predicted_winner)
            if winner == predicted_winner:
                correct_predictions += 1
        print('win rate:', correct_predictions/len(self.races))
            






def main(model_file, start, end):
    p = PredictRaces(model_file, start, end)
    p.run()
    # rf_model = joblib.load(model_file)
    # start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    # end_date = dt.datetime.strptime(end, "%Y-%m-%d")

    # preds = rf_model.predict(X_test)
    # print(confusion_matrix(preds, y_test))

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2])
