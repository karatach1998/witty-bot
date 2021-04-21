import io
import random
from collections import OrderedDict
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Union, cast

import wolframalpha
import yaml
from sympy.parsing.latex import parse_latex
from sympy.printing.maple import maple_code

from . import config
from .book_stores import BOOK_STORE_CONTAINER
from .books import Book
from .math_problems import BookRef, MathProblem, MathTask
from .russian_rules import RussianRules
from .utils import latex2png


class MathProblemsService:
    def __init__(self, subject_name: str) -> None:
        self._wa_client = wolframalpha.Client(config.WOLFRAMALPHA_APP_ID)

        self.subject_name = subject_name

        math_subject_path = config.MATH_PROBLEMS_PATH / subject_name
        problems_dir = math_subject_path / "problems"
        book_path = math_subject_path / "book.yaml"

        def load_tasks(filepath: Path) -> List[MathTask]:
            return [
                MathTask(
                    book_ref=BookRef(
                        chapter_title=filepath.stem, **task.pop("book_ref")
                    ),
                    **task,
                ) for task in yaml.safe_load(filepath.read_text())
            ]

        assert set(problems_dir.glob("*.yaml")) == set(problems_dir.iterdir())
        self._problems = {
            p.stem.split(maxsplit=1)[1]: load_tasks(p)
            for p in problems_dir.iterdir()
        }
        self._book = Book(
            BOOK_STORE_CONTAINER, **yaml.safe_load(book_path.read_text())
        )

    chapter_titles = property(lambda self: list(self._problems.keys()))

    def get_random_problem(
        self, chapter_title: Optional[str] = None
    ) -> MathProblem:
        if chapter_title is None:
            chapter_title = random.choice(self.chapter_titles)
        tasks = self._problems[chapter_title]
        random_task = random.choice(tasks)
        random_problem = random.choice(random_task.problems)
        return MathProblem(
            task=random_task.task,
            problem=random_problem,
            book_ref=random_task.book_ref
        )

    def get_problem_img(self, problem: MathProblem) -> io.BytesIO:
        return latex2png.draw_integral_problem(
            problem.task, problem.problem
        )  # type: ignore

    def _make_wa_query(self, problem: MathProblem) -> str:
        raise NotImplementedError

    def get_solution_sequence(
        self, problem: MathProblem
    ) -> Generator[Tuple[str, bytes], None,
                   None]:  # mypy: disallow_untyped_calls=false
        query = self._make_wa_query(problem)
        res = self._wa_client.query(query)
        for pod in res.results:
            try:
                yield pod.title, next(next(pod.subpod).img).src
            except (StopIteration, AttributeError):
                continue

    def get_theory_pdf(
        self,
        problem: MathProblem,
        *,
        return_title: bool = False
    ) -> Union[bytes, Tuple[bytes, Optional[str]]]:
        book_ref = problem.book_ref
        chapter_title, start, end = (
            book_ref.chapter_title,
            book_ref.start,
            book_ref.end,
        )
        if start and end:
            theory_pdf = self._book.get_page_range_pdf(start, end)
        else:
            chapter = next(
                filter(
                    lambda ch: ch.title == chapter_title, self._book.chapters
                )
            )
            theory_pdf = self._book.get_chapter_pdf(chapter)

        if not return_title:
            return theory_pdf
        else:
            return theory_pdf, chapter_title


class IntegralProblemsService(MathProblemsService):
    def __init__(self) -> None:
        super().__init__("integral")

    def _make_wa_query(self, problem: MathProblem) -> str:
        integral_latex = problem.problem.split("$")[1]
        integral = parse_latex(integral_latex)
        return f"integrate {maple_code(integral.function)} d{integral.free_symbols}"


class RussianRulesService:
    def __init__(self) -> None:
        metainfo_path = config.RESOURCES_PATH / "russian_rules.yaml"
        self._russian_rules = RussianRules(
            **yaml.safe_load(metainfo_path.read_text())
        )

    part_titles = property(lambda self: self._russian_rules.part_titles)

    def get_random_paragraph_html(
        self,
        part_title: str,
        *,
        return_chapter_title: bool = False
    ) -> Union[Optional[str], Tuple[Optional[str], str]]:
        random_chapter = random.choice(
            self._russian_rules.list_part_chapters(part_title)
        )
        paragraphs_html = self._russian_rules.get_chapter_paragraphs_html(
            random_chapter
        )
        paragraph_html = cast(
            Optional[str], paragraphs_html and random.choice(paragraphs_html)
        )
        if not return_chapter_title:
            return paragraph_html
        else:
            return paragraph_html, random_chapter.title


class BookCollectionService:
    def __init__(self) -> None:
        def load_book(path: Path) -> Book:
            return Book(
                BOOK_STORE_CONTAINER, **yaml.safe_load(path.read_text())
            )

        self._books = OrderedDict(
            list(
                map(
                    lambda b: (b.title, b),
                    map(load_book, config.BOOKS_PATH.iterdir())
                )
            )
        )

    book_titles = property(lambda self: self._books.keys())

    def get_random_book_chapter_pdf(
        self,
        book_title: str,
        *,
        return_title_tuple: bool = False
    ) -> Union[bytes, Tuple[bytes, Tuple[str, Optional[str], str]]]:
        book = self._books[book_title]

        random_part = book.parts and random.choice(book.parts)
        random_chapter = random.choice(
            random_part.chapters if random_part else book.chapters
        )

        chapter_pdf = book.get_chapter_pdf(random_chapter)
        if not return_title_tuple:
            return chapter_pdf
        else:
            return (
                chapter_pdf,
                (
                    book.title,
                    random_part and random_part.title,
                    random_chapter.title,
                ),
            )
