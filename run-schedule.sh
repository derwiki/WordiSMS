#!/bin/bash

# HOWTO RUN
# From the /var/wordisms/www directory
#  nohup ./run-schedule.sh > ~/run-schedule1.sh.log &
while true; do
    python /var/wordisms/schedule.py
    sleep 5
done
