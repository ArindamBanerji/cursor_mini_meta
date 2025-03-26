import os
import sys
from pathlib import Path

def fix_indentation_in_file(file_path: str) -> None:
    """Fix indentation in a test file by removing incorrect indentation."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    fixed_lines = []
    in_snippet = False
    for line in lines:
        if "BEGIN_SNIPPET_INSERTION" in line:
            in_snippet = True
            fixed_lines.append(line)
        elif "END_SNIPPET_INSERTION" in line:
            in_snippet = False
            fixed_lines.append(line)
        elif in_snippet:
            # Remove any indentation for lines in the snippet section
            stripped = line.lstrip()
            if stripped:  # Only append non-empty lines
                fixed_lines.append(stripped)
        else:
            fixed_lines.append(line)

    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)

def main():
    # Get the project root directory
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    # Find all integration test files
    integration_dir = project_root / "tests_dest" / "integration"
    if not integration_dir.exists():
        print(f"Integration test directory not found: {integration_dir}")
        return

    # Fix indentation in all Python files in the integration directory
    for file_path in integration_dir.glob("*.py"):
        if file_path.name.startswith("test_"):
            print(f"Fixing indentation in {file_path}")
            fix_indentation_in_file(str(file_path))

if __name__ == "__main__":
    main() 