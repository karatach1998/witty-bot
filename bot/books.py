import io
from dataclasses import dataclass
from itertools import chain
from typing import Any, Dict, List, Optional

from mashumaro import DataClassDictMixin
from PyPDF2 import PdfFileReader, PdfFileWriter


@dataclass
class BookLocation(DataClassDictMixin):
    type: str
    extra: Dict[str, str]


class AbstractBookStore:
    def get_book_content(self, book_location: BookLocation) -> io.BytesIO:
        raise NotImplementedError


@dataclass
class BookStoreContainer:
    stores: Dict[str, AbstractBookStore]

    def get_store(self, book_location: BookLocation) -> AbstractBookStore:
        return self.stores[book_location.type]


@dataclass
class BookChapter(DataClassDictMixin):
    title: str
    start: int
    end: int


@dataclass
class BookPart(DataClassDictMixin):
    title: str
    start: int
    end: int
    chapters: List[BookChapter]


class Book:
    def __init__(
        self, store_container: BookStoreContainer, *, title: str,
        location: Dict[str, Any], **kwargs: Any
    ) -> None:
        self._store_container = store_container
        self.title = title.strip()
        self.location = BookLocation.from_dict(location)
        self.parts = kwargs.pop("parts", None)
        if self.parts is not None:
            self.parts = list(map(BookPart.from_dict, self.parts))
            self._chapters = None
        else:
            self._chapters = list(
                map(BookChapter.from_dict, kwargs.pop("chapters"))
            )
        self._content: Optional[io.BytesIO] = None

    @property
    def chapters(self) -> List[BookChapter]:
        return self._chapters or list(
            chain.from_iterable(p.chapters for p in self.parts)
        )

    def list_part_chapters(self, part: BookPart) -> List[BookChapter]:
        return part.chapters

    @property
    def content(self) -> io.BytesIO:
        if self._content is None:
            store = self._store_container.get_store(self.location)
            self._content = store.get_book_content(self.location)
        return self._content

    def get_page_range_pdf(self, start: int, end: int) -> bytes:
        assert start < end

        pdf = PdfFileReader(self.content)
        page_range_pdf = PdfFileWriter()
        for page in pdf.pages[start - 1:end]:
            page_range_pdf.addPage(page)

        with io.BytesIO() as stream:
            page_range_pdf.write(stream)
            return stream.getvalue()

    def get_chapter_pdf(self, ch: BookChapter) -> bytes:
        return self.get_page_range_pdf(ch.start, ch.end)
