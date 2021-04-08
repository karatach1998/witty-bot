import io
import json

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from yadisk import YaDisk

from . import config
from .books import AbstractBookStore, BookStoreContainer


class GDriveBookStore(AbstractBookStore):
    SCOPES = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]

    def __init__(self):
        creds = service_account.Credentials.from_service_account_info(
            json.loads(config.GOOGLE_SERVICE_ACCOUNT_INFO),
            scopes=GDriveBookStore.SCOPES
        )
        self.drive = build("drive", "v3", credentials=creds)

    def get_book_content(self, book_location):
        data = (
            self.drive.files()  # pylint: disable=no-member
            .get_media(fileId=book_location.extra["file_id"]).execute()
        )
        return io.BytesIO(data)


class YaDiskBookStore(AbstractBookStore):
    def __init__(self):
        self._y = YaDisk(token=config.YANDEX_DISK_TOKEN)

    def get_book_content(self, book_location):
        f = io.BytesIO()
        self._y.download(book_location.extra["path"], f)
        return f


class UrlBookStore(AbstractBookStore):
    def get_book_content(self, book_location):
        r = requests.get(book_location.extra["url"])
        return io.BytesIO(r.content)


BOOK_STORE_CONTAINER = BookStoreContainer({
    "gdrive": GDriveBookStore(),
    "yadisk": YaDiskBookStore(),
    "url": UrlBookStore(),
})
