from __future__ import annotations

from functools import lru_cache
from typing import List

from .search import TaskIndex
from .storage import load_builtin_tasks


@lru_cache(maxsize=1)
def _builtin_index() -> TaskIndex:
    tasks = load_builtin_tasks()
    return TaskIndex(tasks)


def find(query: str, top_k: int = 5) -> List[object]:
    index = _builtin_index()
    matches = index.search(query, top_k=top_k)
    return [match.task.solution for match in matches if match.task.solution is not None]


def refresh_builtin_index() -> None:
    _builtin_index.cache_clear()
