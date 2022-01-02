import os

from leviton import LevitonDecora
from .AbstractPlexHook import AbstractPlexHook
import requests
from plex.Utiliy import *
from plex import Utiliy


class DecoraPlexHook(AbstractPlexHook):

    def __init__(self):
        super().__init__()
        self.switch = os.environ.get('DECORA_SWITCH')
        self.decora_api = LevitonDecora(decora_email=os.environ.get('MY_LEVITON_USER'),
                                        decora_pass=os.environ.get('MY_LEVITON_PASSWORD'),
                                        decora_residence=os.environ.get('MY_LEVITON_RESIDENCE'))

        # Piggy back on play/stop actions by controlling the AMP sound levels
        self.yamaha = os.environ.get('PLEX_LIGHT_AMP_HOST')

    def set_volume_level(self, level):
        if self.yamaha != '':
            log_action(Utiliy.log_id, 'Setting amplifier volume level to: {}'.format(level))
            amp_url = 'http://{}/YamahaExtendedControl/v1/main/setVolume?volume={}'.format(self.yamaha, level * 2)
            requests.get(amp_url)  # No need to check for status.

    def clip_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_CLIP_ACTIVITY'))

    def end_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_END_ACTIVITY'))

    def play_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_PLAY_ACTIVITY'))
        self.set_volume_level(int(os.environ.get('PLEX_LIGHT_AMP_PLAY_VOL_LEVEL')))

    def pause_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_PAUSE_ACTIVITY'))

    def stop_action(self):
        self.decora_api.run_activity(os.environ.get('PLEX_STOP_ACTIVITY'))
        self.set_volume_level(int(os.environ.get('PLEX_LIGHT_AMP_STOP_VOL_LEVEL')))
