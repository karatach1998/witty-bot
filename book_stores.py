import io
from tempfile import NamedTemporaryFile

import requests
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from yadisk import YaDisk

import config
from books import AbstractBookStore, BookStoreContainer


class GDriveBookStore(AbstractBookStore):
    def __init__(self, client_secrets_str):
        with NamedTemporaryFile(
            mode="w+", dir=config.PROJECT_DIR, prefix="client_secrets", suffix="json"
        ) as f:
            f.write(client_secrets_str)
            self._gauth = GoogleAuth()
            self._gauth.LocalWebserverAuth()
        self.drive = GoogleDrive(self._gauth)

    def get_book_content(self, book):
        file = self.drive.CreateFile({"id": book.location["file_id"]})
        file.FetchContent()
        return file.content


class YaDiskBookStore(AbstractBookStore):
    def __init__(self, token):
        self._y = YaDisk(token=token)

    def get_book_content(self, book):
        with io.BytesIO() as f:
            self._y.download(book.location["path"], f)
            return f


class UrlBookStore(AbstractBookStore):
    def get_book_content(self, book):
        r = requests.get(book.location["url"])
        return io.BytesIO(r.content)


BOOK_STORE_CONTAINER = BookStoreContainer(
    {
        "gdrive": GDriveBookStore(config.GOOGLE_AUTH_CLIENT_SECRETS),
        "yadisk": YaDiskBookStore(config.YANDEX_DISK_TOKEN),
        "url": UrlBookStore(),
    }
)
