[![GitHub release](https://img.shields.io/badge/Download-Release%20v0.3-lightgrey.svg?style=social)](https://github.com/randyoyarzabal/plex_light/releases/latest) [![GitHub commits (since latest release)](https://img.shields.io/github/commits-since/randyoyarzabal/plex_light/latest.svg?style=social)](https://github.com/randyoyarzabal/plex_light/commits/master)

# Automated Plex Lighting Control
A webhook application for for [Plex Media Center](http://plex.tv) to automatically control home theater lighting 
(i.e. Leviton Decora) triggered by media (movies, episodes, trailer/pre-roll) events, such as play, pause, 
stop and even media endings.

## Features
- Basic mode: detection and actions for play, pause, stop, and end (90%) of movies and shows.
- Advanced mode: detection of basic features plus actions for clips (trailers or pre-roll).
- Automation only runs at specified times of day so lights aren't controlled in the middle of the day.
- Supports multiple Plex players at a time.
- Only implemented support for [Leviton Decora](http://www.leviton.com/en/products/lighting-controls/decora-smart-with-wifi) 
line of light switches, but feel free to request a pull to contribute code for other dimmer switches by implementing
a concrete subclass of [AbstractPlexHook.py](../plex/AbstractPlexHook.py).

## Quick Start
- Define a configuration file (simply make copy of [.env_sample](../.env_sample) as a new `.env` file.
- Configure the variables in `.env` as appropriate for your use.
- Follow the installation instructions below.
- Run the app: `plex_light.py` 
- Define the full URL as webhook in the Plex configuration. Enjoy!

***Caution:*** if you intend this app to control lights based on trailer/pre-roll events, you need to make sure that 
pre-rolls are defined in Plex Settings (Extras). That is, if trailers are defined, and you intend to have dim lighting 
(for example) for trailers and lights-off for the movie, then you are required to have pre-rolls enabled in Plex. 
*But why, you might ask?* It is because Plex decided to send a "media.play" event ONLY when playback is invoked right 
before the trailers and pre-roll. It is therefore impossible to detect when a movie is about to start, unless you have 
a pre-roll, then this app will detect the end of that, and therefore turn off the lights before the movie starts.  

Long story short, if you have trailer/pre-roll enabled, `CONTROL_MODE` should be set to `Advanced`, otherwise leave 
as `Basic` if you don't.

## Installation

***Please note that while the "master" branch is a working version tested with Python 3.7 on CentOS and MacOS, 
documentation and code clean-up is in-progress.***

### Stand-alone Installation

- Define required environment variables by creating a copy of [.env_sample](../.env_sample) as a new `.env` file.
- Install prerequisite packages from [requirements.txt](../requirements.txt) using Python 3+:  
`pip install -r requirements.txt`
- Run the webhook app:  
`plex_light.py`
- Define webhook on your Plex account as: `http://<ip address>:5000/webhook`

### Docker Installation
TBD

### Known Issues/Solutions
There are no known issues in `Basic` mode and where no trailers/pre-roll are enabled in Plex.
However, in `Advanced` mode, there are some issues due to Plex's limitation on playback events when trailers/pre-roll 
are involved:

> Issue #1: Lights turn on (instead of off) when movie starts.   
> Solution: Make sure pre-roll videos are enabled if trailers are enabled. 

> Issue #2: There's a long delay in some/all the actions.
> Solution: Be sure to set `CONTROL_MODE='Basic'` when trailers/pre-roll are disabled or the stop/play delays will be
> in effect.

> Issue #2: Lights turn on and off in between trailers.   
> Solution: Be sure you have `CONTROL_MODE='Advanced'` and pre-roll enabled in Plex.  This could also be a timing issue
on how fast trailers load making the app think you stopped/skipped the trailer. If it bothers you, tweak the 
`PLEX_STOP_ACTION_DELAY` setting to about 2-5.

> Issue #3: Lights turn off then dim right after I play a movie and the trailers start.   
> Solution: This is a timing issue because Plex sends a 'media.play' for a movie, followed by a 'media.play' for a 
trailer. It all depends on how fast Plex can transition from movie play to trailer. If it bothers you, tweak the 
`PLEX_PLAY_ACTION_DELAY` setting to about 5-8.

## Credits

This is based on the idea and code posted by [dwclarknu](https://forums.plex.tv/t/rel-control-leviton-lights/275873) 
on the [Plex Forums](https://forums.plex.tv).  
The library used for [Leviton Decora](http://www.leviton.com/en/products/lighting-controls/decora-smart-with-wifi) 
Smart WiFi Switches &amp; Dimmers is [python-decora_wifi](https://github.com/tlyakhov/python-decora_wifi).
