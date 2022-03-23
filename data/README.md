`create_df.ipynb` is for experimentation. All of the important code has been copied to `create_df.py`

run `create_df.py` to create a new dataframe (`raw_data.csv`) from all the races in `../scrape/results/`.

run `update_df.py` to append to an existing data csv with races from specific days.
- currently, data.csv contains samples from 2022-03-15 to 2022-03-18 ~1:00 PM.

run `preprocess_raw_data.py` to create `X.csv` and `y.csv` from `raw_data.csv`.

run `train_model.py` to create `rf_model.joblib` from `X.csv` and `y.csv`.

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
