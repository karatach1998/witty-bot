import io
import os
from pathlib import Path
from unittest.mock import Mock

from test_utils import assert_pdf_equal

from books import (  # pylint: disable=import-error
    AbstractBookStore,
    Book,
    BookLocation,
    BookStoreContainer,
)


class TestBookStoreContainer:
    def test_get_store(self):
        store_type = '<store_type>'
        store = object()
        book_location = BookLocation(type=store_type, extra={})

        store_container = BookStoreContainer(stores={store_type: store})

        assert store_container.get_store(book_location) is store


class TestBook:
    def test_chapters(self):
        location = {'type': 'url', 'extra': {'foo': 'bar'}}
        chapters1 = [{'title': 'Chapter 1', 'start': 1, 'end': 2}]
        chapters2 = [{'title': 'Chapter 2', 'start': 2, 'end': 3}]
        parts = [
            {
                'title': 'Part 1',
                'start': 0,
                'end': 2,
                'chapters': chapters1
            },
            {
                'title': 'Part 2',
                'start': 0,
                'end': 2,
                'chapters': chapters2
            },
        ]
        chapters = chapters1 + chapters2

        book1 = Book(None, title='', location=location, parts=parts)
        assert all(
            getattr(bc, attr) == value
            for bc, c in zip(book1.chapters, chapters)
            for attr, value in c.items()
        )
        book2 = Book(None, title='', location=location, chapters=chapters)
        assert all(
            getattr(bc, attr) == value
            for bc, c in zip(book2.chapters, chapters)
            for attr, value in c.items()
        )

    def test_list_part_chaters(self):
        location = {'type': 'url', 'extra': {'foo': 'bar'}}
        chapters1 = [{'title': 'Chapter 1', 'start': 1, 'end': 2}]
        chapters2 = [{'title': 'Chapter 2', 'start': 2, 'end': 3}]
        parts = [
            {
                'title': 'Part 1',
                'start': 0,
                'end': 2,
                'chapters': chapters1
            },
            {
                'title': 'Part 2',
                'start': 0,
                'end': 2,
                'chapters': chapters2
            },
        ]

        book = Book(None, title='', location=location, parts=parts)
        bp = book.parts[1]
        assert all(
            getattr(bc, attr) == value
            for bc, c in zip(book.list_part_chapters(bp), chapters2)
            for attr, value in c.items()
        )

    def test_content(self):
        content = io.BytesIO(b'Book content')
        location = {'type': 'gdrive', 'extra': {'file_id': 'fakkjljlk'}}

        mock_store_container = Mock(BookStoreContainer)
        mock_book_store = Mock(AbstractBookStore)
        mock_store_container.get_store.return_value = mock_book_store
        mock_book_store.get_book_content.return_value = content
        mock_book = Mock(Book)
        mock_book.location = location

        book = Book(
            mock_store_container, title='', location=location, parts=[]
        )
        book_location = BookLocation(**location)
        assert book.content == content

        mock_store_container.get_store.assert_called_once_with(book_location)

    def test_page_range_pdf(self):
        test_data_path = Path(
            os.path.dirname(os.path.abspath(__file__)), 'testdata'
        )
        stream = (test_data_path / 'document.pdf').open('rb')
        page_range_content = (test_data_path /
                              'document-pp(3-5).pdf').read_bytes()
        location = dict(type='', extra={})

        mock_store = Mock(AbstractBookStore)
        mock_store.get_book_content.return_value = stream
        mock_store_container = Mock(BookStoreContainer)
        mock_store_container.get_store.return_value = mock_store

        book = Book(
            mock_store_container, title='', location=location, chapters=[]
        )
        book_page_range_content = book.get_page_range_pdf(3, 5)

        assert_pdf_equal(
            io.BytesIO(book_page_range_content),
            io.BytesIO(page_range_content)
        )
