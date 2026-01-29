import pytest

from sturmer import TaskIndex


@pytest.mark.smoke
def test_smoke_search_roundtrip():
    index = TaskIndex.from_dict(
        {
            "t1": "Add fractions and decimals",
            "t2": "Solve a linear equation",
        }
    )

    matches = index.search("fractions", top_k=1)

    assert matches
    assert matches[0].task.task_id == "t1"
