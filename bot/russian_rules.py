from dataclasses import dataclass
from typing import Any, Dict, List, Optional
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
    def __init__(self, parts: List[Dict[str, Any]], *, base_url: str) -> None:
        self._parts = {
            p["title"].strip(): RulesPart.from_dict(p)
            for p in parts
        }
        self._base_url = base_url

    part_titles = property(lambda self: list(self._parts.keys()))

    def list_part_chapters(self, part_title: str) -> List[RulesChapter]:
        return self._parts[part_title].chapters

    def get_chapter_paragraphs_html(
        self, chapter: RulesChapter
    ) -> Optional[List[str]]:
        r = requests.get(urljoin(self._base_url, chapter.path))

        if not r.ok:
            return None

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
