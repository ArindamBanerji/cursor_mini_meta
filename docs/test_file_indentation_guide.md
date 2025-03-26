# Test File Indentation Guide

## Common Indentation Issue

Many test files in the codebase have a common indentation error in the standard snippet section that causes pytest to fail with an `IndentationError`. The issue appears as:

```python
"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
"""
        # Add project root to path
        if str(project_root) not in sys.path:  # <- IndentationError occurs here
            sys.path.insert(0, str(project_root))
```

## The Problem

The indented block after the docstring is missing a `try:` statement, which should come immediately after the docstring and before the indented code. 

This issue affects many test files across various test directories, including integration tests, unit tests, and diagnostic tests.

## How to Fix It

When encountering this error, manually add the missing `try:` statement after the docstring:

```python
"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
"""
try:  # <- Add this line
    # Add project root to path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
```

## Steps for Fixing a Test File

1. Open the test file with the indentation error
2. Find the docstring ending with "5. Logging configuration"
3. Add a `try:` statement immediately after the docstring
4. Verify that the `except Exception as e:` block is already present
5. Run the test individually to verify the fix: `python -m pytest path/to/fixed_test.py -v`

## Avoiding This Issue in New Test Files

For new test files:

1. Start with the template in `docs/test_file_template.py`
2. Do not modify the standard snippet section (between BEGIN_SNIPPET_INSERTION and END_SNIPPET_INSERTION)
3. Ensure the `try:` statement is present after the standard docstring
4. Validate any new test file with pytest before committing it

## Standard Snippet Structure

The correct structure for the snippet section is:

```python
# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from types import ModuleType

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
"""
try:
    # Add project root to path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    logging.warning("Could not find import_helper.py. Using fallback configuration.")
except Exception as e:
    logging.warning(f"Failed to import import_helper: {{e}}. Using fallback configuration.")
    # Add project root to path
    current_file = Path(__file__).resolve()
    test_dir = current_file.parent.parent
    project_root = test_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
```

## Automated Verification

While we should manually fix each file, you can use this one-line check to verify if a test file has the correct structure:

```bash
grep -A 1 "5. Logging configuration" test_file.py
```

The output should show the docstring ending followed by a `try:` statement. 