#!/bin/sh

#Description : relog the bot

cd "$(dirname "$0")"
dirname "$0"

python ./pywiki/scripts/login.py -oauth

