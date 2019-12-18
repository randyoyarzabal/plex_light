# Automated Plex Lighting Control (plex-light_switch v0.2)
A webhook application for automatically controlling home theater lighting upon movie start, stop, 
and pause in [Plex Media Center](http://plex.tv).  

## Features
- Standard detection and actions for play, pause, stop of movies and TV shows.
- Advanced detection and actions for trailers, pre-roll clips and ending (90%) of a movie.
- Only implemented support for [Leviton Decora](http://www.leviton.com/en/products/lighting-controls/decora-smart-with-wifi) 
line of light switches, but feel free to request a pull to contribute code for other dimmer switches by implementing
a subclass to [PlexHook.py](plex/PlexHook.py).

## Usage
Getting started is very simple. Define these configuration values below (examples) in a `.env` file, follow the 
installation instructions, run the app, then define the full URL as webhook in Plex. Enjoy!
```bash
# Note that the DECORA* values below are from your MyLeviton App
export DECORA_USER='email'
export DECORA_PASS='password'
export DECORA_RESIDENCE='Your House'
export DECORA_SWITCH='Your Switch'
export PLEX_PLAYER='SHIELD Android TV'
export PLEX_ACTION_DELAY=2
```
You can define "Activities" in your MyLeviton App, then define as follows:
```bash
export PLEX_CLIP_ACTIVITY='Plex Clip Play'
export PLEX_END_ACTIVITY='Plex End Play'
export PLEX_PLAY_ACTIVITY='Plex Movie Play'
export PLEX_PAUSE_ACTIVITY='Plex Movie Pause'
export PLEX_STOP_ACTIVITY='Plex Movie Stop'
```
Or, if you'd rather send "brightness" values, define as follows:
```bash
export PLEX_CLIP_BRIGHTNESS=20
export PLEX_END_BRIGHTNESS=10
export PLEX_PLAY_BRIGHTNESS=0
export PLEX_PAUSE_BRIGHTNESS=35
export PLEX_STOP_BRIGHTNESS=100
```

## Installation

***Please note that while the "master" branch is a working version tested with Python 3.7 on CentOS and MacOS, 
documentation and code clean-up is in-progress.***

### Stand-alone Installation

* Define required environment variables by creating a copy of [.env_sample](.env_sample) as a new `.env` file.
* Install prerequisite packages from [requirements.txt](requirements.txt) using Python 3+:  
`pip install -r requirements.txt`
* Run the webhook app:  
`python webhook.py`
* Define webhook on your Plex account as: `http://<ip address>:5000/webhook`

### Docker Installation
TBD

## Credits

This is based on the idea and code posted by [dwclarknu](https://forums.plex.tv/t/rel-control-leviton-lights/275873) 
on the [Plex Forums](https://forums.plex.tv).  
The library used for [Leviton Decora](http://www.leviton.com/en/products/lighting-controls/decora-smart-with-wifi) 
Smart WiFi Switches &amp; Dimmers is [python-decora_wifi](https://github.com/tlyakhov/python-decora_wifi).
