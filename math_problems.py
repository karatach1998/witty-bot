from typing import List, Optional
from dataclasses import dataclass, InitVar


@dataclass
class BookRef:
    start: int
    end: int
    chapter_title: Optional[str] = None


@dataclass
class MathProblem:
    task: str
    problem: str
    book_ref: BookRef


@dataclass
class MathTask:
    task: str
    problems: List[str]
    book_ref: BookRef
    chapter_title: InitVar[str]

    def __post_init__(self, chapter_title):
        self.book_ref.chapter_title = chapter_title
