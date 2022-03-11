#!/usr/local/bin/bash
now=$(date +"%y-%m-%d")
log="./logs/log_$now.txt"
touch $log
/usr/local/bin/python ./main.py &>> $log
