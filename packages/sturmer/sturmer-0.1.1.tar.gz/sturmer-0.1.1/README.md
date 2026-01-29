# sturmer

Local task search library that returns ready-made solutions for a text query.

## Install

```bash
pip install sturmer
```

## Use

```python
from sturmer import find

solutions = find("найдите корни", top_k=3)
for solution in solutions:
    print(solution)
```

## Built-in tasks

Tasks are bundled inside the package at `sturmer/data/tasks.py`. Each task is a dict
with `text` and `solution`. Use triple-quoted strings for long answers.

Example `sturmer/data/tasks.py`:
```python
TASKS = [
    {
        "text": "Найдите корни уравнения x^2 - 5x + 6 = 0.",
        "solution": """Разложим на множители:
(x - 2)(x - 3) = 0
Ответ: x = 2, x = 3.""",
    }
]
```
