from dataclasses import dataclass
from unittest.mock import patch
from urllib.parse import urljoin

import lxml.html

from russian_rules import RussianRules  # pylint: disable=import-error

RULE_CHAPTER_HTML_PAGE = """
<html>
  <head>
  </head>
  <body>
    <div class="content">
      <div class="section-wrapper header"></div>
      <div class="section-wrapper"></div>
    </div>
  </body>
</html>
"""


class TestRussianRules:
    def test_part_titles(self):
        part_titles = ["Part 1", "Part 2"]
        parts = [{'title': title, 'chapters': []} for title in part_titles]

        russian_rules = RussianRules(parts, base_url='')

        assert russian_rules.part_titles == part_titles

    def test_list_part_chaters(self):
        part_title = "Part"
        chapters = [{'title': 'Chapter', 'path': 'https://foo/bar'}]
        parts = [{'title': part_title, 'chapters': chapters}]

        russian_rules = RussianRules(parts, base_url='')

        assert all(
            vars(a) == b for a, b in
            zip(russian_rules.list_part_chapters(part_title), chapters)
        )

    def test_get_chapter_paragraph_html(self):
        html_page = RULE_CHAPTER_HTML_PAGE
        part_title = "Title"
        chapter = {'title': '', 'path': '/bar'}
        parts = [{'title': part_title, 'chapters': [chapter]}]
        base_url = 'http://foo'

        @dataclass
        class Response:
            text: str
            ok: bool = True

        with patch('requests.get') as mock_requests_get:
            mock_requests_get.return_value = Response(text=html_page)

            russian_rules = RussianRules(parts=parts, base_url=base_url)
            chapters = russian_rules.list_part_chapters(part_title)
            htmls = russian_rules.get_chapter_paragraphs_html(chapters[0])

            mock_requests_get.assert_called_once_with(
                urljoin(base_url, chapter['path'])
            )
            assert isinstance(htmls, list)
            assert len(htmls) == 1
            html_str = htmls[0]
            assert isinstance(html_str, str)
            html = lxml.html.document_fromstring(html_str)
            body = html.find('body')
            assert len(body.getchildren()) == 2
