# SAP Test Harness Testing Setup Guide

This guide explains how to set up and run tests for the SAP Test Harness. The testing framework uses a sophisticated path resolution system with environment variables, configuration files, and specialized scripts to ensure robust testing capabilities.

## Overview

The SAP Test Harness testing infrastructure consists of the following components:

1. **Environment Variables** for path resolution
2. **Configuration File** for test structure
3. **Setup Scripts** for initializing the test environment
4. **Code Snippet Injection** for ensuring proper imports
5. **Pytest Configuration** for running tests

## Quick Start

To set up and run the test environment:

```bash
# 1. Run the setup script
python test_setup.py --gen-conftest-dir ./ConfTest

# 2. Run pytest
pytest -xvs tests-dest
```

## Detailed Setup Process

### 1. Environment Variables

The testing framework uses two key environment variables:

- **SAP_HARNESS_HOME**: Points to the root directory of the entire harness (automatically detected based on the location of main.py)
- **SAP_HARNESS_CONFIG**: Full path to the JSON configuration file

These are automatically set by the `test_setup.py` script, but can be manually configured:

```bash
export SAP_HARNESS_HOME=/path/to/harness
export SAP_HARNESS_CONFIG=/path/to/harness/test_structure.json
```

### 2. Configuration File

The `test_structure.json` file defines:

- Project root directory
- Source code directories
- Test directories and subdirectories
- Module mappings for import resolution

Example configuration:
```json
{
  "project_root": "/path/to/project/root",
  "source_dirs": ["services", "models", "controllers", "utils", "api"],
  "test_dirs": ["tests-dest"],
  "test_subdirs": ["api", "unit", "integration", "services", "models", "monitoring"],
  "module_mappings": {
    "tests-dest/models": "model_tests"
  }
}
```

### 3. Setup Scripts

#### test_setup.py

The main setup script performs the following:

1. Automatically detects and sets the SAP_HARNESS_HOME environment variable
2. Generates and sets the SAP_HARNESS_CONFIG environment variable
3. Creates test directory structure
4. Runs GenConfTest to generate conftest.py files
5. (Optional) Adds, removes, or checks code snippets in test files

Usage:
```bash
python test_setup.py [OPTIONS]
```

Options:
- `--gen-conftest-dir PATH`: Directory containing GenConfTest.py (default: current directory)
- `--clean`: Clean test environment before setup
- `--add-snippets`: Add code snippets to test files
- `--remove-snippets`: Remove code snippets from test files
- `--check-snippets`: Check which test files have snippets

**Note**: By default, the script does not add or remove snippets. You must explicitly use the appropriate flag.

#### GenConfTest.py

Generates appropriate conftest.py files for each test directory:

```bash
python GenConfTest.py -source tests-dest -sub-dir-list root,api,unit,integration,services,models,monitoring --overwrite
```

Each directory gets a specialized conftest.py with appropriate fixtures for that test category.

#### SnippetForTests.py

Adds or removes import code to/from test files to ensure proper path resolution:

```bash
# Add snippets
python SnippetForTests.py -source tests-dest -snippet code_snippet_for_test_files.py -option ADD

# Remove snippets
python SnippetForTests.py -source tests-dest -option REMOVE

# Check snippet status
python SnippetForTests.py -source tests-dest -option ADD --check-only
```

### 4. Import System

The testing framework uses a layered import system:

1. **Code Snippets**: Added to each test file, providing initial path setup
2. **test_import_helper.py**: Loaded by the snippet, configures detailed path resolution
3. **conftest.py files**: Provide fixtures and additional import settings
4. **pytest.ini**: Configures pytest behavior

#### Code Snippets

Each test file starts with a code snippet that:
- Locates the project root
- Adds it to `sys.path`
- Imports the test_import_helper
- Sets up environment variables

#### test_import_helper.py

Provides the `setup_test_paths()` function which:
- Loads configuration from SAP_HARNESS_CONFIG
- Adds appropriate paths to `sys.path`
- Handles module mappings to prevent import conflicts
- Sets environment variables if needed

### 5. Required Files

For the test setup to work correctly, the following files must be present:

1. **test_setup.py**: Main setup script
2. **GenConfTest.py**: For generating conftest.py files
3. **genconftest_templates.py**: Templates for conftest.py files
4. **genconftest_utils.py**: Utilities for GenConfTest
5. **code_snippet_for_test_files.py**: Import snippet for test files
6. **test_import_helper.py**: Path resolution helper
7. **SnippetForTests.py**: For adding code snippets to test files

## Troubleshooting

### Path Resolution Issues

If tests cannot import application modules:

1. Check that environment variables are set correctly
   ```bash
   echo $SAP_HARNESS_HOME
   echo $SAP_HARNESS_CONFIG
   ```

2. Verify code snippets are added to test files
   ```bash
   python test_setup.py --check-snippets
   ```

3. If needed, add snippets to test files
   ```bash
   python test_setup.py --add-snippets
   ```

4. Inspect the generated conftest.py files
   ```bash
   find tests-dest -name "conftest.py" -exec cat {} \;
   ```

### GenConfTest Errors

If GenConfTest fails with path errors:

1. Use the `--gen-conftest-dir` option to specify the correct path
   ```bash
   python test_setup.py --gen-conftest-dir ./ConfTest
   ```

2. Check that the structure in test_structure.json matches your actual directory layout

### Invalid Syntax in Test Files

If you encounter syntax errors after adding snippets:

1. Remove the snippets and try again
   ```bash
   python test_setup.py --remove-snippets
   ```

2. Make sure your test files follow Python syntax rules

3. Try adding snippets with backups
   ```bash
   python SnippetForTests.py -source tests-dest -snippet code_snippet_for_test_files.py -option ADD --backup
   ```

### Common Issues

- **Project Root Detection Failure**: If the script cannot find main.py, specify the correct project root by editing test_structure.json directly
- **Snippet File Not Found**: Ensure code_snippet_for_test_files.py exists in one of the expected locations
- **SnippetForTests.py Not Found**: Use the --gen-conftest-dir option to specify the directory containing this script

## Best Practices

1. **Always run test_setup.py first** before running tests
2. Create a clean test environment with `--clean` if you encounter strange errors
3. Only add snippets when needed with the `--add-snippets` flag
4. Check snippet status with `--check-snippets` if tests fail
5. Make sure test files follow proper patterns:
   - Located in a subdirectory of tests-dest
   - Named with test_*.py pattern
   - Properly structured Python code
