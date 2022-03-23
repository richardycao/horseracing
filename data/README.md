
Step 1: Create raw data.
Run `python3 create_raw_data.py raw_data.csv 2022-03-15 2022-03-22`. args: output_file, start_date, end_date (start and end dates are inclusive)

Step 2: Clean data into X and y.
Run `python3 create_train_data.py raw_data.csv X.csv y.csv`. args: input_file, X csv, y csv.

Step 3: Train a model on the training data.
Run `python3 create_model.py X.csv y.csv rf_model.joblib`. args: X csv, y csv, output model file.

Step 4: Use the model to predict winners of individuals races.
Run `python3 predict_races.py rf_model.joblib 2022-03-22 2022-03-22`. args: model file, start_date, end_date (start and end dates are inclusive)


Only bet on races with certain odds. Only bet on races up to a certain number of horses.
- observe the distribution of number of horses per race, and the distribution of odds for correctly guessed races, wrong guess races, and all races.
- also show my winrate depending horses in race.
- maybe include odds in train data.
- look into crowdsourced league worlds rankings. softmax.
===================

Plan:

I need to know how often I predict the winning horse, not my average win rate in 1v1s.

inference:
`create_df.py` is good for creating a mixed dataset for training. But it's not good if I want to do inference per-race. Inference should draw directly from `scrape/results`. It creates a new df of pairs for each file, preprocesses it normally without shuffle, then runs inference. At the end, it matches up the winners between horses and figures out the rankings.

training:
If I want to update the model when new data arrives, I can't be putting everything into a single dataset with `create_df.py`. I need something that will create a lightweight dataset that I can feed into a pipeline to trigger a training session. The pipeline should operate by-race. Whenever new race data arrives for training, the model updates on that race only. Whenever new race data arrives for inference, the inference should only be performed on that race.

have airflow trigger a training session every 12 hours, if there is new data.
use a deep learning model instead so I can save checkpoints and update it every training session.

The end goal is:
I manually run the data gathering script each day. I manually upload the data somewhere.
I can call an api and give it some data and it will tell me the ordering of horses and the confidence.
