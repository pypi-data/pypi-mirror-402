import logging

from pathlib import Path

from strategy.provider.provider import Provider
from strategy.email.email_provider import Email
from strategy.downloader.provider import Downloader
from data.bill_profile import BillProfile


class AliProvider(Provider):

    downloader: Downloader
    email: Email

    def __init__(
        self,
        email: Email = None,
        downloader: Downloader = None,
        bill: BillProfile = None,
    ):
        self.email = email
        self.downloader = downloader
        self.bill = bill

    def process_bills(self):
        logging.info("开始处理ali账单")
        mailbox = self.email.connect()

        with mailbox.login(self.email.username, self.email.password, "INBOX") as mb:
            self.downloader.download(mb, bill=self.bill)
