import requests
import json

##### getRacesMtpStatus #####

getRacesMtpStatus_payload = {
    "operationName": "getRacesMtpStatus",
    "query": "query getRacesMtpStatus($wagerProfile: String, $sortBy: RaceListSort, $filterBy: RaceListFilter, $page: Pagination) {\n  raceDate\n  mtpRaces: races(filter: $filterBy, profile: $wagerProfile, sort: $sortBy) {\n    number\n    mtp\n    trackCode\n    trackName\n    postTime\n    track {\n      perfAbbr\n      __typename\n    }\n    status {\n      code\n      __typename\n    }\n    __typename\n  }\n  nextRace: races(page: $page, profile: $wagerProfile, sort: $sortBy) {\n    number\n    mtp\n    trackCode\n    trackName\n    postTime\n    track {\n      perfAbbr\n      __typename\n    }\n    status {\n      code\n      __typename\n    }\n    __typename\n  }\n}\n",
    "variables": {
        "filterBy": {
            "startIn": 60,
            "status": ["MO","O","IC"], # leave out SK (recently finished races, I think)
        },
        "page": {
            "current": 0,
            "results": 1,
        },
        "sortBy": {
            "byPostTime": "ASC",
        },
        "wagerProfile": "PORT-Generic",
    }
}
def getRacesMtpStatus():
    try:
        url = 'https://service.tvg.com/graph/v2/query'
        resp = requests.post(url, data=json.dumps(getRacesMtpStatus_payload))
        # print(resp.status_code)
        resp = json.loads(resp.text)
        return resp
    except:
        return None

##### getRaceProgram #####

"""
withBettingInterests:   race['bettingInterests']
withBiPools:            race['bettingInterests'][i]['biPools']. Only appears if "withBettingInterests" is true. Shows pools size for different types of wagers.
withDetails:            Basically all of the fields in the details row on the webpage. also includes vido info.
withHandicapping:       race['bettingInterests'][i]['runners'][i]['handicapping']. Only appears if "withBettingInterests" is true. Shows all of the racecard info.
withLateChanges:        race['lateChanges']
withPools:              race['racePools']. Includes id info for each wager type.
withProbables:          race['probables']
withRaces:              race['track']['races']. Includes basic race info for each number of that track.
withResults:            race['results']. Gives the results table. null if race is not finished.
withWagerTypes:         race['wagerTypes']
withWillPays:           race['willPays']. Maybe be null if the race doesn't have will pays.
"""

def getRaceProgramLive_payload(track_id: str, race_number: str):
    return {
        "operationName": "getRaceProgram",
        "query": "query getRaceProgram($trackAbbr: String, $raceNumber: String, $wagerProfile: String, $withRaces: Boolean!, $withResults: Boolean!, $withBettingInterests: Boolean!, $withLateChanges: Boolean!, $withProbables: Boolean!, $withPools: Boolean!, $withWagerTypes: Boolean!, $withHandicapping: Boolean!, $withDetails: Boolean!, $withWillPays: Boolean!, $withBiPools: Boolean!, $isGreyhound: Boolean!, $product: String, $brand: String) {\n  race(track: $trackAbbr, number: $raceNumber, profile: $wagerProfile) {\n    number\n    mtp\n    tvgRaceId\n    postTime\n    status {\n      code\n      __typename\n    }\n    promos(product: $product, brand: $brand) {\n      rootParentPromoID\n      isAboveTheLine\n      promoPath\n      isPromoTagShown\n      __typename\n    }\n    isGreyhound\n    ...detailsFragment @include(if: $withDetails)\n    track {\n      name\n      code\n      perfAbbr\n      featured\n      trackDataSource\n      location {\n        country\n        __typename\n      }\n      ...racesFragment @include(if: $withRaces)\n      __typename\n    }\n    ...poolsFragment @include(if: $withPools)\n    ...probablesFragment @include(if: $withProbables)\n    ...bettingInterestsFragment @include(if: $withBettingInterests)\n    ...lateChangesFragment @include(if: $withLateChanges)\n    ...resultsFragment @include(if: $withResults)\n    ...wagerTypesFragment @include(if: $withWagerTypes)\n    ...willPaysFragment @include(if: $withWillPays)\n    __typename\n  }\n}\n\nfragment detailsFragment on Race {\n  description\n  distance\n  purse\n  numRunners\n  surface {\n    id\n    name\n    defaultCondition\n    __typename\n  }\n  type {\n    id\n    code\n    name\n    __typename\n  }\n  claimingPrice\n  raceClass {\n    id\n    name\n    __typename\n  }\n  video {\n    liveStreaming\n    onTvg\n    onTvg2\n    hasReplay\n    replays\n    streams\n    replayFileName\n    isStreamHighDefinition\n    flashAvailable\n    mobileAvailable\n    __typename\n  }\n  __typename\n}\n\nfragment racesFragment on Track {\n  races(filter: {isGreyhound: $isGreyhound}, sort: {byPostTime: ASC}) {\n    number\n    bettingInterests {\n      biNumber\n      saddleColor\n      favorite\n      numberColor\n      currentOdds {\n        numerator\n        denominator\n        __typename\n      }\n      morningLineOdds {\n        numerator\n        denominator\n        __typename\n      }\n      runners {\n        horseName\n        jockey\n        runnerId\n        scratched\n        dob\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment handicappingFragment on Runner {\n  horseName\n  jockey\n  trainer\n  ownerName\n  weight\n  med\n  ownerName\n  sire\n  damSire\n  dam\n  age\n  sex\n  handicapping {\n    speedAndClass {\n      avgClassRating\n      highSpeed\n      avgSpeed\n      lastClassRating\n      avgDistance\n      __typename\n    }\n    averagePace {\n      finish\n      numRaces\n      middle\n      early\n      __typename\n    }\n    jockeyTrainer {\n      places\n      jockeyName\n      trainerName\n      shows\n      wins\n      starts\n      __typename\n    }\n    snapshot {\n      powerRating\n      daysOff\n      horseWins\n      horseStarts\n      __typename\n    }\n    freePick {\n      number\n      info\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment bettingInterestsFragment on Race {\n  bettingInterests {\n    biNumber\n    saddleColor\n    numberColor\n    ...biPoolsFragment @include(if: $withBiPools)\n    currentOdds {\n      numerator\n      denominator\n      __typename\n    }\n    favorite\n    morningLineOdds {\n      numerator\n      denominator\n      __typename\n    }\n    runners {\n      runnerId\n      scratched\n      dob\n      ...handicappingFragment @include(if: $withHandicapping)\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment poolsFragment on Race {\n  racePools {\n    wagerType {\n      name\n      id\n      __typename\n    }\n    amount\n    __typename\n  }\n  __typename\n}\n\nfragment probablesFragment on Race {\n  probables {\n    betCombos {\n      runner1\n      runner2\n      payout\n      __typename\n    }\n    minWagerAmount\n    wagerType {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment lateChangesFragment on Race {\n  lateChanges {\n    raceChanges {\n      description\n      date\n      newValue\n      oldValue\n      __typename\n    }\n    horseChanges {\n      horseName\n      runnerId\n      changes {\n        description\n        date\n        newValue\n        oldValue\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment resultsFragment on Race {\n  results {\n    payoffs {\n      selections {\n        payoutAmount\n        selection\n        __typename\n      }\n      wagerAmount\n      wagerType {\n        id\n        name\n        __typename\n      }\n      __typename\n    }\n    runners {\n      betAmount\n      runnerNumber\n      biNumber\n      finishPosition\n      placePayoff\n      runnerName\n      showPayoff\n      winPayoff\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment wagerTypesFragment on Race {\n  wagerTypes {\n    maxWagerAmount\n    minWagerAmount\n    wagerAmounts\n    hasPool\n    poolAmount\n    columnCount\n    legCount\n    minBIsPerLeg\n    maxBIsPerLeg\n    columnType\n    isBox\n    poolsPerBI\n    isKey\n    positionCount\n    isWheel\n    type {\n      id\n      code\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment willPaysFragment on Race {\n  willPays {\n    wagerAmount\n    payOffType\n    type {\n      id\n      code\n      name\n      __typename\n    }\n    legResults {\n      legNumber\n      winningBi\n      __typename\n    }\n    payouts {\n      bettingInterestNumber\n      payoutAmount\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment biPoolsFragment on BettingInterest {\n  biPools {\n    poolRunnersData {\n      amount\n      __typename\n    }\n    wagerType {\n      id\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n",
        "variables": {
            "brand": "tvg",
            "forceFetch": True,
            "isGreyhound": False,
            "product": "tvg4",
            "queryOptions": {
                "brand": "tvg",
                "product": "tvg4",
                "withBettingInterests": True,
                "withBiPools": True,
                "withLateChanges": True,
                "withPools": True,
                "withProbables": True
            },
            "raceNumber": race_number,
            "trackAbbr": track_id,
            "wagerProfile": "PORT-Generic",
            "withBettingInterests": True,
            "withBiPools": True,
            "withDetails": False,
            "withHandicapping": True,
            "withLateChanges": False,
            "withPools": True,
            "withProbables": True,
            "withRaces": False,
            "withResults": True, # results is static, but I include to know when to close a race.
            "withWagerTypes": True,
            "withWillPays": True
        }
    }
def getRaceProgramStatic_payload(track_id: str, race_number: str):
    return {
        "operationName": "getRaceProgram",
        "query": "query getRaceProgram($trackAbbr: String, $raceNumber: String, $wagerProfile: String, $withRaces: Boolean!, $withResults: Boolean!, $withBettingInterests: Boolean!, $withLateChanges: Boolean!, $withProbables: Boolean!, $withPools: Boolean!, $withWagerTypes: Boolean!, $withHandicapping: Boolean!, $withDetails: Boolean!, $withWillPays: Boolean!, $withBiPools: Boolean!, $isGreyhound: Boolean!, $product: String, $brand: String) {\n  race(track: $trackAbbr, number: $raceNumber, profile: $wagerProfile) {\n    number\n    mtp\n    tvgRaceId\n    postTime\n    status {\n      code\n      __typename\n    }\n    promos(product: $product, brand: $brand) {\n      rootParentPromoID\n      isAboveTheLine\n      promoPath\n      isPromoTagShown\n      __typename\n    }\n    isGreyhound\n    ...detailsFragment @include(if: $withDetails)\n    track {\n      name\n      code\n      perfAbbr\n      featured\n      trackDataSource\n      location {\n        country\n        __typename\n      }\n      ...racesFragment @include(if: $withRaces)\n      __typename\n    }\n    ...poolsFragment @include(if: $withPools)\n    ...probablesFragment @include(if: $withProbables)\n    ...bettingInterestsFragment @include(if: $withBettingInterests)\n    ...lateChangesFragment @include(if: $withLateChanges)\n    ...resultsFragment @include(if: $withResults)\n    ...wagerTypesFragment @include(if: $withWagerTypes)\n    ...willPaysFragment @include(if: $withWillPays)\n    __typename\n  }\n}\n\nfragment detailsFragment on Race {\n  description\n  distance\n  purse\n  numRunners\n  surface {\n    id\n    name\n    defaultCondition\n    __typename\n  }\n  type {\n    id\n    code\n    name\n    __typename\n  }\n  claimingPrice\n  raceClass {\n    id\n    name\n    __typename\n  }\n  video {\n    liveStreaming\n    onTvg\n    onTvg2\n    hasReplay\n    replays\n    streams\n    replayFileName\n    isStreamHighDefinition\n    flashAvailable\n    mobileAvailable\n    __typename\n  }\n  __typename\n}\n\nfragment racesFragment on Track {\n  races(filter: {isGreyhound: $isGreyhound}, sort: {byPostTime: ASC}) {\n    number\n    bettingInterests {\n      biNumber\n      saddleColor\n      favorite\n      numberColor\n      currentOdds {\n        numerator\n        denominator\n        __typename\n      }\n      morningLineOdds {\n        numerator\n        denominator\n        __typename\n      }\n      runners {\n        horseName\n        jockey\n        runnerId\n        scratched\n        dob\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment handicappingFragment on Runner {\n  horseName\n  jockey\n  trainer\n  ownerName\n  weight\n  med\n  ownerName\n  sire\n  damSire\n  dam\n  age\n  sex\n  handicapping {\n    speedAndClass {\n      avgClassRating\n      highSpeed\n      avgSpeed\n      lastClassRating\n      avgDistance\n      __typename\n    }\n    averagePace {\n      finish\n      numRaces\n      middle\n      early\n      __typename\n    }\n    jockeyTrainer {\n      places\n      jockeyName\n      trainerName\n      shows\n      wins\n      starts\n      __typename\n    }\n    snapshot {\n      powerRating\n      daysOff\n      horseWins\n      horseStarts\n      __typename\n    }\n    freePick {\n      number\n      info\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment bettingInterestsFragment on Race {\n  bettingInterests {\n    biNumber\n    saddleColor\n    numberColor\n    ...biPoolsFragment @include(if: $withBiPools)\n    currentOdds {\n      numerator\n      denominator\n      __typename\n    }\n    favorite\n    morningLineOdds {\n      numerator\n      denominator\n      __typename\n    }\n    runners {\n      runnerId\n      scratched\n      dob\n      ...handicappingFragment @include(if: $withHandicapping)\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment poolsFragment on Race {\n  racePools {\n    wagerType {\n      name\n      id\n      __typename\n    }\n    amount\n    __typename\n  }\n  __typename\n}\n\nfragment probablesFragment on Race {\n  probables {\n    betCombos {\n      runner1\n      runner2\n      payout\n      __typename\n    }\n    minWagerAmount\n    wagerType {\n      id\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment lateChangesFragment on Race {\n  lateChanges {\n    raceChanges {\n      description\n      date\n      newValue\n      oldValue\n      __typename\n    }\n    horseChanges {\n      horseName\n      runnerId\n      changes {\n        description\n        date\n        newValue\n        oldValue\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment resultsFragment on Race {\n  results {\n    payoffs {\n      selections {\n        payoutAmount\n        selection\n        __typename\n      }\n      wagerAmount\n      wagerType {\n        id\n        name\n        __typename\n      }\n      __typename\n    }\n    runners {\n      betAmount\n      runnerNumber\n      biNumber\n      finishPosition\n      placePayoff\n      runnerName\n      showPayoff\n      winPayoff\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment wagerTypesFragment on Race {\n  wagerTypes {\n    maxWagerAmount\n    minWagerAmount\n    wagerAmounts\n    hasPool\n    poolAmount\n    columnCount\n    legCount\n    minBIsPerLeg\n    maxBIsPerLeg\n    columnType\n    isBox\n    poolsPerBI\n    isKey\n    positionCount\n    isWheel\n    type {\n      id\n      code\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment willPaysFragment on Race {\n  willPays {\n    wagerAmount\n    payOffType\n    type {\n      id\n      code\n      name\n      __typename\n    }\n    legResults {\n      legNumber\n      winningBi\n      __typename\n    }\n    payouts {\n      bettingInterestNumber\n      payoutAmount\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment biPoolsFragment on BettingInterest {\n  biPools {\n    poolRunnersData {\n      amount\n      __typename\n    }\n    wagerType {\n      id\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n",
        "variables": {
            "brand": "tvg",
            "forceFetch": True,
            "isGreyhound": False,
            "product": "tvg4",
            "queryOptions": {
                "brand": "tvg",
                "product": "tvg4",
                "withBettingInterests": True,
                "withBiPools": True,
                "withLateChanges": True,
                "withPools": True,
                "withProbables": True
            },
            "raceNumber": race_number,
            "trackAbbr": track_id,
            "wagerProfile": "PORT-Generic",
            "withBettingInterests": True,
            "withBiPools": True,
            "withDetails": True,
            "withHandicapping": True,
            "withLateChanges": False,
            "withPools": True,
            "withProbables": True,
            "withRaces": True,
            "withResults": True,
            "withWagerTypes": True,
            "withWillPays": False
        }
    }
def getRaceProgram(track_id: str, race_number: str, live=False):
    url = 'https://service.tvg.com/graph/v2/query'
    try:
        if live:
            resp = requests.post(url, data=json.dumps(getRaceProgramLive_payload(track_id, race_number)))
        else:
            resp = requests.post(url, data=json.dumps(getRaceProgramStatic_payload(track_id, race_number)))
        # print(resp.status_code)
        resp = json.loads(resp.text)
        return resp
    except:
        return None

# getPastTracks

def getPastTracks_payload(date_str):
    return {
        "operationName": "getPastTracks",
        "query": "query getPastTracks($wagerProfile: String!, $filterBy: PastTrackListFilter, $allTracks: Boolean!, $date: String, $byDate: Boolean!, $trackCode: String, $byCode: Boolean!, $withDates: Boolean!) {\n  allPastTracks: pastTracks(profile: $wagerProfile, filter: $filterBy) @include(if: $allTracks) {\n    ...pastTracksFragment\n    __typename\n  }\n  pastTracksByDate: pastTracks(profile: $wagerProfile, filter: $filterBy, date: $date) @include(if: $byDate) {\n    ...pastTracksFragment\n    __typename\n  }\n  pastTrackByTrackCode: pastTracks(profile: $wagerProfile, filter: $filterBy, trackCode: $trackCode) {\n    ...pastTracksFragment @include(if: $byCode)\n    ...trackDatesFragment @include(if: $withDates)\n    __typename\n  }\n}\n\nfragment trackDatesFragment on PastTrack {\n  dates\n  __typename\n}\n\nfragment pastTracksFragment on PastTrack {\n  code\n  name\n  location {\n    city\n    state\n    country\n    __typename\n  }\n  imageName\n  imageLink\n  __typename\n}\n",        "variables": {
            "allTracks": False,
            "byCode": False,
            "byDate": True,
            "date": date_str,
            "filterBy": {
                "isGreyhound": False,
            },
            "trackCode": "",
            "wagerProfile": "PORT-Generic",
            "withDates": True,
        }
    }

def getPastTracks(date_str):
    url = 'https://service.tvg.com/fcp/v1/query'
    try:
        resp = requests.post(url, data=json.dumps(getPastTracks_payload(date_str)))
        resp = json.loads(resp.text)
        return resp
    except:
        return None

# getPastRaces

def getPastRacesDateTrack_payload(date_str, track_id):
    return {
        "operationName": "getPastRaces",
        "query": "query getPastRaces($filterBy: PastRaceListFilter, $wagerProfile: String!, $byDate: Boolean!, $byDateTrack: Boolean!, $date: String, $trackCode: String, $byDateTrackNumber: Boolean!, $raceNumber: String, $byHorseName: Boolean!, $runnerName: String, $runnerDob: Int) {\n  pastRacesByDate: pastRaces(filter: $filterBy, profile: $wagerProfile, date: $date, sort: {byPostTime: DESC}) @include(if: $byDate) {\n    ...pastRacesFragment\n    __typename\n  }\n  pastRacesByDateAndTrack: pastRaces(filter: $filterBy, profile: $wagerProfile, date: $date, trackCode: $trackCode, sort: {byPostTime: DESC}) @include(if: $byDateTrack) {\n    ...pastRacesFragment\n    __typename\n  }\n  pastRaceByDateTrackAndNumber: pastRaces(filter: $filterBy, profile: $wagerProfile, date: $date, trackCode: $trackCode, raceNumber: $raceNumber, sort: {byPostTime: DESC}) @include(if: $byDateTrackNumber) {\n    ...pastRacesFragment\n    ...bettingInterestsFragment\n    ...resultsFragment\n    __typename\n  }\n  pastRacesByHorseName: pastRaces(filter: $filterBy, runnerName: $runnerName, profile: $wagerProfile, sort: {byPostTime: DESC}, runnerDob: $runnerDob) @include(if: $byHorseName) {\n    ...pastRacesFragment\n    __typename\n  }\n}\n\nfragment bettingInterestsFragment on PastRace {\n  bettingInterests {\n    biNumber\n    numberColor\n    saddleColor\n    favorite\n    runners {\n      horseName\n      runnerId\n      weight\n      med\n      trainer\n      age\n      dam\n      ownerName\n      sex\n      scratched\n      jockey\n      damSire\n      sire\n      date\n      dob\n      __typename\n    }\n    morningLineOdds {\n      numerator\n      denominator\n      __typename\n    }\n    currentOdds {\n      numerator\n      denominator\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment resultsFragment on PastRace {\n  results {\n    runners {\n      biNumber\n      betAmount\n      runnerNumber\n      finishPosition\n      runnerName\n      winPayoff\n      placePayoff\n      showPayoff\n      __typename\n    }\n    payoffs {\n      wagerAmount\n      selections {\n        payoutAmount\n        selection\n        __typename\n      }\n      wagerType {\n        code\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment pastRacesFragment on PastRace {\n  number\n  description\n  purse\n  date\n  postTime\n  track {\n    code\n    name\n    __typename\n  }\n  surface {\n    code\n    name\n    __typename\n  }\n  distance {\n    value\n    code\n    name\n    __typename\n  }\n  isGreyhound\n  type {\n    id\n    code\n    name\n    __typename\n  }\n  raceClass {\n    code\n    name\n    __typename\n  }\n  video {\n    replayFileName\n    __typename\n  }\n  __typename\n}\n",        "variables": {
            "byDate": False,
            "byDateTrack": True,
            "byDateTrackNumber": False,
            "byHorseName": False,
            "date": date_str,
            "filterBy": {
                "isGreyhound": False,
            },
            "trackCode": track_id,
            "wagerProfile": "PORT-Generic",
        }
    }

def getPastRacesDateTrackNumber_payload(date_str, track_id, race_number):
    return {
        "operationName": "getPastRaces",
        "query": "query getPastRaces($filterBy: PastRaceListFilter, $wagerProfile: String!, $byDate: Boolean!, $byDateTrack: Boolean!, $date: String, $trackCode: String, $byDateTrackNumber: Boolean!, $raceNumber: String, $byHorseName: Boolean!, $runnerName: String, $runnerDob: Int) {\n  pastRacesByDate: pastRaces(filter: $filterBy, profile: $wagerProfile, date: $date, sort: {byPostTime: DESC}) @include(if: $byDate) {\n    ...pastRacesFragment\n    __typename\n  }\n  pastRacesByDateAndTrack: pastRaces(filter: $filterBy, profile: $wagerProfile, date: $date, trackCode: $trackCode, sort: {byPostTime: DESC}) @include(if: $byDateTrack) {\n    ...pastRacesFragment\n    __typename\n  }\n  pastRaceByDateTrackAndNumber: pastRaces(filter: $filterBy, profile: $wagerProfile, date: $date, trackCode: $trackCode, raceNumber: $raceNumber, sort: {byPostTime: DESC}) @include(if: $byDateTrackNumber) {\n    ...pastRacesFragment\n    ...bettingInterestsFragment\n    ...resultsFragment\n    __typename\n  }\n  pastRacesByHorseName: pastRaces(filter: $filterBy, runnerName: $runnerName, profile: $wagerProfile, sort: {byPostTime: DESC}, runnerDob: $runnerDob) @include(if: $byHorseName) {\n    ...pastRacesFragment\n    __typename\n  }\n}\n\nfragment bettingInterestsFragment on PastRace {\n  bettingInterests {\n    biNumber\n    numberColor\n    saddleColor\n    favorite\n    runners {\n      horseName\n      runnerId\n      weight\n      med\n      trainer\n      age\n      dam\n      ownerName\n      sex\n      scratched\n      jockey\n      damSire\n      sire\n      date\n      dob\n      handicapping {\n    speedAndClass {\n      avgClassRating\n      highSpeed\n      avgSpeed\n      lastClassRating\n      avgDistance\n      __typename\n    }\n    averagePace {\n      finish\n      numRaces\n      middle\n      early\n      __typename\n    }\n    jockeyTrainer {\n      places\n      jockeyName\n      trainerName\n      shows\n      wins\n      starts\n      __typename\n    }\n    snapshot {\n      powerRating\n      daysOff\n      horseWins\n      horseStarts\n      __typename\n    }\n    freePick {\n      number\n      info\n      __typename\n    }\n    __typename\n  }\n    __typename\n    }\n    morningLineOdds {\n      numerator\n      denominator\n      __typename\n    }\n    currentOdds {\n      numerator\n      denominator\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment resultsFragment on PastRace {\n  results {\n    runners {\n      biNumber\n      betAmount\n      runnerNumber\n      finishPosition\n      runnerName\n      winPayoff\n      placePayoff\n      showPayoff\n      __typename\n    }\n    payoffs {\n      wagerAmount\n      selections {\n        payoutAmount\n        selection\n        __typename\n      }\n      wagerType {\n        code\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment pastRacesFragment on PastRace {\n  number\n  description\n  purse\n  date\n  postTime\n  track {\n    code\n    name\n    __typename\n  }\n  surface {\n    code\n    name\n    __typename\n  }\n  distance {\n    value\n    code\n    name\n    __typename\n  }\n  isGreyhound\n  type {\n    id\n    code\n    name\n    __typename\n  }\n  raceClass {\n    code\n    name\n    __typename\n  }\n  video {\n    replayFileName\n    __typename\n  }\n  __typename\n}\n",        "variables": {
            "byDate": False,
            "byDateTrack": False,
            "byDateTrackNumber": True,
            "byHorseName": False,
            "date": date_str,
            "trackCode": track_id,
            "raceNumber": race_number,
            "wagerProfile": "PORT-Generic",
        }
    }

def getPastRaces(date_str, track_id=None, race_number=None):
    url = 'https://service.tvg.com/fcp/v1/query'
    try:
        if track_id != None and race_number == None:
            resp = requests.post(url, data=json.dumps(getPastRacesDateTrack_payload(date_str, track_id)))
        elif track_id != None and race_number != None:
            resp = requests.post(url, data=json.dumps(getPastRacesDateTrackNumber_payload(date_str, track_id, race_number)))
        resp = json.loads(resp.text)
        return resp
    except:
        return None