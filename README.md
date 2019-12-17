# Automated Plex Lighting Control
A webhook application for automatically controlling home theater lighting upon movie start, stop, 
and pause in [Plex Media Center](http://plex.tv).  

## Installation

***Please note that while the "master" branch is a working version tested with Python 3.7 on CentOS and MacOS, 
documentation and code clean-up is in-progress.***

This currently only supports [Leviton Decora](http://www.leviton.com/en/products/lighting-controls/decora-smart-with-wifi) 
line of light switches.  I am hoping that someone would contribute to support other light switches as well.

### Stand-alone Installation

* Define required environment variables by creating a copy of [.env_sample](.env_sample)) as a new `.env` file.
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
