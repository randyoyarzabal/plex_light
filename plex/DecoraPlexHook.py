import os

from leviton import LevitonDecora
from .PlexHook import PlexHook


class DecoraPlexHook(PlexHook):

    def __init__(self, activity=False):
        super().__init__()
        self.activity = activity
        self.switch = os.environ.get('DECORA_SWITCH')
        self.decora_api = LevitonDecora(decora_email=os.environ.get('DECORA_USER'),
                                        decora_pass=os.environ.get('DECORA_PASS'),
                                        decora_residence=os.environ.get('DECORA_RESIDENCE'))

    def play_movie(self):
        if self.activity:
            self.decora_api.run_activity(os.environ.get('PLEX_PLAY_ACTIVITY'))
        else:
            self.decora_api.control_switch(self.switch, brightness=int(os.environ.get('PLEX_PLAY_BRIGHTNESS')))
        self.decora_api.log_out()

    def pause_movie(self):
        if self.activity:
            self.decora_api.run_activity(os.environ.get('PLEX_PAUSE_ACTIVITY'))
        else:
            self.decora_api.control_switch(self.switch, brightness=int(os.environ.get('PLEX_PAUSE_BRIGHTNESS')))
        self.decora_api.log_out()

    def stop_movie(self):
        if self.activity:
            self.decora_api.run_activity(os.environ.get('PLEX_STOP_ACTIVITY'))
        else:
            self.decora_api.control_switch(self.switch, brightness=int(os.environ.get('PLEX_STOP_BRIGHTNESS')))
        self.decora_api.log_out()