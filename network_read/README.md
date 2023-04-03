
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
- to kill a screen session, `screen -X -S <screen_id> kill`

`read_hist.py` - downloads historical static data
- `python3 read_hist.py 2022-05-31 2022-04-20`
- first date is start_date (future). second date is end_date (past). so it gathers data while moving backwards in time.
- it doesn't stop for some reason, even after ctrl-c