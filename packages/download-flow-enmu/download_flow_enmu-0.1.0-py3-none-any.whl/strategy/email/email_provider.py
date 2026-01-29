from abc import ABC, abstractmethod
from imap_tools import MailBox


class Email(ABC):

    @abstractmethod
    def connect() -> MailBox:
        pass
