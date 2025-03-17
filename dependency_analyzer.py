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

def extract_imports(file_path):
    """Extract import statements from a Python file."""
    imports = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # Find all import statements
    import_regex = re.compile(r'^(?:from\s+([.\w]+)\s+import|import\s+([.\w,\s]+))', re.MULTILINE)
    matches = import_regex.findall(content)
    
    for match in matches:
        from_import, direct_import = match
        if from_import:
            # from X import Y
            # Split on dots to get the base module
            module = from_import.split('.')[0]
            imports.append(module)
        elif direct_import:
            # import X, Y, Z
            modules = [m.strip() for m in direct_import.split(',')]
            for module in modules:
                # Split on dots to get the base module
                base_module = module.split('.')[0]
                imports.append(base_module)
    
    return imports

def is_python_file(path):
    """Check if a file is a Python file."""
    return path.suffix == '.py'

def build_dependency_graph(root_dir):
    """Build a dependency graph from Python files in the directory."""
    graph = defaultdict(set)
    modules_to_files = {}
    
    # Find all Python files
    for path in Path(root_dir).rglob('*.py'):
        # Get relative path
        rel_path = path.relative_to(root_dir)
        # Convert path to module name
        parts = list(rel_path.parts)
        
        # Handle __init__.py files
        if parts[-1] == '__init__.py':
            parts.pop()
        else:
            # Remove .py extension
            parts[-1] = parts[-1][:-3]
            
        module_name = '.'.join(parts) if parts else rel_path.stem
        
        # Store mapping from module to file
        modules_to_files[module_name] = str(path)
        
        # Extract imports
        imports = extract_imports(path)
        for imp in imports:
            graph[module_name].add(imp)
    
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
            if neighbor in graph:  # Only follow edges to known nodes
                dfs(neighbor)
                
        path.pop()
    
    for node in graph:
        dfs(node)
        
    return cycles

def analyze_dependencies(root_dir):
    """Analyze dependencies in the code base."""
    print(f"Analyzing dependencies in {root_dir}...")
    graph, modules_to_files = build_dependency_graph(root_dir)
    
    # Find cycles
    cycles = find_cycles(graph)
    
    if cycles:
        print(f"Found {len(cycles)} potential circular dependencies:")
        for i, cycle in enumerate(cycles, 1):
            print(f"Cycle {i}: {' -> '.join(cycle)}")
            print("Files involved:")
            for module in cycle:
                if module in modules_to_files:
                    print(f"  - {module}: {modules_to_files[module]}")
            print()
    else:
        print("No circular dependencies found.")
    
    # Print all dependencies for reference
    print("\nDependency Graph:")
    for module, imports in sorted(graph.items()):
        if imports:
            print(f"{module} imports: {', '.join(sorted(imports))}")
    
    return cycles

if __name__ == "__main__":
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "."
    
    analyze_dependencies(root_dir) 