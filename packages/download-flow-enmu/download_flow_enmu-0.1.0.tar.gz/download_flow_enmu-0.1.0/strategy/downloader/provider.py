from abc import ABC, abstractmethod
from imap_tools import MailBox
from data.bill_profile import BillProfile


class Downloader(ABC):
    @abstractmethod
    def download(self, mail: MailBox, bill: BillProfile):
        pass
