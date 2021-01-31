import io
import os
import random
from pathlib import Path
from collections import defaultdict, OrderedDict
from itertools import chain, zip_longest
from functools import partial

TASKS_DIR = Path(os.getcwd(), 'tasks')
PROBLEMS_DIRS = {
    'integral': TASKS_DIR / 'integral_problems',
}
THEORY_DIRS = {
    'integral': TASKS_DIR / 'integral_theory',
}
_SUBJECTS = defaultdict(OrderedDict)

import logging
print = logging.getLogger(__name__).info


def _get_subjects(name):
    if not _SUBJECTS[name]:
        theory_dir = THEORY_DIRS[name]
        _SUBJECTS[name].update(p.stem.split(' ', maxsplit=1) for p in sorted(theory_dir.iterdir()))
    return _SUBJECTS[name]

get_integral_subjects = partial(_get_subjects, 'integral')


def get_integral_problem(subject_id=None):
    if not subject_id:
        subject_id = random.choice(list(get_integral_subjects()))

    problems_paths = PROBLEMS_DIRS['integral'].glob(f'{subject_id}*.txt')
    problems_paths = list(problems_paths)
    problems = list(chain.from_iterable(
            zip_longest([p.stem.split(' ', maxsplit=1)[1]], p.read_text().split('\n'))
            for p in problems_paths))
    return (subject_id,) + random.choice(problems)


def get_integral_theory(subject_id):
    doc = next(THEORY_DIRS['integral'].glob(f'{subject_id}*'))
    return doc

