from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

import lxml.etree
import lxml.html
import requests
from mashumaro import DataClassDictMixin


@dataclass
class RulesChapter(DataClassDictMixin):
    title: str
    path: str


@dataclass
class RulesPart(DataClassDictMixin):
    title: str
    chapters: List[RulesChapter]


class RussianRules:
    def __init__(self, parts, *, base_url):
        self._parts = {
            p["title"].strip(): RulesPart.from_dict(p)
            for p in parts
        }
        self._base_url = base_url

    part_titles = property(lambda self: list(self._parts.keys()))

    def list_part_chapters(self, part_title):
        return self._parts[part_title].chapters

    def get_chapter_paragraphs_html(self, chapter):
        r = requests.get(urljoin(self._base_url, chapter.path))

        if not r.ok:
            return

        page = lxml.html.document_fromstring(r.text)
        body = page.find("body")
        assert body is not None

        header, *paragraphs = body.find_class("section-wrapper")
        htmls = []
        for paragraph in paragraphs:
            body[:] = [header, paragraph]
            htmls.append(
                lxml.etree.tostring(  # pylint: disable=c-extension-no-member
                    page, method="html", encoding="unicode"
                )
            )
        return htmls
