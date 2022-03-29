#!/usr/bin/bash
now=$(date +"%y-%m-%d")
log="./Output/logs/log_$now.txt"
dropbox="/home/bpearson/Dropbox/IP-monitoring-output/"
touch $log
/opt/local/anaconda3/bin/python ./run_wcs.py &>> $log
cp -r ./Output/logs/ $dropbox/
cp ./Output/*.csv $dropbox/data/
cp ./Output/*.png $dropbox/plots/
cp -r ./Output/indexes/ $dropbox/
