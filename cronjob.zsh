#!/bin/zsh

today=$(date '+%Y-%m-%d')
echo $today
cd "$(dirname "$0")"
/usr/local/bin/pipenv run python3 parseFeeds.py > logs/"$today.log"

exit
