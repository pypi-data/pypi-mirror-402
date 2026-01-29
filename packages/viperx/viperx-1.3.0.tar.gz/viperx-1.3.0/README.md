# 🐍 ViperX

> **Professional Python Project Initializer**
> *The modern, snake-fast way to bootstrap Python projects.*

**ViperX** is a CLI tool designed to generate production-ready Python projects instantly. It leverages **[uv](https://github.com/astral-sh/uv)** for blazing fast dependency management and offers specialized templates for **Machine Learning** (`ml`) and **Deep Learning** (`dl`).

## ✨ Features

- **Blazing Fast**: Built on top of `uv`.
- **Pre-configured**: `pyproject.toml`, proper `src` layout, `ruff` ready.
- **ML/DL First**: Templates with `torch`, `tensorflow`, `kagglehub` and **Smart Caching**.
- **Smart Caching**: Auto-downloads and caches datasets to `~/.cache/viperx/data` (or local `data/`).
- **Strict Isolation**: Environment variables (`.env`) isolated in `src/<pkg>/` for better security.
- **Config-in-Package**: Solves the "Colab/Kaggle doesn't see my config" problem.
- **Platform Agnostic**: Works on Local, VSCode, Colab, and Kaggle.
- **Safe Mode**: Never overwrites or deletes files automatically—reports changes for manual action.

## 📦 Installation

**Recommended (Global Tool)**
```bash
pipx install viperx
```

**Alternative (uv)**
```bash
uv tool install viperx
```

## 🚀 Quick Start

```bash
# Classic Package
viperx config -n my-lib

# Machine Learning Project
viperx config -n churn-prediction -t ml --env

# Deep Learning Project (PyTorch)
viperx config -n deep-vision -t dl -f pytorch

# Declarative Config (Infrastructure as Code)
viperx config get                   # Generate template
viperx config -c viperx.yaml        # Apply config
```

## 🧱 Project Structure

### Standard Layout
```text
my-lib/
├── pyproject.toml      # Managed by uv
├── README.md
├── .gitignore
├── viperx.yaml         # Config file
└── src/
    └── my_lib/
        ├── __init__.py
        ├── main.py         # Entry point
        ├── config.yaml     # Data URLs & Params
        ├── config.py       # Loader
        ├── .env            # Secrets (ISOLATED)
        └── tests/
            └── test_core.py
```

### ML/DL Layout
```text
deep-vision/
├── pyproject.toml
├── notebooks/
│   ├── Base_Kaggle.ipynb
│   └── Base_General.ipynb
├── data/               # Cached datasets
└── src/
    └── deep_vision/
        ├── main.py
        ├── config.py       # <--- ISOLATED
        ├── .env            # <--- ISOLATED
        ├── data_loader.py  # Smart caching
        └── tests/
```

## 💻 CLI Reference

### `config` - Main Command

```bash
viperx config [OPTIONS]
```

**Options:**
| Flag                | Description                       | Default    |
| ------------------- | --------------------------------- | ---------- |
| `-n, --name`        | Project name **(Required)**       | -          |
| `-t, --type`        | `classic`, `ml`, `dl`             | `classic`  |
| `-d, --description` | Project description               | -          |
| `-a, --author`      | Author name                       | git user   |
| `-l, --license`     | `MIT`, `Apache-2.0`, `GPLv3`      | `MIT`      |
| `-b, --builder`     | `uv`, `hatch`                     | `uv`       |
| `-f, --framework`   | `pytorch`, `tensorflow` (DL only) | `pytorch`  |
| `--env / --no-env`  | Generate `.env` file              | `--no-env` |
| `-c, --config`      | Path to `viperx.yaml`             | -          |

### `config get` - Generate Template

```bash
viperx config get
```

Creates a `viperx.yaml` template in current directory.

### `package` - Workspace Management

```bash
# Add package
viperx package add -n worker-api -t classic

# Delete package
viperx package delete -n worker-api

# Update dependencies
viperx package update -n worker-api
```

## 📝 Declarative Config (`viperx.yaml`)

```yaml
project:
  name: "my-project"
  description: "A cool project"
  author: "Your Name"
  license: "MIT"
  builder: "uv"

settings:
  type: "classic"          # classic | ml | dl
  use_env: false
  use_config: true
  use_tests: true

workspace:
  packages:
    - name: "api"
      type: "classic"
    - name: "ml-core"
      type: "ml"
      use_env: true
```

## 🔒 Safe Mode Philosophy

ViperX follows a **non-destructive** approach:

| Action        | Behavior                          |
| ------------- | --------------------------------- |
| **Add**       | ✅ Creates new files/packages      |
| **Update**    | ⚠️ Reports changes, user decides   |
| **Delete**    | ❌ Never deletes—warns user        |
| **Overwrite** | ❌ Never overwrites existing files |

## 🧪 Test Coverage

```bash
uv run pytest src/viperx/tests
# 34 tests | 77% coverage
```

**Test Structure:**
- `unit/` - Validation (5 tests)
- `functional/` - CLI, licenses, project types (16 tests)
- `scenarios/` - Classic, workspace, updates (11 tests)
- `integration/` - E2E lifecycle (2 tests)

## 🤝 Contributing

```bash
git clone https://github.com/KpihX/viperx.git
cd viperx
uv sync
uv run viperx --help
```

---
*Built with ❤️ by KpihX*
