import json
import sys

import pytest

import todo


class FakeTasksFile:
    def __init__(self, content: str | None = None) -> None:
        self.content = content
        self.name = "tasks.json"

    def exists(self) -> bool:
        return self.content is not None

    def read_text(self, encoding: str = "utf-8") -> str:
        assert encoding == "utf-8"
        if self.content is None:
            raise FileNotFoundError(self.name)
        return self.content

    def write_text(self, text: str, encoding: str = "utf-8") -> int:
        assert encoding == "utf-8"
        self.content = text
        return len(text)


@pytest.fixture
def fake_tasks_file(monkeypatch: pytest.MonkeyPatch) -> FakeTasksFile:
    fake_file = FakeTasksFile()
    monkeypatch.setattr(todo, "TASKS_FILE", fake_file)
    return fake_file


def run_cli(args: list[str], monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.setattr(sys, "argv", ["todo.py", *args])
    return todo.main()


def colored(text: str, status: str) -> str:
    if status == "pending":
        return f"{todo.RED}{text}{todo.RESET}"
    if status == "completed":
        return f"{todo.GREEN}{text}{todo.RESET}"
    return text


def test_list_shows_empty_state(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run_cli(["list"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ID | Task | Status" in captured.out
    assert "No tasks found." in captured.out
    assert captured.err == ""
    assert fake_tasks_file.content is None


def test_add_creates_first_task(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run_cli(["add", "Buy milk"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Added task 1: Buy milk\n"
    assert captured.err == ""
    assert json.loads(fake_tasks_file.content) == [
        {"id": 1, "task": "Buy milk", "status": "pending"}
    ]


def test_add_rejects_empty_task(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run_cli(["add", "   "], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "Error: task cannot be empty.\n"
    assert fake_tasks_file.content is None


def test_add_rejects_task_over_max_length(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run_cli(["add", "x" * 101], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "Error: task must be 100 characters or fewer.\n"
    assert fake_tasks_file.content is None


def test_done_marks_existing_task_completed(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_tasks_file.content = json.dumps(
        [{"id": 1, "task": "Buy milk", "status": "pending"}]
    )

    exit_code = run_cli(["done", "1"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Marked task 1 as completed.\n"
    assert captured.err == ""
    assert json.loads(fake_tasks_file.content) == [
        {"id": 1, "task": "Buy milk", "status": "completed"}
    ]


def test_done_returns_error_for_missing_task(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_tasks_file.content = json.dumps(
        [{"id": 1, "task": "Buy milk", "status": "pending"}]
    )

    exit_code = run_cli(["done", "99"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "Error: task does not exist.\n"
    assert json.loads(fake_tasks_file.content) == [
        {"id": 1, "task": "Buy milk", "status": "pending"}
    ]


def test_remove_deletes_existing_task(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_tasks_file.content = json.dumps(
        [
            {"id": 1, "task": "Buy milk", "status": "pending"},
            {"id": 2, "task": "Walk dog", "status": "completed"},
        ]
    )

    exit_code = run_cli(["remove", "1"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Removed task 1.\n"
    assert captured.err == ""
    assert json.loads(fake_tasks_file.content) == [
        {"id": 2, "task": "Walk dog", "status": "completed"}
    ]


def test_remove_returns_error_for_missing_task(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_tasks_file.content = json.dumps(
        [{"id": 1, "task": "Buy milk", "status": "pending"}]
    )

    exit_code = run_cli(["remove", "99"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "Error: task does not exist.\n"
    assert json.loads(fake_tasks_file.content) == [
        {"id": 1, "task": "Buy milk", "status": "pending"}
    ]


def test_list_displays_existing_tasks(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_tasks_file.content = json.dumps(
        [
            {"id": 1, "task": "Buy milk", "status": "pending"},
            {"id": 2, "task": "Walk dog", "status": "completed"},
        ]
    )

    exit_code = run_cli(["list"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"1  | {colored('Buy milk', 'pending')} | {colored('pending  ', 'pending')}" in captured.out
    assert f"2  | {colored('Walk dog', 'completed')} | {colored('completed', 'completed')}" in captured.out
    assert captured.err == ""


def test_completed_lists_only_completed_tasks(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_tasks_file.content = json.dumps(
        [
            {"id": 1, "task": "Buy milk", "status": "pending"},
            {"id": 2, "task": "Walk dog", "status": "completed"},
        ]
    )

    exit_code = run_cli(["completed"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "1  |" not in captured.out
    assert f"2  | {colored('Walk dog', 'completed')} | {colored('completed', 'completed')}" in captured.out
    assert captured.err == ""


def test_completed_shows_empty_state_when_no_completed_tasks(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_tasks_file.content = json.dumps(
        [{"id": 1, "task": "Buy milk", "status": "pending"}]
    )

    exit_code = run_cli(["completed"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ID | Task | Status" in captured.out
    assert "No tasks found." in captured.out
    assert captured.err == ""


def test_main_returns_error_for_invalid_json(
    fake_tasks_file: FakeTasksFile,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_tasks_file.content = "{not valid json"

    exit_code = run_cli(["list"], monkeypatch)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.startswith("Error: Failed to parse tasks.json:")
