import pandas as pd
import datetime as dt
import numpy as np
import matplotlib.pyplot as plt

data = pd.read_csv('./raw_test_data.csv')

##################################

X = data.iloc[:,:-1]
y = data['result']

# date, time - convert to cycles
date_time = (X['date'] + ' ' + X['time']).apply(lambda x: dt.datetime.strptime(
    x, '%Y-%m-%d %I:%M %p'))
def date_to_nth_day(date):
    new_year_day = pd.Timestamp(year=date.year, month=1, day=1)
    return (date - new_year_day).days + 1
def nth_day_to_cycle(n):
    radians = n*(2*np.pi)/(365.25)
    return np.cos(radians), np.sin(radians)
X['date_cos'] = date_time.apply(lambda x: nth_day_to_cycle(date_to_nth_day(x))[0])
X['date_sin'] = date_time.apply(lambda x: nth_day_to_cycle(date_to_nth_day(x))[1])
def mins_to_cycle(mins):
    radians = mins*(2*np.pi)/(60*24)
    return np.cos(radians), np.sin(radians)
X['time_cos'] = date_time.apply(lambda x: mins_to_cycle(x.hour*60 + x.minute)[0])
X['time_sin'] = date_time.apply(lambda x: mins_to_cycle(x.hour*60 + x.minute)[1])
X.drop(['date','time'], axis=1, inplace=True)

# race_distance - standardize units to meters
def conv_dist(dist):
    dist_to_meters = {'f': 201.168,
                        'mtr': 1,     # mtr (meter) comes before m (mile) in search
                        'm': 1609.34,
                        'y': 0.9144}
    for k,v in dist_to_meters.items():
        if k in dist:
            return float(dist[:-len(k)]) * v
X['race_distance_meters'] = X['race_distance'].apply(lambda x: conv_dist(x))
X.drop(['race_distance'], axis=1, inplace=True)

# race_type - one-hot encode
def fixed_one_hot(df, column, categories):
    for c in categories:
        df[c] = (df[column] == c)*1
fixed_one_hot(X, 'race_type', ['Thoroughbred', 'Harness', 'Mixed', 'QuarterHorse', 'Arabian'])
X.drop(['race_type'], axis=1, inplace=True)

# race_class (TODO)
X.drop(['race_class'], axis=1, inplace=True)

# surface_name - one-hot encode
fixed_one_hot(X, 'surface_name', ['Turf', 'Dirt', 'Synthetic', 'Downhill Turf', 'Steeplechase'])
X.drop(['surface_name'], axis=1, inplace=True)

# default_condition (TODO - see if there's a relationship e.g. good > good to soft > soft)
X.drop(['default_condition'], axis=1, inplace=True)

for i in ['1','2']:
    # horse number (TODO - normalize somehow. also has ints and strings.)
    X.drop(['horse_number_'+i], axis=1, inplace=True)

    # runner odds - drop
    X.drop(['runner_odds_'+i], axis=1, inplace=True)

    # morning odds - drop
    X.drop(['morning_odds_'+i], axis=1, inplace=True)

    # horse name (TODO)
    X.drop(['horse_name_'+i], axis=1, inplace=True)

    # horse age - as is

    # horse gender (TODO - a bunch of different "genders")
    X.drop(['horse_gender_'+i], axis=1, inplace=True)

    # horse siredam
    X.drop(['horse_siredam_'+i], axis=1, inplace=True)

    # horse med - drop
    X.drop(['horse_med_'+i], axis=1, inplace=True)

    # horse trainer (TODO)
    X.drop(['trainer_'+i], axis=1, inplace=True)

    # horse weight - convert to int and fill na with mean.
    def str_to_int(x):
        return int(x) if x.isdigit() else np.nan
    weight_ints = X['horse_weight_'+i].apply(lambda x: str_to_int(x.replace(' ','')))
    X['jockey_weight_'+i] = weight_ints.fillna(weight_ints.mean())
    X.drop(['horse_weight_'+i], axis=1, inplace=True)

    # horse jockey (TODO)
    X.drop(['jockey_'+i], axis=1, inplace=True)

    # horse power rating - convert to int and fill na with mean.
    power_ints = X['horse_power_rating_'+i].apply(lambda x: str_to_int(x.replace(' ','')))
    X['horse_power_rating_'+i] = power_ints.fillna(power_ints.mean())

    # horse wins/starts (TODO - handle confidence with increasing number of starts)
    X.drop(['horse_wins/starts_'+i], axis=1, inplace=True)

    # horse days off - convert to int and fill na with mean.
    days_off_ints = X['horse_days_off_'+i].apply(lambda x: str_to_int(x.replace(' ','')))
    X['horse_days_off_'+i] = days_off_ints.fillna(days_off_ints.mean())

    # avg speed - convert to int and fill na with mean.
    avg_speed_ints = X['horse_avg_speed_'+i].apply(lambda x: str_to_int(x.replace(' ','')))
    X['horse_avg_speed_'+i] = avg_speed_ints.fillna(avg_speed_ints.mean())

    # avg distance - convert to int and fill na with mean.
    avg_distance_ints = X['horse_avg_distance_'+i].apply(lambda x: str_to_int(x.replace(' ','')))
    X['horse_avg_distance_'+i] = avg_distance_ints.fillna(avg_distance_ints.mean())

    # high speed - convert to int and fill na with mean.
    high_speed_ints = X['horse_high_speed_'+i].apply(lambda x: str_to_int(x.replace(' ','')))
    X['horse_high_speed_'+i] = high_speed_ints.fillna(high_speed_ints.mean())

    # avg class - convert to int and fill na with mean.
    avg_class_ints = X['horse_avg_class_'+i].apply(lambda x: str_to_int(x.replace(' ','')))
    X['horse_avg_class_'+i] = avg_class_ints.fillna(avg_class_ints.mean())

    # last class - convert to int and fill na with mean.
    last_class_ints = X['horse_last_class_'+i].apply(lambda x: str_to_int(x.replace(' ','')))
    X['horse_last_class_'+i] = last_class_ints.fillna(last_class_ints.mean())

    # num races - as is

    # early - as is

    # middle - as is

    # finish - as is

    # starts - as is

    # 1st - as is

    # 2nd - as is

    # 3rd - as is

print(X.shape)
print(y.shape)
X.to_csv('X_test.csv', index=False)
y.to_csv('y_test.csv', index=False)
