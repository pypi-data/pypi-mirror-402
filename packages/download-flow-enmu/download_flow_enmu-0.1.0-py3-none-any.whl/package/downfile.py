import imaplib
import email
import logging
import os
import datetime
import re
from email.header import decode_header
import requests
from bs4 import BeautifulSoup
from config import config

# === 配置区域 ===
username = config["email"]["username"]
password = config["email"]["password"]
DOWNLOAD_FOLDER_ALI = config["email"]["download_folder_ali"]
DOWNLOAD_FOLDER_WECHAT = config["email"]["download_folder_wechat"]
SEARCH_KEYWORD = config["email"]["search_keyword"]
IMAP_SERVER = config["email"].get("imap_server", "imap.gmail.com")


def clean_text(text):
    if not text:
        return ""
    decoded_list = decode_header(text)
    text_str = ""
    for decoded_part, encoding in decoded_list:
        if isinstance(decoded_part, bytes):
            text_str += decoded_part.decode(
                encoding if encoding else "utf-8", errors="ignore"
            )
        else:
            text_str += str(decoded_part)
    return text_str


def get_html_content(msg):
    for part in msg.walk():
        # 只要 HTML 格式的部分
        if part.get_content_type() == "text/html":
            try:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="ignore")
            except Exception as e:
                logging.error(f"HTML解码失败: {e}")
    return None


def process_wechat_links(html_content):
    if not html_content:
        return False

    soup = BeautifulSoup(html_content, "html.parser")

    # 提取链接
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    target_links = [
        link
        for link in links
        if "download" in link or "ftn" in link or "qq.com" in link  # type: ignore
    ]

    if not target_links:
        logging.warning("未找到符合条件的下载链接")
        return False

    download_url = target_links[0]
    logging.info(f"提取到下载链接: {download_url}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(download_url, headers=headers, stream=True)  # type: ignore

        if r.status_code == 200:
            # import time

            # timestamp = int(time.time())
            today_str = datetime.date.today().strftime("%Y%m%d")
            filename = f"{today_str}.zip"
            if not os.path.exists(DOWNLOAD_FOLDER_WECHAT):
                os.makedirs(DOWNLOAD_FOLDER_WECHAT)

            filepath = os.path.join(DOWNLOAD_FOLDER_WECHAT, filename)

            logging.info(f"准备保存文件到: {filepath}")

            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            logging.info(f"链接下载成功: {filename}")
            return True
        else:
            logging.error(f"下载链接访问失败: {r.status_code}")
            return False

    except Exception as e:
        logging.error(f"下载异常: {e}")
        return False


def download_safe_mode() -> bool:
    try:
        logging.info("正在连接 Gmail...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(username, password)
        mail.select("inbox")

        # 搜索最近 2 天 (防止时区问题导致搜不到今天)
        target_date = datetime.date.today() - datetime.timedelta(days=2)
        today_str = target_date.strftime("%Y/%m/%d")

        query_safe = f'X-GM-RAW "after:{today_str}"'
        logging.info(f"步骤1: 向服务器请求邮件 (query: {query_safe})")
        status, messages = mail.search(None, query_safe)

        if status != "OK":
            logging.error("搜索失败。")
            return False

        email_ids = messages[0].split()
        total_found = len(email_ids)
        logging.info(f"步骤1完成: 找到 {total_found} 封邮件。")

        if total_found == 0:
            return False

        logging.info(f"步骤2: 正在本地筛选包含关键词 '{SEARCH_KEYWORD}' 的邮件...\n")

        match_count = 0
        match_email_id = []
        for email_id in reversed(email_ids):
            res, msg_data = mail.fetch(email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])  # type: ignore

            subject = clean_text(msg["Subject"])

            match = re.search(SEARCH_KEYWORD, subject)
            if not match:
                continue

            key = match.group()
            logging.info(f"当前关键词为:{key}")

            match_count += 1
            match_email_id.append(email_id)
            logging.info(f"  [√ 匹配] 发现目标邮件: {subject}")

            # === 分支逻辑 ===
            if key == "微信":
                logging.info("检测到微信账单，尝试提取下载链接...")
                html_content = get_html_content(msg)
                link_success = False
                if html_content:
                    link_success = process_wechat_links(html_content)
                if not link_success:
                    logging.info("链接提取失败或未找到，尝试检查是否有普通附件...")

            else:
                logging.info("检测到支付宝或其他，执行附件下载...")
                for part in msg.walk():
                    if (
                        part.get_content_maintype() == "multipart"
                        or part.get("Content-Disposition") is None
                    ):
                        continue

                    filename = part.get_filename()
                    if filename:
                        filename = clean_text(filename)
                        if not os.path.exists(DOWNLOAD_FOLDER_ALI):
                            os.makedirs(DOWNLOAD_FOLDER_ALI)

                        today_str = datetime.date.today().strftime("%Y%m%d")
                        filepath = os.path.join(DOWNLOAD_FOLDER_ALI, f"{today_str}.zip")

                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))  # type: ignore

                        logging.info(f"      -> 附件已保存: {today_str}")

        # ... (后续的归档/移动邮件逻辑保持不变) ...

        mail.close()
        mail.logout()
        return True

    except Exception as e:
        logging.error(f"发生错误: {e}")
        return False
