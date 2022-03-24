
Step 1: Create raw data.
Run `python3 create_raw_data.py raw_data.csv 2022-03-15 2022-03-22`. args: output_file, start_date, end_date (start and end dates are inclusive)
Or to update raw data, run `python3 update_raw_data.py raw_data_2.csv 2022-03-15 2022-03-15`

Step 2: Clean data into X and y.
Run `python3 create_train_data.py raw_data.csv X.csv y.csv avgs.csv`. args: input_file, X csv, y csv, output averages file

Step 3: Train a model on the training data.
Run `python3 create_model.py X.csv y.csv lgb.pkl`. args: X csv, y csv, output model file.

Step 4: Use the model to predict winners of individuals races.
Run `python3 predict_races.py lgb.pkl 2022-03-23 2022-03-23 avgs.csv observations.csv`. args: model file, start_date, end_date (start and end dates are inclusive), averages file, observations file

*** Do not shuffle data during training ***
Validation data needs to come from different races than training data comes from.

number 1 priority:
- better data preprocessing.
- optimize the model since it's not profitable yet.
- standardize the units of each column.

TODO:
- include odds in train data. odds measures public sentiment. do I want to include that? I can try.
- look into crowdsourced league worlds rankings. softmax: https://www.pro-football-reference.com/blog/indexa828.html?p=171

set up efficient train-val.
1. train a neural network on 1, val on 2. train on 1 and 2 (continue training the previous model on 2), val on 3. continue train on 3, val on 4.
2. track the f1 score after each step.


make "horse number" into a string since it can be 1A, 2A, etc. 
===================

Plan:

inference:
`create_df.py` is good for creating a mixed dataset for training. But it's not good if I want to do inference per-race. Inference should draw directly from `scrape/results`. It creates a new df of pairs for each file, preprocesses it normally without shuffle, then runs inference. At the end, it matches up the winners between horses and figures out the rankings.

training:
If I want to update the model when new data arrives, I can't be putting everything into a single dataset with `create_df.py`. I need something that will create a lightweight dataset that I can feed into a pipeline to trigger a training session. The pipeline should operate by-race. Whenever new race data arrives for training, the model updates on that race only. Whenever new race data arrives for inference, the inference should only be performed on that race.

have airflow trigger a training session every 12 hours, if there is new data.
use a deep learning model instead so I can save checkpoints and update it every training session.

The end goal is:
I manually run the data gathering script each day. I manually upload the data somewhere.
I can call an api and give it some data and it will tell me the ordering of horses and the confidence.
