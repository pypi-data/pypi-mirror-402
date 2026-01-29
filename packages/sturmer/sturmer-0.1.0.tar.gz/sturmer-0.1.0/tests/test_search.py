import pytest

from sturmer import Task, TaskIndex


def test_search_finds_relevant_tasks():
    index = TaskIndex(
        [
            Task(task_id="t1", text="Add fractions and decimals"),
            Task(task_id="t2", text="Solve a linear equation"),
            Task(task_id="t3", text="Fractions practice with word problems"),
        ]
    )

    matches = index.search("fractions", top_k=2)

    assert len(matches) == 2
    ids = {match.task.task_id for match in matches}
    assert ids == {"t1", "t3"}
    assert all(match.score > 0 for match in matches)


def test_top_k_limits_results():
    index = TaskIndex(
        [
            Task(task_id="t1", text="Add fractions and decimals"),
            Task(task_id="t2", text="Fractions and percents"),
        ]
    )

    matches = index.search("fractions", top_k=1)
    assert len(matches) == 1
    assert matches[0].task.task_id in {"t1", "t2"}


def test_empty_query_returns_empty_list():
    index = TaskIndex([Task(task_id="t1", text="Add fractions")])
    assert index.search("") == []
    assert index.search("   ") == []


def test_unknown_tokens_returns_empty_list():
    index = TaskIndex([Task(task_id="t1", text="Add fractions")])
    assert index.search("integration") == []


def test_duplicate_id_raises():
    index = TaskIndex([Task(task_id="t1", text="Add fractions")])
    with pytest.raises(ValueError):
        index.add_task(Task(task_id="t1", text="Duplicate"))


def test_top_k_must_be_positive():
    index = TaskIndex([Task(task_id="t1", text="Add fractions")])
    with pytest.raises(ValueError):
        index.search("fractions", top_k=0)


def test_from_dict_builds_tasks():
    data = {"t1": "Add fractions", "t2": "Solve equations"}
    index = TaskIndex.from_dict(data)

    assert index.size == 2
    assert index.get("t2").text == "Solve equations"
