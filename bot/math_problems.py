from dataclasses import dataclass
from typing import List, Optional

from mashumaro import DataClassDictMixin


@dataclass
class BookRef(DataClassDictMixin):
    start: int
    end: int
    chapter_title: Optional[str] = None


@dataclass
class MathProblem(DataClassDictMixin):
    task: str
    problem: str
    book_ref: BookRef


@dataclass
class MathTask(DataClassDictMixin):
    task: str
    problems: List[str]
    book_ref: BookRef
