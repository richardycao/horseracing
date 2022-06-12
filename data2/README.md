
Run `python3 create_data.py data7_1.csv 2022-03-15 2022-04-20 v4 False 7`. args: output_file, start_date, end_date (start and end dates are inclusive), mode (v1: pools only, v2: pools, omega_i, age, v3: everything, v4: everything, to match network_read format), use_missing ('True' or 'False'), num_horses
- `create_data` is for data in /scrape
- this is for simulation on final pools

Run `python3 create_data2.py hist_data_7only_includemissing.csv 2021-06-01 2022-03-14 7 exact True`. args: output_file, start_date, end_date, horse_limit, mode ('exact' or 'not_exact'), use_missing ('True' or 'False')
- `create_data2` is for data in /network_read
- include a way to identify which race a sample comes from (postTime, datetime, track_id, race_number)
- this is for training

Run `python3 create_data3.py live_data_upto12.csv 2022-04-21 2022-05-31 12 not_exact Some`. args: output_file, start_date, end_date, horse_limit, mode ('exact' or 'not_exact'), use_missing ('True', 'Some', or 'False')
- `create_data3` is for data from s3
- this is for simulation on pre-final pools

Run `python3 estimate_takeout_s3.py takeout_estimates_s3.csv 2022-04-21 2022-05-31`. args: output_file, start_date, end_date

Run `python3 create_details.py details_9m.csv 2021-06-01 2022-03-14`. args: output_file, start_date, end_date
- `create_details` is for data in /network_read
- gets all historic race details into a dataframe

==========

For jockey, trainer, sire, sex ratings, only use data that isn't None. This is detected in create_data2.py.

Train a separate model for each number of horses, now that I have enough data.

Find out why p's are estimated well in testing, but not in simulation.
- might be because I also scored non-existent horses with dummy values, which usually come out to be low probabilities.

Find out why avgClassRating and some others still come out to be 0, even though I have a check for that.

Consider duplicating data for simulation too.

==========
