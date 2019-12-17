# Automated Plex Lighting Control
A webhook application for automatically controlling home theater lighting upon movie start, stop, 
and pause in [Plex Media Center](http://plex.tv).  

## Instructions

### Notes
This currently only supports [Leviton Decora](http://www.leviton.com/en/products/lighting-controls/decora-smart-with-wifi) 
line of light switches.  I am hoping that someone would contribute to support other light switches as well.

### Stand-alone installation

* Define required environment variables (see samples in [start_hook.sh](start_hook.sh)) in `.env` file.
* Install prerequisite packages from [requirements.txt](requirements.txt) using Python 3+:  
`pip install -r requirements.txt`
* Run the webhook app:  
`./start_hook.sh`
* Define webhook on your Plex account as: `http://<ip address>:5000/webhook`

### Docker installation
TBD

## Credits

This is based on the idea and code posted by [dwclarknu](https://forums.plex.tv/t/rel-control-leviton-lights/275873) 
on the [Plex Forums](https://forums.plex.tv).  

The library used for [Leviton Decora](http://www.leviton.com/en/products/lighting-controls/decora-smart-with-wifi) 
Smart WiFi Switches &amp; Dimmers is [python-decora_wifi](https://github.com/tlyakhov/python-decora_wifi).
