#!/usr/bin/bash
now=$(date +"%y-%m-%d")
log="./Output/logs/log_$now.txt"
touch $log
/opt/local/anaconda3/bin/python ./run_non_wcs.py &>> $log
cp -r ./Output/logs/ ./Dropbox/logs/
cp ./Output/*.csv ./Dropbox/
cp ./Output/*.png ./Dropbox/
