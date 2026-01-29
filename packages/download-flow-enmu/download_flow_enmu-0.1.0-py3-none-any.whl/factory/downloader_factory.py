from strategy.downloader.attchment import AttchmentDownloader


def creat_downloader(download_type: str):
    if download_type == "attchment":
        return AttchmentDownloader()
    else:
        raise NameError("未知下载器类型")
