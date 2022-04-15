
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