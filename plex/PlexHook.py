from abc import ABC, abstractmethod


class PlexHook(ABC):

    @abstractmethod
    def clip_action(self):
        pass

    @abstractmethod
    def end_action(self):
        pass

    @abstractmethod
    def play_action(self):
        pass

    @abstractmethod
    def pause_action(self):
        pass

    @abstractmethod
    def stop_action(self):
        pass
