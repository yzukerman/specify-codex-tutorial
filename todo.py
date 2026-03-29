#!/usr/bin/env -S uv run python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TASKS_FILE = Path(__file__).with_name("tasks.json")
VALID_STATUSES = {"pending", "completed"}
MAX_TASK_LENGTH = 100
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"


def load_tasks() -> list[dict[str, Any]]:
    if not TASKS_FILE.exists():
        return []

    try:
        data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse {TASKS_FILE.name}: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError(f"{TASKS_FILE.name} must contain a JSON list.")

    for task in data:
        validate_task_record(task)

    return data


def validate_task_record(task: Any) -> None:
    if not isinstance(task, dict):
        raise ValueError(f"Each task in {TASKS_FILE.name} must be an object.")

    if not isinstance(task.get("id"), int):
        raise ValueError("Each task must include an integer 'id'.")

    text = task.get("task")
    if not isinstance(text, str) or not text or len(text) > MAX_TASK_LENGTH:
        raise ValueError(
            f"Each task must include a non-empty 'task' string up to {MAX_TASK_LENGTH} characters."
        )

    status = task.get("status")
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Each task must include a valid 'status' of {sorted(VALID_STATUSES)}."
        )


def save_tasks(tasks: list[dict[str, Any]]) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")


def next_task_id(tasks: list[dict[str, Any]]) -> int:
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1


def find_task(tasks: list[dict[str, Any]], task_id: int) -> dict[str, Any] | None:
    return next((task for task in tasks if task["id"] == task_id), None)


def colorize(text: str, status: str) -> str:
    if status == "pending":
        return f"{RED}{text}{RESET}"
    if status == "completed":
        return f"{GREEN}{text}{RESET}"
    return text


def render_table(tasks: list[dict[str, Any]]) -> str:
    headers = ("ID", "Task", "Status")
    rows = [(str(task["id"]), task["task"], task["status"]) for task in tasks]
    widths = [len(header) for header in headers]

    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]

    def format_row(row: tuple[str, str, str]) -> str:
        return " | ".join(value.ljust(width) for value, width in zip(row, widths))

    separator = "-+-".join("-" * width for width in widths)
    table_lines = [format_row(headers), separator]

    if rows:
        for row in rows:
            status = row[2]
            colored_row = (
                row[0].ljust(widths[0]),
                colorize(row[1].ljust(widths[1]), status),
                colorize(row[2].ljust(widths[2]), status),
            )
            table_lines.append(" | ".join(colored_row))
    else:
        table_lines.append("No tasks found.")

    return "\n".join(table_lines)


def add_task(args: argparse.Namespace) -> int:
    task_text = args.text.strip()
    if not task_text:
        print("Error: task cannot be empty.", file=sys.stderr)
        return 1

    if len(task_text) > MAX_TASK_LENGTH:
        print(
            f"Error: task must be {MAX_TASK_LENGTH} characters or fewer.",
            file=sys.stderr,
        )
        return 1

    tasks = load_tasks()
    task = {
        "id": next_task_id(tasks),
        "task": task_text,
        "status": "pending",
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f'Added task {task["id"]}: {task["task"]}')
    return 0


def list_tasks(_: argparse.Namespace) -> int:
    tasks = load_tasks()
    print(render_table(tasks))
    return 0


def list_completed_tasks(_: argparse.Namespace) -> int:
    tasks = load_tasks()
    completed_tasks = [task for task in tasks if task["status"] == "completed"]
    print(render_table(completed_tasks))
    return 0


def mark_done(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    task = find_task(tasks, args.id)
    if task is None:
        print("Error: task does not exist.", file=sys.stderr)
        return 1

    task["status"] = "completed"
    save_tasks(tasks)
    print(f"Marked task {args.id} as completed.")
    return 0


def remove_task(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    task = find_task(tasks, args.id)
    if task is None:
        print("Error: task does not exist.", file=sys.stderr)
        return 1

    updated_tasks = [entry for entry in tasks if entry["id"] != args.id]
    save_tasks(updated_tasks)
    print(f"Removed task {args.id}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage tasks stored in tasks.json.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task.")
    add_parser.add_argument("text", help=f"Task text ({MAX_TASK_LENGTH} characters max).")
    add_parser.set_defaults(handler=add_task)

    list_parser = subparsers.add_parser("list", help="List all tasks.")
    list_parser.set_defaults(handler=list_tasks)

    completed_parser = subparsers.add_parser(
        "completed", help="List only completed tasks."
    )
    completed_parser.set_defaults(handler=list_completed_tasks)

    done_parser = subparsers.add_parser("done", help="Mark a task as completed.")
    done_parser.add_argument("id", type=int, help="The task ID.")
    done_parser.set_defaults(handler=mark_done)

    remove_parser = subparsers.add_parser("remove", help="Remove a task.")
    remove_parser.add_argument("id", type=int, help="The task ID.")
    remove_parser.set_defaults(handler=remove_task)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return args.handler(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
