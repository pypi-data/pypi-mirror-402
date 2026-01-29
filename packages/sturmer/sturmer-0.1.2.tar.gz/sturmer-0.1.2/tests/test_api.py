from sturmer import find, refresh_builtin_index


def test_find_uses_builtin_tasks():
    refresh_builtin_index()
    solutions = find("найдите корни", top_k=1)

    assert solutions
    result = solutions[0]
    assert isinstance(result, dict)
    assert result.get("text")
    assert result.get("solution")
