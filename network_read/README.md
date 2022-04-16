
======

Plan:

under each directory of date/track/number:
- real-time pools csv:
    - have a csv for each race, organized by date/track/number.
    - each row is a data point of pools
- daily data:
    - everything from getRaceResults.
        - details
        - results
        - racecard
        - pools
        - (maybe) probables
        - (maybe) will pays
        - anything else

For real-time pools data, gather enough days of data.
- For each csv, I need to clean it to have data points fall on intervals (0,15,30,45).
- See if I can predict future pools, given race info.
    - This means I'll need to include all of the other information about the race.
    - I need to store the race program info alongside the real-time pools data.

======

`read.py` (don't use) opens the races in chrome tabs and listens to the requests. It's very slow.
`read2.py` calls the APIs directly and is very clean.

======

Have a tab open on the race schedule. Every time `getLHNRaces` or `getRacesMtpStatus` request is made, get the up-to-date list of races with <60 MTP. The response will include the track_id, track name, and race number for each race.
- Use those 3 values to get the race program URL. Open a new tab with that URL and start polling for races.

*** How do I parallelize polling? ***
- first keep a monitor open on the schedules page.

When do I know to close a tab?
- if `getRaceProgram` doesn't show up for 2 minutes, close the tab. It should show up if (0 <= MTP < 60), even if the values don't change.

What do I do if the pools are missing?
- biPools field will be null. In that case, just mark it as 0.

- upon detecting a race with MTP <= 5, record its unique trackCode+number and add it to a set, if it's not there already. then open a tab for it.
- for each tab (race with <= 5 MTP), collect the trend until data points stop coming. Then close the tab.
- or maybe a "race finished" query will show?
- eventually, I'll make a prediction of the final 