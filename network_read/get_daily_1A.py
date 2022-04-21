import api

resp = api.getPastRaces("2022-04-17")
trackId_raceNum_list = [(race['track']['code'], race['number']) for race in resp['data']['pastRacesByDate']]

for tr in trackId_raceNum_list:
    track_id, race_num = tr
    program = api.getRaceProgram(track_id, race_num, live=False)
    for bi in program['data']['race']['bettingInterests']:
        if len(bi['runners']) > 1:
            print(track_id, race_num)
            break