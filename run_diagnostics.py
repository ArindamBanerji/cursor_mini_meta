#!/usr/bin/env python3
"""
Run diagnostics on Python test files to identify syntax errors and other issues.
This script checks for code correctness before making changes.
"""

import os
import sys
import ast
import logging
from pathlib import Path
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('code_diagnostics')

def check_syntax(file_path):
    """Check Python file for syntax errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Try to parse the code with ast
        try:
            ast.parse(source)
            logger.info(f"✓ {file_path}: Syntax is valid")
            return True
        except SyntaxError as e:
            logger.error(f"✗ {file_path}: Syntax error at line {e.lineno}, column {e.offset}: {e.msg}")
            # Extract the problematic line and show context
            lines = source.split('\n')
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            for i in range(start, end):
                prefix = "  "
                if i + 1 == e.lineno:
                    prefix = "→ "
                logger.error(f"{prefix}{i+1}: {lines[i]}")
            return False
    except Exception as e:
        logger.error(f"✗ {file_path}: Error reading file: {str(e)}")
        return False

def check_indentation(file_path):
    """Check for consistent indentation."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check for mixed tabs and spaces
        has_tabs = any('\t' in line for line in lines)
        has_spaces = any(line.startswith(' ') for line in lines)
        
        if has_tabs and has_spaces:
            logger.warning(f"⚠ {file_path}: Mixed tabs and spaces detected")
            return False
        
        logger.info(f"✓ {file_path}: Indentation is consistent")
        return True
    except Exception as e:
        logger.error(f"✗ {file_path}: Error checking indentation: {str(e)}")
        return False

def check_parentheses_balance(file_path):
    """Check for balanced parentheses, brackets, and braces."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Simple stack-based approach to check balanced parentheses
        stack = []
        pairs = {')': '(', ']': '[', '}': '{'}
        line_num = 1
        col_num = 0
        
        for i, char in enumerate(source):
            if char == '\n':
                line_num += 1
                col_num = 0
            else:
                col_num += 1
                
            if char in '([{':
                stack.append((char, line_num, col_num))
            elif char in ')]}':
                if not stack or stack[-1][0] != pairs[char]:
                    logger.error(f"✗ {file_path}: Unbalanced parentheses at line {line_num}, column {col_num}")
                    return False
                stack.pop()
        
        if stack:
            unclosed = [(char, line, col) for char, line, col in stack]
            logger.error(f"✗ {file_path}: Unclosed parentheses: {unclosed}")
            return False
            
        logger.info(f"✓ {file_path}: Parentheses are balanced")
        return True
    except Exception as e:
        logger.error(f"✗ {file_path}: Error checking parentheses: {str(e)}")
        return False

def check_missing_colons(file_path):
    """Check for missing colons in function definitions and control structures."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        issues = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            # Check for lines that should have colons but don't
            if re.match(r'^(def|class|if|elif|else|for|while|try|except|finally|with)\s+.*[^:]\s*$', line):
                issues.append((i+1, line))
        
        if issues:
            for line_num, content in issues:
                logger.error(f"✗ {file_path}: Missing colon at line {line_num}: {content}")
            return False
            
        logger.info(f"✓ {file_path}: No missing colons detected")
        return True
    except Exception as e:
        logger.error(f"✗ {file_path}: Error checking for missing colons: {str(e)}")
        return False

def check_import_issues(file_path):
    """Check for common import issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        issues = []
        import_lines = []
        
        for i, line in enumerate(lines):
            if re.match(r'^\s*(import|from)\s+', line.strip()):
                import_lines.append((i+1, line.strip()))
        
        # Check for imports with dashes
        for line_num, content in import_lines:
            if 'tests-dest' in content:
                issues.append((line_num, f"Invalid import with dash: {content}"))
        
        if issues:
            for line_num, msg in issues:
                logger.error(f"✗ {file_path}: Line {line_num}: {msg}")
            return False
            
        logger.info(f"✓ {file_path}: No import issues detected")
        return True
    except Exception as e:
        logger.error(f"✗ {file_path}: Error checking imports: {str(e)}")
        return False

def run_diagnostics(file_path):
    """Run all diagnostic checks on a file."""
    logger.info(f"Running diagnostics on {file_path}")
    
    syntax_ok = check_syntax(file_path)
    if not syntax_ok:
        # If syntax is invalid, don't bother checking other aspects
        return False
    
    indentation_ok = check_indentation(file_path)
    parentheses_ok = check_parentheses_balance(file_path)
    colons_ok = check_missing_colons(file_path)
    imports_ok = check_import_issues(file_path)
    
    all_ok = syntax_ok and indentation_ok and parentheses_ok and colons_ok and imports_ok
    
    if all_ok:
        logger.info(f"✓ {file_path}: All checks passed")
    else:
        logger.error(f"✗ {file_path}: Some checks failed")
    
    return all_ok

def fix_missing_parentheses(file_path):
    """Fix missing parentheses in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix specific issues
        # Fix unclosed parentheses in sys.path.insert
        content = content.replace("sys.path.insert(0, str(parent_dir)", "sys.path.insert(0, str(parent_dir))")
        
        # Fix unclosed parentheses in MagicMock
        content = content.replace("Depends(lambda: MagicMock()", "Depends(lambda: MagicMock())")
        
        # Fix missing parentheses in signature.parameters.keys()
        content = content.replace("sig.parameters.keys(", "sig.parameters.keys()")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Fixed missing parentheses in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing parentheses in {file_path}: {str(e)}")
        return False

def fix_logging_config(file_path):
    """Fix logging configuration issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Fix logging.basicConfig() syntax error
            if "logging.basicConfig()" in line and i+2 < len(lines):
                # Check if the next lines contain logging config params
                if "level=" in lines[i+1] and "format=" in lines[i+2]:
                    fixed_lines.append("logging.basicConfig(\n")
                    fixed_lines.append(lines[i+1])
                    fixed_lines.append(lines[i+2])
                    fixed_lines.append(")\n")
                    i += 3
                    continue
            
            fixed_lines.append(line)
            i += 1
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
            
        logger.info(f"Fixed logging configuration in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing logging in {file_path}: {str(e)}")
        return False

def fix_function_def_syntax(file_path):
    """Fix function definition syntax issues."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix async def function() -> async def function():
        content = re.sub(r'async def (\w+)\(\)\s+', r'async def \1(', content)
        
        # Add missing colons in function definitions
        content = re.sub(r'(async def \w+\([^)]*\))\s*$', r'\1:', content)
        content = re.sub(r'(def \w+\([^)]*\))\s*$', r'\1:', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Fixed function definition syntax in {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing function syntax in {file_path}: {str(e)}")
        return False

def fix_all_files():
    """Run diagnostics and fix issues in all test files."""
    # Get all test files in the API directory
    api_dir = Path("tests_dest/api")
    if not api_dir.exists():
        logger.error(f"Directory not found: {api_dir}")
        return
    
    files = list(api_dir.glob("**/*.py"))
    logger.info(f"Found {len(files)} Python files to check")
    
    issues_found = 0
    files_fixed = 0
    
    for file_path in files:
        # First run diagnostics
        logger.info(f"Diagnosing {file_path}")
        if not run_diagnostics(file_path):
            issues_found += 1
            
            # Apply fixes
            logger.info(f"Applying fixes to {file_path}")
            fixed_parentheses = fix_missing_parentheses(file_path)
            fixed_logging = fix_logging_config(file_path)
            fixed_functions = fix_function_def_syntax(file_path)
            
            if fixed_parentheses or fixed_logging or fixed_functions:
                files_fixed += 1
                
                # Check if fixes resolved the issues
                logger.info(f"Re-checking {file_path} after fixes")
                if run_diagnostics(file_path):
                    logger.info(f"✓ {file_path}: Successfully fixed")
                else:
                    logger.warning(f"⚠ {file_path}: Issues remain after fixes")
    
    logger.info(f"Diagnostics complete: {issues_found} files had issues, {files_fixed} files were fixed")

if __name__ == "__main__":
    import re  # Import here to avoid issues if checking this file itself
    
    # Check specific file(s) if provided as arguments
    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            if os.path.exists(file_path):
                run_diagnostics(Path(file_path))
            else:
                logger.error(f"File not found: {file_path}")
    else:
        # Check all files
        fix_all_files() 