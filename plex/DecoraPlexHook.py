import os

from leviton import LevitonDecora
from .AbstractPlexHook import AbstractPlexHook


class DecoraPlexHook(AbstractPlexHook):

    def __init__(self):
        super().__init__()
        self.switch = os.environ.get('DECORA_SWITCH')
        self.decora_api = LevitonDecora(decora_email=os.environ.get('MY_LEVITON_USER'),
                                        decora_pass=os.environ.get('MY_LEVITON_PASSWORD'),
                                        decora_residence=os.environ.get('MY_LEVITON_RESIDENCE'))

    def clip_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_CLIP_ACTIVITY'))

    def end_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_END_ACTIVITY'))

    def play_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_PLAY_ACTIVITY'))

    def pause_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_PAUSE_ACTIVITY'))

    def stop_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_STOP_ACTIVITY'))
