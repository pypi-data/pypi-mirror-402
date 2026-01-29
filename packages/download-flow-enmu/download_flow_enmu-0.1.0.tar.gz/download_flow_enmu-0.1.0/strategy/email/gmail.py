import logging

from datetime import date
from strategy.email.email_provider import Email
from imap_tools import MailBox
from strategy.downloader.attchment import AttchmentDownloader


class Gmail(Email):
    username: str
    password: str

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.host = "imap.gmail.com"

    def connect(self) -> MailBox:
        return MailBox(self.host)
