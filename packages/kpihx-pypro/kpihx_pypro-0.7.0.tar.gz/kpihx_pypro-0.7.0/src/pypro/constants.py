from pathlib import Path

# Project Defaults
DEFAULT_VERSION = "0.1.0"
DEFAULT_PYTHON_VERSION = "3.11"
DEFAULT_LICENSE = "MIT"
DEFAULT_BUILDER = "uv"

# File Names
CONFIG_FILENAME = "config.yaml"
PYPROJECT_FILENAME = "pyproject.toml"
README_FILENAME = "README.md"
INIT_FILENAME = "__init__.py"
MAIN_FILENAME = "main.py"

# Directory Names
SRC_DIR = "src"
NOTEBOOKS_DIR = "notebooks"
TESTS_DIR = "tests"

# Templates
TEMPLATE_DIR_NAME = "templates"

# Types
TYPE_CLASSIC = "classic"
TYPE_ML = "ml"
TYPE_DL = "dl"
PROJECT_TYPES = [TYPE_CLASSIC, TYPE_ML, TYPE_DL]

# DL Frameworks
FRAMEWORK_PYTORCH = "pytorch"
FRAMEWORK_TENSORFLOW = "tensorflow"
DL_FRAMEWORKS = [FRAMEWORK_PYTORCH, FRAMEWORK_TENSORFLOW]
