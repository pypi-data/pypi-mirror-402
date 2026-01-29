# tflow

A task flow management tool for syncing todo files with taskwarrior.

## Installation

### Development Installation (Editable Mode)

Install the package in editable mode so you can use the `tflow` command anywhere:

```bash
# In the project directory
pip install -e .
```

### Regular Installation

```bash
pip install .
```

## Usage

After installation, you can use the `tflow` command directly:

```bash
# Show available commands
tflow --help

# Read and import tasks from todo files
tflow read -c /path/to/files.yaml

# Modify tasks
tflow modfiy -a "new_data" -c "command"
```

## Configuration

Create a `files.yaml` configuration file to specify your todo file locations:

```yaml
sources:
  - id: "project1"
    type: "static"
    path:
      darwin: "/path/to/project1.todo"
      wsl: "/mnt/path/to/project1.todo"
  - id: "daily"
    type: "daily"
    path:
      darwin: "/path/to/agenda/todo"
      wsl: "/mnt/path/to/agenda/todo"
```

## Development

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Requirements

- Python >= 3.10
- taskwarrior installed on your system
