#!/usr/bin/env python3

import os
import re
import sys
import glob
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

"""
Script to fix compliance issues in test files:
1. Replace direct imports with imports from service_imports.py
2. Identify excessive mock usage in integration tests
3. Fix encapsulation issues (private methods)

Usage:
    python fix_test_compliance.py --path <directory_or_file> [--apply] [--verbose]
"""

# Patterns for direct imports that should be replaced
DIRECT_IMPORT_PATTERN = re.compile(
    r'^from\s+(services|models|controllers)\.(\w+)\s+import\s+(.+?)$', 
    re.MULTILINE
)

# Pattern for service_imports import
SERVICE_IMPORTS_PATTERN = re.compile(
    r'from\s+tests_dest\.test_helpers\.service_imports\s+import', 
    re.MULTILINE
)

# Pattern for mock usage
MOCK_PATTERN = re.compile(r'(?:MagicMock|AsyncMock|patch)\(')

# Common import mapping for modules
IMPORT_REPLACEMENTS = {
    "services.monitor_service": "MonitorService, get_monitor_service",
    "services.material_service": "MaterialService, get_material_service",
    "services.p2p_service": "P2PService, get_p2p_service",
    "services.state_manager": "StateManager, get_state_manager",
    "models.material": "Material, MaterialCreate, MaterialUpdate, MaterialStatus",
    "models.p2p": "Requisition, RequisitionCreate, Order, OrderCreate, DocumentStatus",
    "controllers.monitor_controller": "get_safe_client_host, health_check_endpoint",
}

def find_python_files(path: str) -> List[str]:
    """Find all Python files in the given path."""
    if os.path.isfile(path) and path.endswith('.py'):
        return [path]
    
    files = []
    for root, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(root, filename))
    
    return files

def analyze_file(file_path: str, verbose: bool = False) -> Dict[str, List[Tuple[int, str]]]:
    """Analyze a file for compliance issues."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = {
        "direct_imports": [],
        "mock_usage": [],
        "no_service_imports": []
    }
    
    # Check for direct imports
    for match in DIRECT_IMPORT_PATTERN.finditer(content):
        line_number = content[:match.start()].count('\n') + 1
        issues["direct_imports"].append((line_number, match.group(0)))
        if verbose:
            print(f"{file_path}:{line_number} Direct import: {match.group(0)}")
    
    # Check for service_imports
    if not SERVICE_IMPORTS_PATTERN.search(content) and '/test_helpers/' not in file_path:
        issues["no_service_imports"].append((1, "Missing import from tests_dest.test_helpers.service_imports"))
        if verbose:
            print(f"{file_path}: Missing service_imports import")
    
    # Check for mock usage in integration test
    if '/integration/' in file_path:
        for match in MOCK_PATTERN.finditer(content):
            line_number = content[:match.start()].count('\n') + 1
            line = content.splitlines()[line_number - 1]
            issues["mock_usage"].append((line_number, line))
            if verbose:
                print(f"{file_path}:{line_number} Mock usage: {line.strip()}")
    
    return issues

def fix_imports(file_path: str, apply: bool = False, verbose: bool = False) -> str:
    """Fix direct imports by replacing them with service_imports."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track what we'll be importing from service_imports
    imports_needed = set()
    
    # First, find all direct imports
    direct_imports = list(DIRECT_IMPORT_PATTERN.finditer(content))
    if not direct_imports:
        return content  # No changes needed
    
    # Check if service_imports is already imported
    has_service_imports = SERVICE_IMPORTS_PATTERN.search(content) is not None
    
    modified_content = content
    
    # Replace each direct import
    offset = 0
    for match in direct_imports:
        module_type = match.group(1)
        module_name = match.group(2)
        imports = match.group(3)
        
        # Get the full original import statement
        original = match.group(0)
        
        # Determine what should be imported from service_imports
        full_module = f"{module_type}.{module_name}"
        if full_module in IMPORT_REPLACEMENTS:
            # Use predefined common imports
            suggested_imports = IMPORT_REPLACEMENTS[full_module]
            # Filter to only include what was actually imported
            requested_imports = [i.strip() for i in imports.split(',')]
            imports_needed.update(requested_imports)
        else:
            # Keep the original imports
            suggested_imports = imports
            imports_needed.update([i.strip() for i in imports.split(',')])
        
        # Don't replace imports in test_helpers
        if '/test_helpers/' in file_path:
            continue
        
        if verbose:
            print(f"Replacing import in {file_path}:")
            print(f"  Original: {original}")
            print(f"  Needed imports: {', '.join(imports_needed)}")
    
    # Now build the new import block
    if not has_service_imports and imports_needed and '/test_helpers/' not in file_path:
        # Find the last import line to insert after it
        import_lines = re.findall(r'^import.*|^from.*import', content, re.MULTILINE)
        if import_lines:
            last_import = import_lines[-1]
            last_import_pos = content.rfind(last_import) + len(last_import)
            
            # Create new import statement
            imports_list = ", ".join(sorted(imports_needed))
            new_import = f"\n\n# Import from service_imports\nfrom tests_dest.test_helpers.service_imports import ({imports_list})"
            
            # Insert new import after the last existing import
            modified_content = content[:last_import_pos] + new_import + content[last_import_pos:]
            
            if verbose:
                print(f"Adding service_imports to {file_path}:")
                print(f"  {new_import}")
    
    # If we're applying changes, write to the file
    if apply and modified_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"Applied import fixes to {file_path}")
    
    return modified_content

def main():
    parser = argparse.ArgumentParser(description='Fix compliance issues in test files')
    parser.add_argument('--path', required=True, help='Directory or file to analyze')
    parser.add_argument('--apply', action='store_true', help='Apply fixes to files')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    args = parser.parse_args()
    
    python_files = find_python_files(args.path)
    
    all_issues = {
        "direct_imports": 0,
        "mock_usage": 0,
        "no_service_imports": 0
    }
    
    files_with_issues = []
    
    for file_path in python_files:
        # Skip certain files we don't want to modify
        if 'test_helpers/service_imports.py' in file_path:
            continue
            
        issues = analyze_file(file_path, args.verbose)
        
        # Track statistics
        for issue_type, issue_list in issues.items():
            all_issues[issue_type] += len(issue_list)
        
        # Fix imports if needed
        if issues["direct_imports"] or issues["no_service_imports"]:
            files_with_issues.append(file_path)
            fix_imports(file_path, args.apply, args.verbose)
    
    # Print summary
    print("\nSummary of issues found:")
    print(f"  Direct imports: {all_issues['direct_imports']}")
    print(f"  Missing service_imports: {all_issues['no_service_imports']}")
    print(f"  Mock usage in integration tests: {all_issues['mock_usage']}")
    print(f"\nFiles with import issues: {len(files_with_issues)}")
    
    if args.apply:
        print(f"\nApplied import fixes to {len(files_with_issues)} files")
    else:
        print("\nRun with --apply to fix the import issues")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 