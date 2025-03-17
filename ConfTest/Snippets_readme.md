# SnippetForTests

A utility script for managing code snippets in test files within a Python project.

## What is it?

`SnippetForTests.py` is a Python script that helps manage import boilerplate in test files. It can automatically add standard import code to the beginning of all test files in a directory tree, verify which files have the snippet already, and remove snippets when needed.

## Features

### Path Handling
- Supports both relative and absolute paths
- Works with Windows path names, including spaces (e.g., "My Documents")
- Uses Python's `pathlib` for cross-platform path operations

### Snippet Management
- Adds markers to clearly identify the snippet in files
- Validates Python syntax after adding/removing snippets
- Provides detailed feedback on operations
- Properly handles both `.txt` and `.py` format snippet files

### Safety Features
- Option to backup files before making changes (using `--backup`)
- Check-only mode to preview without modifying (using `--check-only`)
- Prevents duplicate snippet insertions
- Validates that files remain valid Python after modification
- Detects and handles special Python file features (.py snippet files)

## Usage Examples

### Adding Snippets

To add snippets to all test files:
```bash
python SnippetForTests.py -source "./tests-dest" -snippet "./code_snippet_for_test_files.txt" -option "ADD"
```

The script works with both `.txt` and `.py` snippet files:
```bash
python SnippetForTests.py -source "./tests-dest" -snippet "./my_imports.py" -option "ADD"
```

### Removing Snippets

To remove snippets from all test files:
```bash
python SnippetForTests.py -source "./tests-dest" -option "REMOVE"
```

### Safety Options

Create backups before making changes:
```bash
python SnippetForTests.py -source "./tests-dest" -snippet "./code_snippet_for_test_files.txt" -option "ADD" --backup
```

Check which files already have snippets without modifying anything:
```bash
python SnippetForTests.py -source "./tests-dest" -option "ADD" --check-only
```

## How It Works

The script uses clear markers to identify the snippet in files:

```python
# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
import os
import sys
from pathlib import Path

# Add project root to path
test_file = Path(__file__).resolve()
test_dir = test_file.parent
# ...more import code...
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
```

These markers ensure the snippet can be cleanly removed later, even if the rest of the file has changed.

## Command-Line Arguments

| Argument       | Description                                                |
|----------------|------------------------------------------------------------|
| `-source`      | Root directory containing test files to process (required) |
| `-snippet`     | Path to snippet file (required for ADD without --check-only) |
| `-option`      | Operation to perform: ADD or REMOVE (required)             |
| `--backup`     | Create backups of files before modifying                   |
| `--check-only` | Report on files without modifying them                     |

## Requirements

- Python 3.6 or higher
- No external dependencies

## Integration with Test Setup

This script is designed to work with the test setup infrastructure:

1. `test_setup.py` initializes the environment variables and test directories
2. `SnippetForTests.py` adds the necessary import code to test files 
3. `test_import_helper.py` handles path resolution during test execution

Together, these components provide a robust testing infrastructure that ensures all tests can properly import the application code regardless of their location in the directory tree.
