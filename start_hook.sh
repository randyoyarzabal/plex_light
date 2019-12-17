#!/usr/bin/env bash

# This requires a ".env" file containing the following variables:

## These are example values only.
#DECORA_USER='myemail@domain.com'
#DECORA_PASS='mypassword'
#DECORA_RESIDENCE='My Home'
#DECORA_SWITCH='Home Theater Dimmer'
#PLEX_PLAYER='SHIELD Android TV'
#
## We can either use Activities
## Plex Trigger Activities on the My Leviton App
#PLEX_PLAY_ACTIVITY='Plex Movie Play'
#PLEX_PAUSE_ACTIVITY='Plex Movie Pause'
#PLEX_STOP_ACTIVITY='Plex Movie Stop'
#
## OR, we can use direct brightness settings.
## Plex Trigger Activities on the My Leviton App
#PLEX_PLAY_BRIGHTNESS=0
#PLEX_PAUSE_BRIGHTNESS=30
#PLEX_STOP_BRIGHTNESS=100

# Not needed if "python-dotenv" is installed.
source .env

# Start the webhook
python webhook.py