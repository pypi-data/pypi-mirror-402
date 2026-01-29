from sturmer import (
    Task,
    dump_tasks_json,
    dump_tasks_jsonl,
    load_builtin_tasks,
    load_tasks_json,
    load_tasks_jsonl,
)


def test_json_roundtrip(tmp_path):
    tasks = [
        Task(task_id="t1", text="Add fractions", solution="Add numerators"),
        Task(task_id="t2", text="Solve equations"),
    ]
    path = tmp_path / "tasks.json"

    dump_tasks_json(path, tasks)
    loaded = load_tasks_json(path)

    assert [task.text for task in loaded] == ["Add fractions", "Solve equations"]
    assert loaded[0].solution == "Add numerators"
    assert loaded[1].solution is None


def test_jsonl_roundtrip(tmp_path):
    tasks = [
        Task(task_id="t1", text="Add fractions", solution="Add numerators"),
        Task(task_id="t2", text="Solve equations"),
    ]
    path = tmp_path / "tasks.jsonl"

    dump_tasks_jsonl(path, tasks)
    loaded = load_tasks_jsonl(path)

    assert [task.text for task in loaded] == ["Add fractions", "Solve equations"]


def test_load_builtin_tasks_has_entries():
    tasks = load_builtin_tasks()

    assert tasks
    assert all(task.task_id and task.text for task in tasks)
