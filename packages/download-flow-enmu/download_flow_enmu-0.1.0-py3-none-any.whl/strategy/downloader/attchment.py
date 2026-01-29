import datetime
import logging

from imap_tools import MailBox, AND

from strategy.downloader.provider import Downloader
from typing import override
from data.bill_profile import BillProfile


class AttchmentDownloader(Downloader):
    @override
    def download(self, mail: MailBox, bill: BillProfile):

        criteria = AND(
            from_=bill.sender_email,
            date=datetime.date.today(),
        )

        for msg in mail.fetch(criteria=criteria):
            logging.info(f"找到邮件: {msg.subject}")  # 添加这一行

            if bill.search_subject not in msg.subject:
                continue
            for att in msg.attachments:
                if att.filename.lower().endswith(bill.file_suffix):
                    bill.save_subdir.mkdir(parents=True, exist_ok=True)
                    filepath = (
                        bill.save_subdir / f"{datetime.date.today()}.{bill.file_suffix}"
                    )  # 改这里：加扩展名

                    try:
                        if bill.file_suffix in ["zip", "7z", "rar"]:
                            filepath.write_bytes(att.payload)
                        else:
                            content_str = att.payload.decode(bill.encoding)
                            filepath.write_text(content_str, encoding="utf-8")
                    except UnicodeDecodeError:
                        logging.error("  ✗ 转码失败")
                else:
                    logging.info(f"✗ 附件类型不匹配 (期望后缀: {bill.file_suffix})")
