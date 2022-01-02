import os

from leviton import LevitonDecora
from .AbstractPlexHook import AbstractPlexHook
import requests


class DecoraPlexHook(AbstractPlexHook):

    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.decora_api = None
        self.yamaha = None

    def login(self):
        leviton_user = os.environ.get('MY_LEVITON_USER')
        leviton_pass = os.environ.get('MY_LEVITON_PASSWORD')
        leviton_residence = os.environ.get('MY_LEVITON_RESIDENCE')
        self.logger.write(
            'Logging in to Leviton residence: {}, user: {}, pass: ****'.format(leviton_residence, leviton_user))
        self.decora_api = LevitonDecora(decora_email=leviton_user,
                                        decora_pass=leviton_pass,
                                        decora_residence=leviton_residence)

        # Piggyback on play/stop actions by controlling the AMP sound levels
        self.yamaha = os.environ.get('PLEX_LIGHT_AMP_HOST', None)

    def set_volume_level(self, level):
        if self.yamaha:
            self.logger.write('Setting amplifier volume level to: {}'.format(level))
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
