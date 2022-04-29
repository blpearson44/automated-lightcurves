#!/usr/bin/bash
now=$(date +"%y-%m-%d")
log="/home/bpearson/Projects/IP-monitoring/Output/logs/log_$now.txt"
dropbox="/home/bpearson/Dropbox/IP-monitoring-output/"
touch $log
/opt/local/anaconda3/bin/python /home/bpearson/Projects/IP-monitoring/run_wcs.py &>> $log
cp -r /home/bpearson/Projects/IP-monitoring/Output/logs/ $dropbox/
cp /home/bpearson/Projects/IP-monitoring/Output/*.csv $dropbox/data/
cp /home/bpearson/Projects/IP-monitoring/Output/*.png $dropbox/plots/
cp -r /home/bpearson/Projects/IP-monitoring/Output/indexes/ $dropbox/
