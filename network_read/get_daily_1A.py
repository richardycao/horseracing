import api
from tqdm import tqdm

datestr = "2022-12-18"
resp = api.getPastRaces(datestr)
trackId_raceNum_list = [(race['track']['code'], race['number']) for race in resp['data']['pastRacesByDate']]

for tr in tqdm(trackId_raceNum_list):
    track_id, race_num = tr
    race = api.getPastRaces(datestr, track_id, race_num)
    # print(race['data']['pastRaceByDateTrackAndNumber'][0].keys())
    # program = api.getRaceProgram(track_id, race_num, live=False)
    for bi in race['data']['pastRaceByDateTrackAndNumber'][0]['bettingInterests']:
        if len(bi['runners']) > 1:
            print(track_id, race_num)
            break
        