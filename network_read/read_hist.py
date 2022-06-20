import api
import sys
import datetime as dt
from pathlib import Path
import pandas as pd

def safe_get(d: dict, keys: list):
    result = d
    for k in keys:
        if isinstance(result, dict) and k in result:
            result = result[k]
        else:
            return None
    return result
def safe_makedir(path):
    Path(path).mkdir(parents=True, exist_ok=True)
def create_race_path(date_str, track_id, race_number):
    return f"./hist_data_v2/{date_str}/{track_id}/{race_number}"

def get_track_ids_by_date(date_str):
    resp = api.getPastTracks(date_str)
    if resp == None:
        print('getPastTracks response is None', date_str)
        return None
    tracks = safe_get(resp, ['data','pastTracksByDate'])
    if tracks == None:
        print('safe_get past tracks is None', date_str)
        return None
    track_ids = [safe_get(t, ['code']) for t in tracks]
    return track_ids

def get_race_numbers_by_date_and_track_id(date_str, track_id):
    resp = api.getPastRaces(date_str=date_str, track_id=track_id)
    if resp == None:
        print('getPastRaces for date and track_id is None.', date_str, track_id)
        return None
    races = safe_get(resp, ['data','pastRacesByDateAndTrack'])
    if races == None:
        print('safe_get for getPastRaces for date and track_id is None.', date_str, track_id)
        return None
    race_numbers = [safe_get(r, ['number']) for r in races]
    return race_numbers

def get_race_info(date_str, track_id, race_number):
    resp = api.getPastRaces(date_str=date_str, track_id=track_id, race_number=race_number)
    if resp == None:
        print('getPastRaces for date, track_id, and race number is None.', date_str, track_id, race_number)
        return None
    races = safe_get(resp, ['data','pastRaceByDateTrackAndNumber'])
    if races == None:
        print('safe_get for getPastRaces for date, track_id, and race number is None.', date_str, track_id, race_number)
        return None
    if len(races) != 1:
        print('getPastRaces gave more than 1 race for some reason.', date_str, track_id, race_number)
        return None
    return races[0]

def extract_and_save_race_info(race, race_path):
    # details
    race_data = {
        'postTime': [safe_get(race, ['postTime'])],
        'distance': [safe_get(race, ['distance','value'])],
        'distance_unit': [safe_get(race, ['distance','code'])],
        'purse': [safe_get(race, ['purse'])],
        'surface_name': [safe_get(race, ['surface','name'])],
        'race_type_code': [safe_get(race, ['type','code'])],
        'race_type_name': [safe_get(race, ['type','name'])],
        'race_class': [safe_get(race, ['raceClass','name'])],
        'winningTime': [safe_get(race, ['results','winningTime'])],
    }
    if not race_data['winningTime'][0]:
        return
    safe_makedir(race_path)
    pd.DataFrame(race_data).to_csv(f'{race_path}/details.csv')

    # bis
    bis = {}
    bettingInterests = safe_get(race, ['bettingInterests'])
    if not isinstance(bettingInterests, list):
        print("betting interests is not a list.", race_path)
        return
    if bettingInterests == None:
        print("betting interests is missing.", race_path)
        return
    for bi in bettingInterests:
        biNum = safe_get(bi, ['biNumber'])
        if biNum == None:
            print('biNumber is missing.', race_path)
            continue
        if biNum not in bis:
            bis[biNum] = {}
        bis[biNum]['currentOdds_numerator'] = safe_get(bi, ['currentOdds','numerator'])
        bis[biNum]['currentOdds_denominator'] = safe_get(bi, ['currentOdds','denominator'])
        bis[biNum]['morningLineOdds_numerator'] = safe_get(bi, ['morningLineOdds','numerator'])
        bis[biNum]['morningLineOdds_denominator'] = safe_get(bi, ['morningLineOdds','denominator'])
        biRunners = safe_get(bi, ['runners'])
        if biRunners == None:
            print('bi runners is missing.', race_path)
            continue
        for bi_horse in biRunners:
            bis[biNum]['runnerId'] = safe_get(bi_horse, ['runnerId'])
            bis[biNum]['scratched'] = safe_get(bi_horse, ['scratched'])
            bis[biNum]['birthday'] = safe_get(bi_horse, ['dob'])
            bis[biNum]['horseName'] = safe_get(bi_horse, ['horseName'])
            bis[biNum]['jockey'] = safe_get(bi_horse, ['jockey'])
            bis[biNum]['trainer'] = safe_get(bi_horse, ['trainer'])
            bis[biNum]['owner'] = safe_get(bi_horse, ['ownerName'])
            bis[biNum]['weight'] = safe_get(bi_horse, ['weight'])
            bis[biNum]['med'] = safe_get(bi_horse, ['med'])
            bis[biNum]['sire'] = safe_get(bi_horse, ['sire'])
            bis[biNum]['damSire'] = safe_get(bi_horse, ['damSire'])
            bis[biNum]['dam'] = safe_get(bi_horse, ['dam'])
            bis[biNum]['age'] = safe_get(bi_horse, ['age'])
            bis[biNum]['sex'] = safe_get(bi_horse, ['sex'])
            bis[biNum]['powerRating'] = safe_get(bi_horse, ['handicapping','snapshot','powerRating'])
            bis[biNum]['daysOff'] = safe_get(bi_horse, ['handicapping','snapshot','daysOff'])
            bis[biNum]['horseWins'] = safe_get(bi_horse, ['handicapping','snapshot','horseWins'])
            bis[biNum]['horseStarts'] = safe_get(bi_horse, ['handicapping','snapshot','horseStarts'])
            bis[biNum]['avgClassRating'] = safe_get(bi_horse, ['handicapping','speedAndClass','avgClassRating'])
            bis[biNum]['highSpeed'] = safe_get(bi_horse, ['handicapping','speedAndClass','highSpeed'])
            bis[biNum]['avgSpeed'] = safe_get(bi_horse, ['handicapping','speedAndClass','avgSpeed'])
            bis[biNum]['lastClassRating'] = safe_get(bi_horse, ['handicapping','speedAndClass','lastClassRating'])
            bis[biNum]['avgDistance'] = safe_get(bi_horse, ['handicapping','speedAndClass','avgDistance'])
            bis[biNum]['numRaces'] = safe_get(bi_horse, ['handicapping','averagePace','numRaces'])
            bis[biNum]['early'] = safe_get(bi_horse, ['handicapping','averagePace','early'])
            bis[biNum]['middle'] = safe_get(bi_horse, ['handicapping','averagePace','middle'])
            bis[biNum]['finish'] = safe_get(bi_horse, ['handicapping','averagePace','finish'])
            bis[biNum]['starts'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','starts'])
            bis[biNum]['wins'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','wins'])
            bis[biNum]['places'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','places'])
            bis[biNum]['shows'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','shows'])
            bis[biNum]['jockeyName'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','jockeyName'])
            bis[biNum]['trainerName'] = safe_get(bi_horse, ['handicapping','jockeyTrainer','trainerName'])
            break
    runners = safe_get(race, ['results','runners'])
    if runners == None:
        print('runners is missing.', race_path)
        return
    for runner in runners:
        biNum = safe_get(runner, ['biNumber'])
        if biNum == None:
            print('runner biNumber is missing.', race_path)
            continue
        bis[biNum]['runnerNumber'] = safe_get(runner, ['runnerNumber'])
        bis[biNum]['runnerName'] = safe_get(runner, ['runnerName'])
        bis[biNum]['finishPosition'] = safe_get(runner, ['finishPosition'])
        bis[biNum]['betAmount'] = safe_get(runner, ['betAmount'])
        bis[biNum]['winPayoff'] = safe_get(runner, ['winPayoff'])
        bis[biNum]['placePayoff'] = safe_get(runner, ['placePayoff'])
        bis[biNum]['showPayoff'] = safe_get(runner, ['showPayoff'])
        bis[biNum]['beatenDistance'] = safe_get(runner, ['timeform','beatenDistance'])
        bis[biNum]['beatenDistanceStatus'] = safe_get(runner, ['timeform','beatenDistanceStatus'])
        bis[biNum]['isp'] = safe_get(runner, ['timeform','isp'])
        bis[biNum]['postRaceReport'] = safe_get(runner, ['timeform','postRaceReport'])
        bis[biNum]['accBeatenDistance'] = safe_get(runner, ['timeform','accBeatenDistance'])
        bis[biNum]['accBeatenDistanceStatus'] = safe_get(runner, ['timeform','accBeatenDistanceStatus'])
        bis[biNum]['accBeatenDistanceStatusAbrev'] = safe_get(runner, ['timeform','accBeatenDistanceStatusAbrev'])
    pd.DataFrame.from_dict(bis, orient='index').to_csv(f'{race_path}/bis.csv')

def download_races_by_date(date_str):
    track_ids = get_track_ids_by_date(date_str)
    if track_ids == None:
        print('track ids id None.')
        return
    for track_id in track_ids:
        if track_id == None:
            print('track id is None.')
            continue
        race_numbers = get_race_numbers_by_date_and_track_id(date_str, track_id)
        # print(track_id, race_numbers)
        if race_numbers == None:
            print('race numbers is None.')
            continue
        for race_number in race_numbers:
            race_path = create_race_path(date_str, track_id, race_number)
            if Path(race_path).is_dir():
                continue
            info = get_race_info(date_str, track_id, race_number)
            extract_and_save_race_info(info, race_path)

def main(start_date, end_date):
    cur = dt.datetime.strptime(start_date, '%Y-%m-%d')
    end = dt.datetime.strptime(end_date, '%Y-%m-%d')

    while cur >= end:
        date_str = cur.strftime('%Y-%m-%d')
        print(f'{date_str}. Started at {dt.datetime.now()}')
        download_races_by_date(date_str)
        cur = cur - dt.timedelta(days=1)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1])
