#!/usr/bin/env python3
"""
Fix syntax errors in Python test files.
This script specifically targets missing parentheses and other common syntax issues.
"""

import os
import re
import logging
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('syntax_fixer')

def fix_file_syntax(file_path):
    """Fix syntax errors in a file, focusing on missing parentheses."""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a simple backup
        backup_path = f"{file_path}.bak"
        shutil.copy2(file_path, backup_path)
        
        # Fix missing parentheses in sys.path.insert
        content = re.sub(r'sys\.path\.insert\(0, str\(parent_dir\)', r'sys.path.insert(0, str(parent_dir))', content)
        
        # Fix missing parentheses in lambda functions with Depends
        content = re.sub(r'Depends\(lambda: MagicMock\(\)', r'Depends(lambda: MagicMock())', content)
        
        # Fix missing closing parentheses in parameter lists
        content = re.sub(r'param_names = list\(sig\.parameters\.keys\(', r'param_names = list(sig.parameters.keys())', content)
        
        # Fix missing closing parentheses in parameter definition functions
        content = re.sub(r'def get_(\w+)_dependency\(\):\s+return Depends\(lambda: MagicMock\(\)', 
                        r'def get_\1_dependency():\n    return Depends(lambda: MagicMock())', content)
        
        # Fix missing closing parentheses in error handling
        content = re.sub(r'monitor_service\.log_error\(error=str\(e\)', r'monitor_service.log_error(error=str(e))', content)
        
        # Fix missing closing parentheses in asyncio.run calls
        content = re.sub(r'asyncio\.run\(([\w_]+)\(AsyncMock\(\)', r'asyncio.run(\1(AsyncMock()))', content)
        
        # General function calls with missing parentheses
        content = re.sub(r'(\w+)\(([\w_]+)\(([^)]*)\)', r'\1(\2(\3))', content)
        
        # Fix controller function definitions with missing closing parentheses
        pattern = r'(async def \w+\([^)]*,\s*\w+ = Depends\(lambda: \w+\(\),)'
        content = re.sub(pattern, r'\1)', content)
        
        # Fix function parameters with missing closing parentheses - more aggressive approach
        content = re.sub(r'(\s*\w+ = Depends\(lambda: \w+\(\),\s*\w+ = Depends\(lambda: \w+\(\):)', 
                        r'\1)', content)
        
        # Another approach: balance all parentheses in each line
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            # Skip multiline strings and comments
            if line.strip().startswith('"""') or line.strip().startswith("'''") or line.strip().startswith('#'):
                fixed_lines.append(line)
                continue
                
            # Count opening and closing parentheses
            open_parens = line.count('(')
            close_parens = line.count(')')
            
            # If there are more opening than closing, add the difference
            if open_parens > close_parens and not line.strip().endswith('\\'):
                line += ')' * (open_parens - close_parens)
                
            fixed_lines.append(line)
            
        content = '\n'.join(fixed_lines)
        
        # Fix from tests-dest to tests_dest
        content = content.replace('from tests-dest', 'from tests_dest')
        content = content.replace('import tests-dest', 'import tests_dest')
        
        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Fixed file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error fixing {file_path}: {e}")
        return False

def fix_all_test_files():
    """Fix all test files in the tests_dest/api directory."""
    api_dir = Path('tests_dest/api')
    fixed_count = 0
    error_count = 0
    
    for file_path in api_dir.glob('**/*.py'):
        try:
            logger.info(f"Fixing {file_path}")
            if fix_file_syntax(file_path):
                fixed_count += 1
            else:
                error_count += 1
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            error_count += 1
    
    logger.info(f"Completed fixing syntax errors in test files")
    logger.info(f"Fixed {fixed_count} files, encountered errors in {error_count} files")

if __name__ == "__main__":
    fix_all_test_files() 