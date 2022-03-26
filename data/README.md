
Step 1: Create raw data.
Run `python3 create_raw_data.py raw_data.csv 2022-03-15 2022-03-22`. args: output_file, start_date, end_date (start and end dates are inclusive)
Or to update raw data, run `python3 update_raw_data.py raw_data_2.csv 2022-03-15 2022-03-15`

Step 2: Clean data into X and y.
Run `python3 create_train_data.py raw_data.csv X.csv y.csv avgs.csv`. args: input_file, X csv, y csv, output averages file

Step 3: Train a model on the training data.
Run `python3 create_model.py X.csv y.csv lgb.pkl`. args: X csv, y csv, output model file.

Step 4: Use the model to predict winners of individuals races.
Run `python3 predict_races.py lgb3.pkl 2022-03-23 2022-03-25 avgs3.csv obs_lgb3_0_m23m25.csv 0`. args: model file, start_date, end_date (start and end dates are inclusive), averages file, observations file, simulation file, scoring method (0: additive, 1: multiplicative)

==========

What I know at each step:
1. Create raw data - I either use all races (train), or only races with all results (test).
2. Clean data - don't use odds, remove date, normalize a bunch of stuff.
3. Train model - rf, lgbm, or nn. rf has been best empircally so far.
4. Predictions - use small test sets in the beginning for fast testing. increase the size to gain confidence in the results. for winrate, scoring can be by prediction or probability. for return, scoring may be MSE.

at each step, I don't just want to take the horse that I think will win. I want to take the horse that I think has the highest return. This could mean taking horses with lower confidence score because they have higher odds. I should record the ranking of all horses at the end, not just the winner.

==========

try additive probabilities for scoring=1.
try only using races that show full results.
maybe add odds back into the dataset?
try predicting for place or show instead. there's a higher chance of an underdog to make it.
remove date from training data. I don't have a year's worth of data for it to be relevant.
test on a smaller set (1 day) for faster testing.

I need underdog winners to matter more in training. The model needs to be about how much expected return I get, not just winrate. 

*** Do not shuffle data during training ***
Validation data needs to come from different races than training data comes from.
*** Do not include odds in the training data ***
If the goal is to predict wins, then low odds will be more likely to win. But low odds give low returns.

remove weak features from the model?
remove bet limit?

- include date and time into observations from the title of the race
- include pools into raw_data.csv from pool.csv
- account for pool size when betting - I can drastically alter the odds by betting a lot. include pool size in observations.
- find the distribution of pool sizes. I need to know which races I can bet more on.

number 1 priority:
- better data preprocessing.
- optimize the model since it's not profitable yet.
- standardize the units of each column.
- RankNet: https://towardsdatascience.com/learning-to-rank-for-information-retrieval-a-deep-dive-into-ranknet-200e799b52f4
- LambdaRank: 

TODO:
- try training on place or show instead.
- returns are multiplicative so they are calculated wrong in evaluate_observation.ipynb.
- look into crowdsourced league worlds rankings. softmax: https://www.pro-football-reference.com/blog/indexa828.html?p=171


===================

Pipeline stuff for later:

set up efficient train-val.
1. train a neural network on 1, val on 2. train on 1 and 2 (continue training the previous model on 2), val on 3. continue train on 3, val on 4.
2. track the f1 score after each step.

inference:
`create_df.py` is good for creating a mixed dataset for training. But it's not good if I want to do inference per-race. Inference should draw directly from `scrape/results`. It creates a new df of pairs for each file, preprocesses it normally without shuffle, then runs inference. At the end, it matches up the winners between horses and figures out the rankings.

training:
If I want to update the model when new data arrives, I can't be putting everything into a single dataset with `create_df.py`. I need something that will create a lightweight dataset that I can feed into a pipeline to trigger a training session. The pipeline should operate by-race. Whenever new race data arrives for training, the model updates on that race only. Whenever new race data arrives for inference, the inference should only be performed on that race.

have airflow trigger a training session every 12 hours, if there is new data.
use a deep learning model instead so I can save checkpoints and update it every training session.

The end goal is:
I manually run the data gathering script each day. I manually upload the data somewhere.
I can call an api and give it some data and it will tell me the ordering of horses and the confidence.
