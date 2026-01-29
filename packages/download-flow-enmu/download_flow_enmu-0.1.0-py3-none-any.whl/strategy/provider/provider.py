from abc import ABC, abstractmethod


class Provider(ABC):

    @abstractmethod
    def process_bills(self):
        pass
