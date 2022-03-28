#!/usr/bin/bash
now=$(date +"%y-%m-%d")
log="./logs/log_$now.txt"
touch $log
/opt/local/anaconda3/bin/python ./main.py &>> $log
