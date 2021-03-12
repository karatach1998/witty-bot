import io
import json

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from yadisk import YaDisk

import config
from books import AbstractBookStore, BookStoreContainer


class GDriveBookStore(AbstractBookStore):
    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]

    def __init__(self, service_account_info_str):
        creds = service_account.Credentials.from_service_account_info(
            json.loads(service_account_info_str), scopes=GDriveBookStore.SCOPES
        )
        self.drive = build("drive", "v3", credentials=creds)

    def get_book_content(self, book):
        data = (
            self.drive.files()  # pylint: disable=no-member
            .get_media(fileId=book.location["file_id"])
            .execute()
        )
        return io.BytesIO(data)


class YaDiskBookStore(AbstractBookStore):
    def __init__(self, token):
        self._y = YaDisk(token=token)

    def get_book_content(self, book):
        f = io.BytesIO()
        self._y.download(book.location["path"], f)
        return f


class UrlBookStore(AbstractBookStore):
    def get_book_content(self, book):
        r = requests.get(book.location["url"])
        return io.BytesIO(r.content)


BOOK_STORE_CONTAINER = BookStoreContainer(
    {
        "gdrive": GDriveBookStore(config.GOOGLE_SERVICE_ACCOUNT_INFO),
        "yadisk": YaDiskBookStore(config.YANDEX_DISK_TOKEN),
        "url": UrlBookStore(),
    }
)
