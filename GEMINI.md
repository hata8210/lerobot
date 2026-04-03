# GEMINI.md - LeRobot Project Overview

## Project Overview
**LeRobot** is a state-of-the-art robotics library developed by Hugging Face, designed to provide a unified, Python-native interface for real-world robotics in PyTorch. It aims to lower the barrier to entry for robotics research and development by standardizing control, datasets, and models across diverse hardware platforms.

### Key Technologies
- **Core Framework:** PyTorch
- **Data Handling:** Hugging Face `datasets` (LeRobotDataset format using Parquet and MP4/images)
- **Model Architectures:** Diffusion Policy, ACT (Action Chunking Transformer), VQ-BeT, TDMPC, and various VLA (Vision-Language-Action) models.
- **Hardware Integration:** Supports SO-100, LeKiwi, Koch arms, Unitree G1 humanoids, and teleoperation devices like gamepads and phones.
- **Simulation Environments:** Integration with ALOHA, PushT, LIBERO, and MetaWorld.
- **Monitoring & Visualization:** Weights & Biases (wandb), Rerun.io, and OpenCV.

### Architecture
The project is structured to decouple hardware control from policy logic:
- `src/lerobot/robots/`: Hardware-specific implementations.
- `src/lerobot/policies/`: SOTA imitation and reinforcement learning models.
- `src/lerobot/datasets/`: Tools for managing and streaming robotic data.
- `src/lerobot/scripts/`: CLI entry points for training, evaluation, and hardware setup.

---

## Building and Running

### building building and running
本项目运行前提需要激活conda环境，命令如下：
source ~/apps/python/init_conda.profile
conda activate lerobot
若改动examples package以外代码，则需要先去到项目根目录编译项目，编译命令如下：
pip install -e .


### Key CLI Commands
- **Info:** `lerobot-info` - Display library and environment information.
- **Training:**
  ```bash
  lerobot-train --policy=act --dataset.repo_id=lerobot/aloha_mobile_cabinet
  ```
- **Evaluation:**
  ```bash
  lerobot-eval --policy.path=path/to/checkpoint --env.type=aloha
  ```
- **Data Collection/Replay:**
  - `lerobot-record` - Record data from a robot.
  - `lerobot-replay` - Replay recorded data.
- **Hardware Setup:**
  - `lerobot-find-cameras`
  - `lerobot-calibrate`
  - `lerobot-setup-motors`

### Running Tests
Tests are managed via `pytest` and can be run using the provided `Makefile`:
- **Fast Tests:** `pytest tests/`
- **End-to-End Tests:** `make test-end-to-end`
- **Device Specific:** `DEVICE=cuda make test-act-ete-train`

---

## Development Conventions

### Coding Style
- **Linting:** The project uses `ruff` for linting and formatting (configured in `pyproject.toml`).
- **Typing:** Type hints are encouraged, and `mypy` is used for static type checking in specific modules.
- **Standards:** Adheres to Hugging Face's engineering standards (e.g., using `draccus` for configuration management).

### Contribution Guidelines
- Refer to `CONTRIBUTING.md` for detailed instructions.
- All new features or bug fixes must include corresponding tests in the `tests/` directory.
- Check `test_available.py` when adding new models, datasets, or environments.

### Testing Practices
- End-to-end tests are preferred for verifying the full training and evaluation pipeline.
- Hardware-specific tests should use mocks where possible (see `tests/mocks`).
- Use `pytest-timeout` for long-running tests.

---

## Key Files
- `pyproject.toml`: Defines project dependencies, CLI entry points, and tool configurations.
- `Makefile`: Provides shortcuts for common development and testing tasks.
- `src/lerobot/__init__.py`: Central registry for available environments, policies, and datasets.
- `src/lerobot/scripts/`: Implementation of core CLI utilities.
