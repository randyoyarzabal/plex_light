from abc import ABC, abstractmethod


class PlexHook(ABC):

    @abstractmethod
    def play_movie(self):
        pass

    @abstractmethod
    def pause_movie(self):
        pass

    @abstractmethod
    def stop_movie(self):
        pass
