
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

def getRaceProgram_payload(track_id: str, race_number: str):
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
            "withHandicapping": False,
            "withLateChanges": True,
            "withPools": True,
            "withProbables": True,
            "withRaces": False,
            "withResults": False,
            "withWagerTypes": False,
            "withWillPays": False
        }
    }