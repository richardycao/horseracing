import requests

payload = {
    'operationName': 'getPastRaces',
    'query': 'query getPastRaces($filterBy: PastRaceListFilter, $wagerProfile: String!, $byDate: Boolean!, $byDateTrack: Boolean!, $date: String, $trackCode: String, $byDateTrackNumber: Boolean!, $raceNumber: String, $byHorseName: Boolean!, $runnerName: String, $runnerDob: Int) {\n  pastRacesByDate: pastRaces(filter: $filterBy, profile: $wagerProfile, date: $date, sort: {byPostTime: DESC}) @include(if: $byDate) {\n    ...pastRacesFragment\n    __typename\n  }\n  pastRacesByDateAndTrack: pastRaces(filter: $filterBy, profile: $wagerProfile, date: $date, trackCode: $trackCode, sort: {byPostTime: DESC}) @include(if: $byDateTrack) {\n    ...pastRacesFragment\n    __typename\n  }\n  pastRaceByDateTrackAndNumber: pastRaces(filter: $filterBy, profile: $wagerProfile, date: $date, trackCode: $trackCode, raceNumber: $raceNumber, sort: {byPostTime: DESC}) @include(if: $byDateTrackNumber) {\n    ...pastRacesFragment\n    ...bettingInterestsFragment\n    ...resultsFragment\n    __typename\n  }\n  pastRacesByHorseName: pastRaces(filter: $filterBy, runnerName: $runnerName, profile: $wagerProfile, sort: {byPostTime: DESC}, runnerDob: $runnerDob) @include(if: $byHorseName) {\n    ...pastRacesFragment\n    __typename\n  }\n}\n\nfragment bettingInterestsFragment on PastRace {\n  bettingInterests {\n    biNumber\n    numberColor\n    saddleColor\n    runners {\n      horseName\n      runnerId\n      weight\n      med\n      trainer\n      age\n      dam\n      ownerName\n      sex\n      scratched\n      jockey\n      damSire\n      sire\n      date\n      dob\n      __typename\n    }\n    morningLineOdds {\n      numerator\n      denominator\n      __typename\n    }\n    currentOdds {\n      numerator\n      denominator\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment resultsFragment on PastRace {\n  results {\n    runners {\n      biNumber\n      betAmount\n      runnerNumber\n      finishPosition\n      runnerName\n      winPayoff\n      placePayoff\n      showPayoff\n      __typename\n    }\n    payoffs {\n      wagerAmount\n      selections {\n        payoutAmount\n        selection\n        __typename\n      }\n      wagerType {\n        code\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment pastRacesFragment on PastRace {\n  number\n  description\n  purse\n  date\n  postTime\n  track {\n    code\n    name\n    __typename\n  }\n  surface {\n    code\n    name\n    __typename\n  }\n  distance {\n    value\n    code\n    name\n    __typename\n  }\n  isGreyhound\n  type {\n    id\n    code\n    name\n    __typename\n  }\n  raceClass {\n    code\n    name\n    __typename\n  }\n  video {\n    replayFileName\n    __typename\n  }\n  __typename\n}\n',
    'variables': {
        'byDate': False,
        'byDateTrack': False,
        'byDateTrackNumber': True,
        'byHorseName': False,
        'date': '2022-03-12',
        'filterBy': {},
        'raceNumber': 10, # try an invalid number later, like 11
        'trackCode': 'FON',
        'wagerProfile': 'PORT-Generic'
    }
}

resp = requests.post('https://service.tvg.com/fcp/v1/query', data=payload)
print(resp.status_code)