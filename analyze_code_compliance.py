#!/usr/bin/env python3

import os
import re
import sys
import argparse
from pathlib import Path

"""
Code compliance analyzer for test files.

This script checks test files in the specified directory against compliance rules:
1. No mockups or fallback routines within test code
2. Test code should always use tests_dest/test_helpers/service_imports.py
3. Direct source imports should be visible, not hidden
4. No breaking encapsulation (accessing private methods/attributes)
5. Diagnostic files should be created before making significant changes
"""

# Patterns to check
MOCKUP_PATTERNS = [
    r"# Optional imports",
    r"try:.*?except ImportError",
    r"try:.*?except Exception",
    r"if ImportError",
    r"if Exception",
]
DIRECT_SERVICE_IMPORT_PATTERN = r"from\s+services\.[a-zA-Z0-9_]+\s+import"
DIRECT_MODEL_IMPORT_PATTERN = r"from\s+models\.[a-zA-Z0-9_]+\s+import"
FALLBACK_ROUTINE_PATTERN = r"except\s+[a-zA-Z0-9_]+\s+as\s+[a-zA-Z0-9_]+\s*:.*?pass"
ENCAPSULATION_BREAK_PATTERN = r"\._[a-zA-Z0-9_]+"
# Exclude special dunder methods (those with double underscores)
PRIVATE_METHOD_PATTERN = r"def\s+_(?!_)[a-zA-Z0-9_]+"
SERVICE_IMPORTS_PATTERN = r"from\s+tests_dest\.test_helpers\.service_imports\s+import"

class ComplianceIssue:
    def __init__(self, file_path, line_num, issue_type, line, description):
        self.file_path = file_path
        self.line_num = line_num
        self.issue_type = issue_type
        self.line = line.strip()
        self.description = description
    
    def __str__(self):
        return f"{self.file_path}:{self.line_num} - {self.issue_type}: {self.description}\n  {self.line}"

def check_file_compliance(file_path):
    """Check a single file for compliance issues."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return []
    
    # Check for mockup patterns
    for pattern in MOCKUP_PATTERNS:
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            line = lines[line_num - 1] if line_num <= len(lines) else ""
            issues.append(ComplianceIssue(
                file_path, line_num, "Mockup/Fallback",
                line, "Contains mockup or fallback routine"
            ))
    
    # Check for direct service imports
    matches = re.finditer(DIRECT_SERVICE_IMPORT_PATTERN, content, re.MULTILINE)
    for match in matches:
        line_num = content[:match.start()].count('\n') + 1
        line = lines[line_num - 1] if line_num <= len(lines) else ""
        issues.append(ComplianceIssue(
            file_path, line_num, "Direct Service Import",
            line, "Direct import from services module instead of using service_imports.py"
        ))
    
    # Check for direct model imports
    matches = re.finditer(DIRECT_MODEL_IMPORT_PATTERN, content, re.MULTILINE)
    for match in matches:
        line_num = content[:match.start()].count('\n') + 1
        line = lines[line_num - 1] if line_num <= len(lines) else ""
        issues.append(ComplianceIssue(
            file_path, line_num, "Direct Model Import",
            line, "Direct import from models module instead of using service_imports.py"
        ))
    
    # Check for fallback routines
    matches = re.finditer(FALLBACK_ROUTINE_PATTERN, content, re.MULTILINE | re.DOTALL)
    for match in matches:
        line_num = content[:match.start()].count('\n') + 1
        line = lines[line_num - 1] if line_num <= len(lines) else ""
        issues.append(ComplianceIssue(
            file_path, line_num, "Fallback Routine",
            line, "Contains fallback routine that hides errors"
        ))
    
    # Check for encapsulation breaks
    matches = re.finditer(ENCAPSULATION_BREAK_PATTERN, content, re.MULTILINE)
    for match in matches:
        line_num = content[:match.start()].count('\n') + 1
        line = lines[line_num - 1] if line_num <= len(lines) else ""
        issues.append(ComplianceIssue(
            file_path, line_num, "Encapsulation Break",
            line, "Accessing private attribute or method (with leading underscore)"
        ))
    
    # Check for private methods in test code
    matches = re.finditer(PRIVATE_METHOD_PATTERN, content, re.MULTILINE)
    for match in matches:
        line_num = content[:match.start()].count('\n') + 1
        line = lines[line_num - 1] if line_num <= len(lines) else ""
        issues.append(ComplianceIssue(
            file_path, line_num, "Private Method",
            line, "Test code should not use private methods (with leading underscore)"
        ))
    
    # Check if service_imports.py is used
    if re.search(SERVICE_IMPORTS_PATTERN, content) is None and (
        re.search(DIRECT_SERVICE_IMPORT_PATTERN, content) is not None or
        re.search(DIRECT_MODEL_IMPORT_PATTERN, content) is not None
    ):
        issues.append(ComplianceIssue(
            file_path, 1, "Missing Service Imports",
            "", "File imports services or models but doesn't use service_imports.py"
        ))
    
    return issues

def analyze_directory(directory_path, recursive=True):
    """Analyze Python files in the directory.
    
    Args:
        directory_path: Directory to analyze
        recursive: If True, recursively scan subdirectories
    
    Returns:
        Dictionary of file paths to issues
    """
    issues_by_file = {}
    scanned_files = []
    
    if recursive:
        # Recursively walk through all subdirectories
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    scanned_files.append(file_path)
                    issues = check_file_compliance(file_path)
                    if issues:
                        issues_by_file[file_path] = issues
    else:
        # Only scan files in the specified directory (not subdirectories)
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path) and file.endswith('.py'):
                scanned_files.append(file_path)
                issues = check_file_compliance(file_path)
                if issues:
                    issues_by_file[file_path] = issues
    
    return issues_by_file, scanned_files

def analyze_multiple_paths(paths, recursive=True):
    """Analyze multiple file or directory paths.
    
    Args:
        paths: List of file or directory paths to analyze
        recursive: If True, recursively scan subdirectories
    
    Returns:
        Dictionary of file paths to issues and list of scanned files
    """
    all_issues = {}
    all_scanned_files = []
    
    for path in paths:
        if os.path.isdir(path):
            issues, scanned_files = analyze_directory(path, recursive)
            all_issues.update(issues)
            all_scanned_files.extend(scanned_files)
        elif os.path.isfile(path):
            issues = check_file_compliance(path)
            all_scanned_files.append(path)
            if issues:
                all_issues[path] = issues
        else:
            print(f"Warning: {path} is not a valid file or directory", file=sys.stderr)
    
    return all_issues, all_scanned_files

def print_summary(issues_by_file, scanned_files=None, list_files=False):
    """Print a summary of compliance issues.
    
    Args:
        issues_by_file: Dictionary of file paths to issues
        scanned_files: List of all scanned files (for displaying stats)
        list_files: If True, list all scanned files
    """
    total_issues = sum(len(issues) for issues in issues_by_file.values())
    total_files = len(issues_by_file)
    
    print(f"\n=== Code Compliance Analysis Summary ===")
    print(f"Files with issues: {total_files}")
    if scanned_files:
        print(f"Total files scanned: {len(scanned_files)}")
    print(f"Total issues found: {total_issues}")
    
    issue_types = {}
    for issues in issues_by_file.values():
        for issue in issues:
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
    
    if issue_types:
        print("\nIssue Types:")
        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {issue_type}: {count}")
    
    if list_files and scanned_files:
        print("\n=== Scanned Files ===")
        for file_path in sorted(scanned_files):
            if file_path in issues_by_file:
                issue_count = len(issues_by_file[file_path])
                print(f"  {file_path} ({issue_count} issues)")
            else:
                print(f"  {file_path} (no issues)")
    
    if issues_by_file:
        print("\n=== Detailed Issues by File ===")
        for file_path, issues in sorted(issues_by_file.items()):
            print(f"\n{file_path} ({len(issues)} issues):")
            for issue in sorted(issues, key=lambda x: x.line_num):
                print(f"  Line {issue.line_num}: {issue.issue_type} - {issue.description}")
                print(f"    {issue.line}")

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Analyze code compliance in test files")
    parser.add_argument("paths", nargs="+", help="Files or directories to analyze")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false",
                      help="Don't recursively scan subdirectories")
    parser.add_argument("--list-files", action="store_true",
                      help="List all scanned files in the output")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    print(f"Analyzing code compliance in: {', '.join(args.paths)}...")
    issues_by_file, scanned_files = analyze_multiple_paths(args.paths, args.recursive)
    
    print_summary(issues_by_file, scanned_files, args.list_files)
    
    return 0 if not issues_by_file else 1

if __name__ == "__main__":
    sys.exit(main()) 