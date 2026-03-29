# To-Do CLI Specification v1.1

## 🎯 Scope
A stateless CLI tool that manages tasks via a local `tasks.json`.

## 💾 Schema
- id: Integer (Auto-incrementing)
- task: String (Max 100 chars)
- status: Enum ["pending", "completed"]

## 🛠 Required Commands
1. `add "text"`: Append a new task.
2. `list`: Display all tasks in a formatted table.
3. `done <id>`: Update status to completed.
4. `remove <id>`: Delete a task.
5. `completed`: List only completed tasks

## Validation Rules
1. If a task does not exist when a user wants to set is as done or remove it, please show an error saying the task does not exist.

## Development requirement
1. Make sure that you are using the Python environment tool uv
2. All needed libraries must be installed into that environment
3. Every time the applicaiton runs, it must run the environment

## User interface
1. Display pending tasks in red
2. Display completed tasks in green
