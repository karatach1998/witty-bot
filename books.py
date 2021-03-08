import io
from typing import Dict
from dataclasses import dataclass
from itertools import chain

from PyPDF2 import PdfFileReader, PdfFileWriter


class AbstractBookStore:
    def get_book_content(self, book):
        raise NotImplementedError


@dataclass
class BookStoreContainer:
    stores: Dict[str, AbstractBookStore]

    def get_store(self, book):
        return self.stores[book.location["type"]]


class Book:
    def __init__(self, store_container, *, title, location, **kwargs):
        self._store_container = store_container
        self.title = title.strip()
        self.location = location
        self.parts = kwargs.pop("parts", None)
        if self.parts is not None:
            # self.parts = list(map(lambda x: BookPart(**x), self.parts))
            self._chapters = None
        else:
            # self._chapters = list(map(lambda x: print(x) and BookChapter(**x), kwargs.pop("chapters")))
            self._chapters = kwargs.pop("chapters")
        self._content = None

    @property
    def chapters(self):
        return self._chapters or list(
            chain.from_iterable(p["chapters"] for p in self.parts)
        )

    def list_part_chapters(self, part):
        return part["chapters"]

    @property
    def content(self):
        if self._content is None:
            store = self._store_container.get_store(self)
            self._content = store.get_book_content(self)
        return self._content

    def get_page_range_pdf(self, start, end):
        pdf = PdfFileReader(self.content)
        page_range_pdf = PdfFileWriter()
        for page in pdf.pages[start : end + 1]:
            page_range_pdf.addPage(page)

        with io.BytesIO() as stream:
            page_range_pdf.write(stream)
            return stream.getvalue()

    def get_chapter_pdf(self, ch):
        return self.get_page_range_pdf(ch["start"], ch["end"])
