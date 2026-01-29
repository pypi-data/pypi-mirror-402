from __future__ import annotations

import importlib
import json
from importlib import resources
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Union

from .search import Task

PathLike = Union[str, Path]
DEFAULT_TASKS_SOURCE = "sturmer.data.tasks"


def load_tasks_json(path: PathLike) -> List[Task]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected a list of task records in JSON")
    return [_task_from_record(record, index + 1) for index, record in enumerate(data)]


def dump_tasks_json(path: PathLike, tasks: Iterable[Task]) -> None:
    records = [_task_to_record(task) for task in tasks]
    Path(path).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def load_tasks_jsonl(path: PathLike) -> List[Task]:
    tasks: List[Task] = []
    index = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        index += 1
        record = json.loads(line)
        tasks.append(_task_from_record(record, index))
    return tasks


def dump_tasks_jsonl(path: PathLike, tasks: Iterable[Task]) -> None:
    lines = [json.dumps(_task_to_record(task), ensure_ascii=False) for task in tasks]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _task_from_record(record: Mapping[str, object], index: int) -> Task:
    if not isinstance(record, Mapping):
        raise ValueError("Task record must be a mapping")
    text = record.get("text")
    if text is None:
        raise ValueError("Task record must include 'text'")
    solution = record.get("solution")
    task_id = record.get("id", record.get("task_id", f"auto-{index:05d}"))
    return Task(task_id=str(task_id), text=str(text), solution=solution)


def _task_to_record(task: Task) -> Dict[str, object]:
    record: Dict[str, object] = {"text": task.text}
    if task.solution is not None:
        record["solution"] = task.solution
    return record


def load_builtin_tasks(source: str = DEFAULT_TASKS_SOURCE) -> List[Task]:
    if source.endswith(".jsonl"):
        loader = load_tasks_jsonl
        data = resources.files("sturmer.data").joinpath(source)
        with resources.as_file(data) as path:
            return loader(path)
    if source.endswith(".json"):
        loader = load_tasks_json
        data = resources.files("sturmer.data").joinpath(source)
        with resources.as_file(data) as path:
            return loader(path)

    module_path = source
    if source.endswith(".py"):
        module_path = source[:-3]
    if "." not in module_path:
        module_path = f"sturmer.data.{module_path}"

    module = importlib.import_module(module_path)
    records = getattr(module, "TASKS", None)
    if records is None:
        raise ValueError(f"Module '{module_path}' does not define TASKS")
    if not isinstance(records, list):
        raise ValueError("TASKS must be a list of task records")

    tasks: List[Task] = []
    for index, record in enumerate(records, 1):
        tasks.append(_task_from_record(record, index))
    return tasks
