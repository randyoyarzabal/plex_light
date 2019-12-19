# Automated Plex Lighting Control (plex-light_switch v0.3)
A webhook application for automatically controlling home theater lighting upon movie (also supports trailer/pre-roll 
detection) start, stop, and pause in [Plex Media Center](http://plex.tv).  

## Features
- Standard detection and actions for play, pause, stop of movies and TV shows.
- Advanced detection and actions for clips (trailers or pre-roll) and ending (90%) of a movie.
- Only implemented support for [Leviton Decora](http://www.leviton.com/en/products/lighting-controls/decora-smart-with-wifi) 
line of light switches, but feel free to request a pull to contribute code for other dimmer switches by implementing
a concrete subclass of [AbstractPlexHook.py](AbstractPlexHook.py).

## Quick Start
- Define a configuration file (simply make copy of [.env_sample](.env_sample) as a new `.env` file.
- Configure the variables in `.env` as appropriate for your use.
- Follow the installation instructions below.
- Run the app: `python webhook.py` 
- Define the full URL as webhook in the Plex configuration. Enjoy!

***Caution:*** if you intend this app to control lights based on trailer/pre-roll events, you need to make sure that 
pre-rolls are defined in Plex Settings (Extras). That is, if trailers are defined, and you intend to have dim lighting 
(for example) for trailers and lights-off for the movie, then you are required to have pre-rolls enabled in Plex. 
*But why, you might ask?* It is because Plex decided to send a "media.play" event ONLY when playback is invoked right 
before the trailers and pre-roll. It is therefore impossible to detect when a movie is about to start, unless you have 
a pre-roll, then this app will detect the end of that, and therefore turn off the lights before the movie starts.  

Long story short, leave `ADVANCED_CONTROL` setting to `false` if you don't have pre-rolls enabled.

## Installation

***Please note that while the "master" branch is a working version tested with Python 3.7 on CentOS and MacOS, 
documentation and code clean-up is in-progress.***

### Stand-alone Installation

- Define required environment variables by creating a copy of [.env_sample](.env_sample) as a new `.env` file.
- Install prerequisite packages from [requirements.txt](requirements.txt) using Python 3+:  
`pip install -r requirements.txt`
- Run the webhook app:  
`python webhook.py`
- Define webhook on your Plex account as: `http://<ip address>:5000/webhook`

### Docker Installation
TBD

### Known Issues/Solutions

- Issue #1: 
> Solution:
- Issue #2:
> Solution:

## Credits

This is based on the idea and code posted by [dwclarknu](https://forums.plex.tv/t/rel-control-leviton-lights/275873) 
on the [Plex Forums](https://forums.plex.tv).  
The library used for [Leviton Decora](http://www.leviton.com/en/products/lighting-controls/decora-smart-with-wifi) 
Smart WiFi Switches &amp; Dimmers is [python-decora_wifi](https://github.com/tlyakhov/python-decora_wifi).
