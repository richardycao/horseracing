
Run `python3 create_data.py data8_6.csv 2022-03-15 2022-04-20 v4`. args: output_file, start_date, end_date (start and end dates are inclusive), mode (v1: pools only, v2: pools, omega_i, age, v3: everything, v4: everything, to match network_read format)
- `create_data` is for data in /scrape

Run `python3 create_data2.py hist_data_upto12.csv 2021-06-01 2022-03-14 12 not_exact`. args: output_file, start_date, end_date, horse_limit, mode ('exact' or 'not_exact')
- `create_data2` is for data in /network_read
- include a way to identify which race a sample comes from (postTime, datetime, track_id, race_number)

==========

For jockey, trainer, sire, sex ratings, only use data that isn't None. This is detected in create_data2.py.

Train a separate model for each number of horses, now that I have enough data.

Find out why p's are estimated well in testing, but not in simulation.
- might be because I also scored non-existent horses with dummy values, which usually come out to be low probabilities.

Find out why avgClassRating and some others still come out to be 0, even though I have a check for that.

Consider duplicating data for simulation too.

==========
