from copy import deepcopy
from urllib.parse import urljoin

import requests
import lxml.etree, lxml.html


class RussianRules:
    def __init__(self, parts, *, base_url):
        self._parts = {p["title"].strip(): p for p in parts}
        self._base_url = base_url

    part_titles = property(lambda self: list(self._parts.keys()))

    def list_part_chapters(self, part_title):
        return self._parts[part_title]["chapters"]

    def get_chapter_paragraphs_html(self, chapter):
        r = requests.get(urljoin(self._base_url, chapter["path"]))

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
                    deepcopy(page), method="html", encoding="unicode"
                )
            )
        return htmls
