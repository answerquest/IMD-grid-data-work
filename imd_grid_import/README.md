# IMD Gridded data import to a PostGreSQL DB

## Steps to start the program:

1. See sample_launch.sh
2. Replace the dummy credentials in it with proper credentials. Note, the credentials are needed in docker command at bottom also.
3. Rename the sample shell script and populate it with proper DB credentials etc. Also replace the persistent volume paths (left side of : in -v lines) with full path on the machine of a folder. Put in "" quotes in case the path has a space in it.
4. Run the docker command first. Skip if you already have a postgresql DB and using its credentials.
5. To inspect what's happening inside the postgresql docker, replace "-d" with "--rm -it" and run - then its running in your terminal instead of background. Leave this running and start another terminal tab to do the rest.
6. Create the tables in the DB. Connect to the DB using PGAdmin or other ways, and run the contents of dbschema.sql in it.
7. Supposing you've renamed the sample shell script to "launch.sh". Apply execute permissions to it.
```
sudo chmod +x launch.sh
```
8. Now run the shell script. (You could run the python file directly, but we need those env params loaded prior)
```
./launch.sh
```
9. If you want to leave this running in background, do like so:
```
nohup ./launch.sh &
```
10. You can monitor progress by:
```
tail -f logs/log.txt
```
11. Ensure you have about 15GBs free space where you're running this, for data downloads and DB combined. If re-run, the program won't re-download data that has already been downloaded.
12. If you see errors like so and so package / lib is missing, pls install them.
```
pip3 install -r requirements.txt
```

## Warnings / Notes

A. The time.sleep(5) is there so that IMD website doesn't ban your IP address forever (which could be your home or your entire college/school lol), or worse, take the gridded data download page offline. Don't expect this to be faster; instead leave it running overnight and check back next morning.


B. Imp For College profs etc : DO NOT GIVE the downloading task as an assignment for each and every student to run -> complete bandwidth waste and server overload. Instead, you can take just the relevant download lines, run the script once at your end, have the data files gathered (will be about 10GB) and then distribute those to your class by pen drive / shared LAN folder etc. After they've placed the "tmax", "tmin", "rain" data folders in their system next to the program, THEN it's ok to run the program.


B. Change the starting and ending years for temperature and rainfall as per your requirements, in the shell script / env params. In first runs when you're trying things out, better to reduce the years-span to just one or two. (Seriously, if you only want some years of data, do NOT run it for the entire century. It takes a long time and lot of HDD space and bandwidth to load up all the years.


C. If you're on windows instead of linux (God help you), then pls make a windows version of this all and do. Contributions welcome. And please consider dual-booting your machine with ubuntu / linux mint for coding - it's way better in lib compatibilities and won't put exotic blockers in your way like windows does. Mac users - most linux commands work well at your end so meh.


## Temperature-only script
Addendum: Since temperature data is a much smaller amount and its locations are also lesser, I made a second script to process just that and load up to a separate pair of DB tables: imd_temp_data and temp_grid.

Adapt and run `sample_temponly_launch.sh`.


