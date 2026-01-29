# 🗺️ PyPro Roadmap

This document tracks the evolution of `pypro`.
**Workflow:** Check items in "To Do". When completed, move them to the "Done" history below.

## 🚀 To Do

- [ ] **Docker Support** 🐳
    - [ ] Generate optimized `Dockerfile` based on project type (Slim for Classic, CUDA-ready for DL).
    - [ ] Generate `docker-compose.yaml` (optional/flag).
    - [ ] Ensure `uv` is used inside Docker for fast installs.

## ✅ Done

- [x] **V3.1: Multi-Package & Polish**
    - [x] Global `-v`/`--verbose` flag for transparent logging.
    - [x] Command `add-package` to manage Workspaces.
    - [x] Automatic Workspace upgrade logic.
    - [x] `LICENSE` generation (MIT, Apache 2.0, GPLv3).
    - [x] "Glass Box" `README.md` templates.

- [x] **V2: Core Refinement**
    - [x] Native `uv init --package` integration.
    - [x] Dynamic system Python version detection.
    - [x] Config-in-Package architecture verification.
    - [x] ML/DL Templates with `kagglehub` integration.
