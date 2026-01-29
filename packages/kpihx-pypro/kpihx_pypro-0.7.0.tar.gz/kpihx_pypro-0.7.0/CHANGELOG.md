# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-01-19 (V7 Advanced Data Loading)

### Added
- **Data Infrastructure**: `data/` directory layout for ML/DL projects (git-ignored).
- **Generic Data Loader**: `data_loader.py` utility for caching & loading CSVs from URLs.
- **Dual Notebooks**:
    - `Base_Kaggle.ipynb`: For KaggleHub workflows.
    - `Base_General.ipynb`: For generic URL/Local workflows.
- **Dependencies**: Added `requests` and `tqdm` to ML/DL templates.

## [0.6.0] - 2026-01-19 (V6 Strict Isolation)

### Added
- **Strict Env Isolation**: `.env` and `.env.example` are now generated inside `src/<package_name>/`, never at the root.
- **Config Loader**: `config.py` now supports automatic loading of the isolated `.env` file via `python-dotenv`.
- **Granular Control**: New `--readme / --no-readme` option for `package add` to skip generating local documentation.

## [0.5.0] - 2026-01-19 (V5 DL Frameworks)

### Added
- **Deep Learning Framework Selection**: New `--framework / -f` option for `init` and `package add`.
- **PyTorch Support**: Default for `dl` projects (includes `torch`, `torchvision`, CUDA checks).
- **TensorFlow Support**: Explicit support via `-f tensorflow` (includes `tensorflow`, GPU checks).
- **Conditional Templates**: `pyproject.toml` and `Base.ipynb` adapt content based on selected framework.

## [0.4.0] - 2026-01-19 (V4 CLI Hierarchy)

### Added
- **`package` Subcommand Group**: New hierarchical CLI structure `pypro package [COMMAND]`.
- **`package delete`**: Command to remove a package directory and its entry from the workspace members list.
- **`package update`**: Command to update dependencies (`uv lock --upgrade`) for a specific package.

### Changed
- **CLI Refactor**: Moved `add-package` to `package add` for better organization.
- **Core Logic**: Updated workspace management to handle package deletion and updates robustly.

## [0.3.0] - 2026-01-19 (V3 Features)

### Added
- **Multi-Package Support**: New `add-package` command to seamlessly upgrade projects to use `uv` workspaces.
- **Verbose Mode**: Global `-v / --verbose` flag using standard logging for transparency.
- **License Generation**: Added `--license` option supporting MIT, Apache-2.0, and GPLv3 with template rendering.
- **Glass Box Documentation**: Generated READMEs now explain the "why" and "how" of the project infrastructure (`uv`, `config.yaml`).

### Changed
- Refactored `main.py` to correctly handle global flags via callback.
- Updated `core.py` to use robust constant defaults `DEFAULT_LICENSE` and `DEFAULT_BUILDER`.

## [0.2.0] - 2026-01-19 (V2 Refinement)

### Added
- **Deep Learning Template**: Dedicated DL setup with GPU-ready libraries (Torch) and KaggleHub integration.
- **Transparency**: Added `Base.ipynb` showing explicit config loading.

### Changed
- **Scaffolding Engine**: Switched to `uv init --package` as the core generation mechanism for 100% standard compliance.
- **Build System**: Enforced `hatchling` backend in `pyproject.toml` to ensure `config.yaml` is packaged correctly in wheels.
- **Structure**: Moved tests to `src/<package>/tests/` for better self-containment.
- **Config**: Implemented "Config-in-Package" pattern using `importlib.resources`.

## [0.1.0] - Initial Release

### Added
- Basic "Classic" project structure generation.
- Initial integration with `uv`.
