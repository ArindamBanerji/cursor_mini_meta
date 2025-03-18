#!/usr/bin/env python
"""
dependency_analyzer.py - Analyzes Python files for potential circular imports

This script scans all Python files in a directory structure and identifies
potential circular import dependencies by building an import graph.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict
import importlib.util
import argparse

# Standard library modules to exclude from the analysis
STDLIB_MODULES = set(sys.builtin_module_names)
try:
    # Try to get a more complete list from stdlib_list
    from stdlib_list import stdlib_list
    STDLIB_MODULES.update(stdlib_list("3.9"))  # Use Python 3.9 as reference
except ImportError:
    # Fallback to a minimal list if stdlib_list is not available
    STDLIB_MODULES.update([
        "os", "sys", "re", "math", "time", "datetime", "json", "csv", 
        "random", "collections", "itertools", "functools", "pathlib", 
        "typing", "enum", "logging", "unittest", "argparse"
    ])

def extract_imports(file_path):
    """
    Extract import statements from a Python file.
    
    Returns:
        tuple: (direct_imports, from_imports, conditional_imports)
            - direct_imports: set of modules imported directly (import X)
            - from_imports: set of modules imported from (from X import Y)
            - conditional_imports: set of modules imported conditionally (inside try/except)
    """
    direct_imports = set()
    from_imports = set()
    conditional_imports = set()
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find all try/except blocks that might contain imports
    try_blocks = re.findall(r'try\s*:(.*?)except', content, re.DOTALL)
    for block in try_blocks:
        # Extract imports from try blocks
        try_imports = re.findall(r'(?:from\s+([.\w]+)\s+import|import\s+([.\w,\s]+))', block)
        for from_imp, direct_imp in try_imports:
            if from_imp:
                conditional_imports.add(from_imp)
            if direct_imp:
                for module in [m.strip() for m in direct_imp.split(',')]:
                    conditional_imports.add(module)
    
    # Remove try blocks to avoid double counting
    for block in try_blocks:
        content = content.replace(block, '')
    
    # Find direct imports: import X, import X.Y, import X as Y
    direct_import_regex = re.compile(r'^import\s+([\w\s,.]+)', re.MULTILINE)
    for imports_str in direct_import_regex.findall(content):
        for module_str in imports_str.split(','):
            module = module_str.strip().split(' as ')[0].strip()
            direct_imports.add(module)
    
    # Find from imports: from X import Y, from X.Y import Z
    from_import_regex = re.compile(r'^from\s+([\w.]+)\s+import', re.MULTILINE)
    for module in from_import_regex.findall(content):
        from_imports.add(module)
    
    return direct_imports, from_imports, conditional_imports

def is_python_file(path):
    """Check if a file is a Python file."""
    return path.suffix == '.py'

def module_path_to_name(path, root_dir):
    """Convert file path to module name."""
    rel_path = path.relative_to(root_dir)
    parts = list(rel_path.parts)
    
    # Handle __init__.py files
    if parts[-1] == '__init__.py':
        parts.pop()
    else:
        # Remove .py extension
        parts[-1] = parts[-1][:-3]
    
    module_name = '.'.join(parts)
    return module_name

def resolve_relative_import(base_module, relative_import):
    """Resolve a relative import to its absolute form."""
    if not relative_import.startswith('.'):
        return relative_import
    
    # Count the number of dots for relative import level
    level = 0
    for char in relative_import:
        if char == '.':
            level += 1
        else:
            break
    
    # Split the base module
    base_parts = base_module.split('.')
    
    # Remove parts based on the level
    if level > len(base_parts):
        print(f"Warning: Invalid relative import '{relative_import}' from '{base_module}'")
        return None
    
    new_base = '.'.join(base_parts[:-level] if level > 0 else base_parts)
    
    # Add the relative module if it exists
    relative_module = relative_import[level:]
    if relative_module:
        return f"{new_base}.{relative_module}" if new_base else relative_module
    else:
        return new_base

def is_local_module(module_name, known_modules):
    """Check if a module is local to the project."""
    # Check if it's a standard library module
    if module_name in STDLIB_MODULES:
        return False
    
    # Check if it's a known module in our project
    module_parts = module_name.split('.')
    base_module = module_parts[0]
    
    for known_module in known_modules:
        known_parts = known_module.split('.')
        if base_module == known_parts[0]:
            return True
    
    return False

def build_dependency_graph(root_dir):
    """Build a dependency graph from Python files in the directory."""
    graph = defaultdict(set)
    modules_to_files = {}
    all_modules = set()
    
    # First pass: Find all Python modules
    for path in Path(root_dir).rglob('*.py'):
        if path.is_file():
            module_name = module_path_to_name(path, root_dir)
            modules_to_files[module_name] = str(path)
            all_modules.add(module_name)
    
    # Second pass: Extract imports and build the graph
    for module_name, file_path in modules_to_files.items():
        direct_imports, from_imports, conditional_imports = extract_imports(file_path)
        
        # Process all types of imports
        for imports in [direct_imports, from_imports]:
            for imp in imports:
                # Skip standard library imports
                if imp in STDLIB_MODULES:
                    continue
                
                # Handle relative imports
                if imp.startswith('.'):
                    resolved_imp = resolve_relative_import(module_name, imp)
                    if resolved_imp and is_local_module(resolved_imp, all_modules):
                        graph[module_name].add(resolved_imp)
                # Handle absolute imports
                elif is_local_module(imp, all_modules):
                    graph[module_name].add(imp)
        
        # Add conditional imports separately
        for imp in conditional_imports:
            if imp not in STDLIB_MODULES:
                if imp.startswith('.'):
                    resolved_imp = resolve_relative_import(module_name, imp)
                    if resolved_imp and is_local_module(resolved_imp, all_modules):
                        # Mark as conditional with a tuple
                        graph[module_name].add((resolved_imp, True))
                elif is_local_module(imp, all_modules):
                    # Mark as conditional with a tuple
                    graph[module_name].add((imp, True))
    
    return graph, modules_to_files

def find_cycles(graph):
    """Find cycles in the dependency graph using DFS."""
    visited = set()
    path = []
    cycles = []
    
    def dfs(node):
        if node in path:
            # Found a cycle
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        
        if node in visited:
            return
            
        visited.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            # Handle conditional imports (tuples)
            if isinstance(neighbor, tuple):
                neighbor_name, is_conditional = neighbor
                # Skip conditional imports in cycle detection as they might not
                # always be imported
                continue
            
            if neighbor in graph:  # Only follow edges to known nodes
                dfs(neighbor)
                
        path.pop()
    
    for node in graph:
        if node not in visited:
            dfs(node)
        
    return cycles

def analyze_dependencies(root_dir, verbose=False):
    """
    Analyze dependencies in the code base.
    
    Args:
        root_dir: Root directory to analyze
        verbose: Whether to print the full dependency graph
    """
    print(f"Analyzing dependencies in {root_dir}...")
    graph, modules_to_files = build_dependency_graph(root_dir)
    
    # Find cycles
    cycles = find_cycles(graph)
    
    if cycles:
        print(f"Found {len(cycles)} potential circular dependencies:")
        for i, cycle in enumerate(cycles, 1):
            print(f"\nCycle {i}: {' -> '.join(cycle)}")
            print("Files involved:")
            for module in cycle:
                if module in modules_to_files:
                    print(f"  - {module}: {modules_to_files[module]}")
            
            # Suggest possible solutions
            print("\nPossible solutions:")
            print("  1. Use conditional imports (inside try/except blocks)")
            print("  2. Move common functionality to a separate module")
            print("  3. Use dependency injection patterns")
            print("  4. Refactor to use abstract base classes or interfaces")
    else:
        print("No circular dependencies found.")
    
    # Print all dependencies if requested
    if verbose:
        print("\nDependency Graph:")
        for module, imports in sorted(graph.items()):
            if imports:
                # Format imports, handling conditional imports (tuples)
                formatted_imports = []
                for imp in sorted(imports, key=lambda x: x[0] if isinstance(x, tuple) else x):
                    if isinstance(imp, tuple):
                        imp_name, is_conditional = imp
                        formatted_imports.append(f"{imp_name} (conditional)")
                    else:
                        formatted_imports.append(imp)
                
                print(f"{module} imports: {', '.join(formatted_imports)}")
    
    return cycles

def main():
    parser = argparse.ArgumentParser(description="Analyze Python code for circular dependencies")
    parser.add_argument("root_dir", nargs="?", default=".", help="Root directory to analyze")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print full dependency graph")
    parser.add_argument("--focus", help="Focus analysis on specific module or directory")
    
    args = parser.parse_args()
    
    analyze_dependencies(args.root_dir, verbose=args.verbose)

if __name__ == "__main__":
    main() 