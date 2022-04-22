
`cd horseracing/network_read`
`python3 read2.py`

`read.py` - old version that scrapes from the webpage.
`read2.py` - default
`read3.py` - writes to s3
- connect to EC2
- run `screen` to open a new screen.
- run `python3 ./horseracing/network_read/read3.py`
- press ctrl+A, then press d. this detaches the screen I just opened and lets it run in the background.
- I can now safely cut the connection with the ec2 instance and the program should continue to run.
- run `screen -r` to resume the session with the program. all the output should be there.
- more about screen: https://stackoverflow.com/questions/32500498/how-to-make-a-process-run-on-aws-ec2-even-after-closing-the-local-machine
`read_hist.py` - downloads historical static data
- `python3 read_hist.py 2022-04-20 2022-04-20`
- it doesn't stop for some reason, even after ctrl-c

======

I need to detect 1A and stuff within get_live_race_data. If I find one, I need to return and remove the race from open_races.

One idea is to include win, place, and show pools into features.

Add timeout for each open race.

Look into running the code on EC2. Should be cheap.
- Think about how to restart if the program crashes.
- Find out how to start the code at 1 AM each day and stop at 11:30 PM.
Find out how to save csvs directly to S3.
Make sure that the gathered data is valid.


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

what happens if I call getRaceResults before the race has finished?
- I want to know if there is an indication of a race being finished. That way I know when to stop
    getting real-time pool data for a race and get all of the race program data at the end.

I have to think about which data is changing in real-time and which data will be the same throughout.

every 10 seconds, run
- get latest races
    - (only do this later for online mode) whenever I onboard a new race, get the race program info.
- get live race data
    - if results is not null, then save the live df to date/track/number when the race is closed.
        - close the race and get the final race program info and save it to csv.
    - each sample is a row in the dataframe for a race. I need to maintain a dataframe for each race.

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