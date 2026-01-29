from __future__ import annotations

from dataclasses import dataclass
import math
import re
from collections import Counter
from typing import Dict, Iterable, List, Mapping, Optional


_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def _tokenize(text: str) -> List[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


@dataclass(frozen=True)
class Task:
    task_id: str
    text: str
    solution: Optional[object] = None


@dataclass(frozen=True)
class TaskMatch:
    task: Task
    score: float


class TaskIndex:
    def __init__(self, tasks: Optional[Iterable[Task]] = None) -> None:
        self._tasks: List[Task] = []
        self._task_by_id: Dict[str, Task] = {}
        self._doc_vectors: List[Dict[str, float]] = []
        self._doc_norms: List[float] = []
        self._idf: Dict[str, float] = {}
        self._dirty = True

        if tasks:
            self.add_tasks(tasks)

    @classmethod
    def from_dict(cls, data: Mapping[str, str]) -> "TaskIndex":
        tasks = [Task(task_id=task_id, text=text) for task_id, text in data.items()]
        return cls(tasks)

    def add_task(self, task: Task) -> None:
        if task.task_id in self._task_by_id:
            raise ValueError(f"Task with id '{task.task_id}' already exists")
        self._tasks.append(task)
        self._task_by_id[task.task_id] = task
        self._dirty = True

    def add_tasks(self, tasks: Iterable[Task]) -> None:
        for task in tasks:
            self.add_task(task)

    def add_from_dict(self, data: Mapping[str, str]) -> None:
        for task_id, text in data.items():
            self.add_task(Task(task_id=task_id, text=text))

    def get(self, task_id: str) -> Optional[Task]:
        return self._task_by_id.get(task_id)

    def build(self) -> None:
        self._doc_vectors = []
        self._doc_norms = []
        self._idf = {}

        if not self._tasks:
            self._dirty = False
            return

        doc_freq = Counter()
        for task in self._tasks:
            tokens = set(_tokenize(task.text))
            doc_freq.update(tokens)

        total_docs = len(self._tasks)
        for token, freq in doc_freq.items():
            self._idf[token] = math.log((1 + total_docs) / (1 + freq)) + 1.0

        for task in self._tasks:
            token_counts = Counter(_tokenize(task.text))
            vector: Dict[str, float] = {}
            for token, count in token_counts.items():
                idf = self._idf.get(token)
                if idf is None:
                    continue
                vector[token] = (1.0 + math.log(count)) * idf
            norm = math.sqrt(sum(weight * weight for weight in vector.values()))
            self._doc_vectors.append(vector)
            self._doc_norms.append(norm)

        self._dirty = False

    def search(self, query: str, top_k: int = 5) -> List[TaskMatch]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if not query or not query.strip():
            return []

        self._ensure_built()
        if not self._tasks:
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        query_counts = Counter(tokens)
        query_vector: Dict[str, float] = {}
        for token, count in query_counts.items():
            idf = self._idf.get(token)
            if idf is None:
                continue
            query_vector[token] = (1.0 + math.log(count)) * idf

        if not query_vector:
            return []

        query_norm = math.sqrt(sum(weight * weight for weight in query_vector.values()))
        if query_norm == 0.0:
            return []

        matches: List[TaskMatch] = []
        for index, doc_vector in enumerate(self._doc_vectors):
            doc_norm = self._doc_norms[index]
            if doc_norm == 0.0:
                continue
            dot = sum(query_vector[token] * doc_vector.get(token, 0.0) for token in query_vector)
            if dot <= 0.0:
                continue
            score = dot / (query_norm * doc_norm)
            matches.append(TaskMatch(task=self._tasks[index], score=score))

        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:top_k]

    def _ensure_built(self) -> None:
        if self._dirty:
            self.build()

    @property
    def size(self) -> int:
        return len(self._tasks)

    @property
    def tasks(self) -> List[Task]:
        return list(self._tasks)
