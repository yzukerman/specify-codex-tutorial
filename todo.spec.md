# To-Do CLI Specification v1.0

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

## Validation Rules
1. If a task does not exist when a user wants to set is as done or remove it, please show an error saying the task does not exist.
