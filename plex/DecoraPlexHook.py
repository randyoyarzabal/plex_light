import os

from leviton import LevitonDecora
from .PlexHook import PlexHook


class DecoraPlexHook(PlexHook):

    def __init__(self):
        super().__init__()
        self.switch = os.environ.get('DECORA_SWITCH')
        self.decora_api = LevitonDecora(decora_email=os.environ.get('DECORA_USER'),
                                        decora_pass=os.environ.get('DECORA_PASS'),
                                        decora_residence=os.environ.get('DECORA_RESIDENCE'))

    def clip_action(self):
        self.decora_api.run_activity('PLEX_CLIP_ACTIVITY')

    def end_action(self):
        self.decora_api.run_activity('PLEX_END_ACTIVITY')

    def play_action(self):
        self.decora_api.run_activity('PLEX_PLAY_ACTIVITY')

    def pause_action(self):
        self.decora_api.run_activity('PLEX_PAUSE_ACTIVITY')

    def stop_action(self):
        self.decora_api.run_activity('PLEX_STOP_ACTIVITY')
