# PyShala

A self-hosted interactive Python training platform for delivering custom lessons with live code execution and automated feedback.

## Features

- **Interactive Lessons**: Write and run Python code directly in the browser
- **Automated Testing**: Instant feedback with pass/fail results for each test case
- **Custom Content**: Create your own lessons using simple YAML files
- **Data File Support**: Lessons can include CSV, JSON, and other data files
- **Self-Hosted**: Deploy on your own infrastructure
- **No External Dependencies**: Code execution runs locally (no Docker required)

## Quick Start

### Installation

```bash
pip install pyshala
```

### Command Line

```bash
# Run with default lessons directory (./lessons)
pyshala

# Run with custom lessons path
pyshala ./my_lessons

# Run with custom port
pyshala ./my_lessons --port 8080

# See all options
pyshala --help
```

**CLI Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `lessons_path` | `./lessons` | Path to lessons directory |
| `--host` | `0.0.0.0` | Host address to bind |
| `--port`, `-p` | `3000` | Frontend port |
| `--backend-port` | `8000` | Backend API port |
| `--max-execution-time` | `10.0` | Max code execution time (seconds) |
| `--python-path` | Current interpreter | Python interpreter for execution |
| `--loglevel` | `info` | Logging level (debug/info/warning/error) |
| `--app-name` | `Learn Python` | Application name displayed in the UI |
| `--app-description` | (see below) | Description displayed on home page |
| `--version`, `-v` | | Show version and exit |

### Python API

```python
from pyshala import PyShala

# Create and run the app with your lessons
app = PyShala(lessons_path="./my_lessons")
app.run()
```

Open your browser at http://localhost:3000

**Configuration Options:**

```python
from pyshala import PyShala

app = PyShala(
    lessons_path="./lessons",      # Path to lesson YAML files
    host="0.0.0.0",                # Host address
    port=3000,                     # Frontend port
    backend_port=8000,             # Backend API port
    max_execution_time=10.0,       # Max code execution time (seconds)
    python_path="/usr/bin/python3", # Python interpreter for execution
    loglevel="info",               # Logging level
)
app.run()
```

**Alternative: Using create_app**

```python
from pyshala import create_app

app = create_app(lessons_path="./my_lessons", port=8080)
app.run()
```

## Creating Lessons

Lessons are defined using YAML files organized into modules. For more information about writing lessons, see [LESSONS.md](lessons.md).

### Directory Structure

```
lessons/
├── python_basics/           # Module directory
│   ├── module.yaml          # Module metadata
│   ├── 01_hello_world.yaml  # Lesson file
│   ├── 02_variables.yaml
│   └── sales_data.csv       # Data file for lessons
└── control_flow/
    ├── module.yaml
    └── 01_if_statements.yaml
```

### Module Configuration (`module.yaml`)

```yaml
name: "Python Basics"
description: "Learn the fundamentals of Python programming"
order: 1

lessons:
  - 01_hello_world.yaml
  - 02_variables.yaml
```

### Lesson Configuration

```yaml
title: "Hello, World!"
description: "Write your first Python program"
order: 0

instructions: |
  # Hello, World!

  Use the `print()` function to display text.

  ## Your Task
  Print "Hello, World!"

starter_code: |
  # Write your code here

test_cases:
  - description: "Prints greeting"
    stdin: ""
    expected_output: "Hello, World!"

# Optional: include data files
data_files:
  - name: data.csv
    path: data.csv
```

### Test Case Options

| Field | Description |
|-------|-------------|
| `stdin` | Input provided to the program |
| `expected_output` | Expected stdout output |
| `description` | Test description shown to learner |
| `hidden` | If true, test details hidden from learner |

## Development

### Setup

```bash
git clone https://github.com/dkedar7/pyshala.git
cd pyshala
pip install -e ".[dev]"
```

### Running Directly with Reflex

```bash
reflex run
```

### Running Tests

```bash
pytest tests/ -v
```

### Building the Package

```bash
python -m build
```

## Tech Stack

- **Frontend/Backend**: [Reflex](https://reflex.dev) (Python)
- **Code Editor**: Monaco Editor via reflex-monaco
- **Code Execution**: Local Python subprocess (sandboxed)

## License

MIT License
