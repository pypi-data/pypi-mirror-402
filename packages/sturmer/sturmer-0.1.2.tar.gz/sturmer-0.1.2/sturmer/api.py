from __future__ import annotations

from functools import lru_cache

from .search import TaskIndex
from .storage import load_builtin_tasks


@lru_cache(maxsize=1)
def _builtin_index() -> TaskIndex:
    tasks = load_builtin_tasks()
    return TaskIndex(tasks)


def find(query: str, top_k: int = 5) -> list[dict[str, object]]:
    index = _builtin_index()
    matches = index.search(query, top_k=top_k)
    results: list[dict[str, object]] = []
    for match in matches:
        if match.task.solution is None:
            continue
        results.append(
            {
                "text": match.task.text,
                "solution": match.task.solution,
            }
        )
    return results


def refresh_builtin_index() -> None:
    _builtin_index.cache_clear()
