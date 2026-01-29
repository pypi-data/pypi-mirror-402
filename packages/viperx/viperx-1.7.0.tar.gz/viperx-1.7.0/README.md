# 🐍 ViperX

> **The Mentor-Based Project Initializer**
> *Stop memorizing boilerplate. Start learning best practices.*

**ViperX** is more than a CLI—it's an **automated mentor**. It generates production-ready Python projects (Classic, ML, DL) using **[uv](https://github.com/astral-sh/uv)**, but crucially, it creates **ultra-commented code** that teaches you *why* the structure is built that way.

## 🦅 Philosophy: "Freedom & Grip"
1.  **Grip (Mentorship)**: We hold your hand at the start with strict, educational defaults.
2.  **Freedom (No Lock-in)**: Use `viperx eject` to remove the tool entirely. Your code remains standard Python.
3.  **Conscious Mastery**: We aim to make you autonomous, not dependent.

## 🎓 Educational Features

### 1. The Knowledge Base (`viperx learn`)
Don't leave the terminal to read generic tutorials. ViperX includes a curated knowledge base about modern Python tooling.

```bash
viperx learn uv          # Why uv is the future of packaging
viperx learn structure   # Why we use the src/ layout
viperx learn packaging   # Understanding pyproject.toml
```

### 2. Explain Mode (`--explain` or Persistent)
Pass the global `--explain` flag to any command to get a real-time architectural breakdown.
**Or make it permanent:**

```bash
viperx explain --activate    # I want a mentor for everything
viperx explain --deactivate  # I know what I'm doing now
```

When active, every command explains itself:

```bash
$ viperx config -n my-lib --explain

╭─ 🎓 Explain: Project Structure Strategy ────────────────────────╮
│ We are about to create my-lib.                                  │
│ - Layout: src/ layout (Standard)                                │
│ - Why?: Placing code in src/ prevents "import side effects".    │
│   It forces you to install the package to test it.              │
│ - Tool: We use uv init because it sets up a modern              │
│   pyproject.toml automatically.                                 │
╰─────────────────────────────────────────────────────────────────╯
```

## ✨ Features

- **Education First**: Generated files are learning materials. `viperx --explain` tells you the "why".
- **Blazing Fast**: Built on top of `uv` for sub-second setup.
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

### `learn` - Educational Hub
```bash
viperx learn         # List topics
viperx learn uv      # Learn about uv
```

### Global Options
- `--explain`: Enable detailed architectural explanations during execution.
- `--version`: Show version.

### `config get` - Generate Template

```bash
viperx config get
```

Creates a `viperx.yaml` template in current directory.

### `config update` - Rebuild from Codebase

```bash
viperx config update
```

Scans the existing project and updates `viperx.yaml` to match reality:
- Detects packages in `src/`
- Detects `use_config`, `use_env`, `use_tests` from actual files
- Adds annotations for any mismatches

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
# 46 tests | 76% coverage
```

**Test Structure:**
- `unit/` - Validation (5 tests)
- `functional/` - CLI, licenses, project types, updates (18 tests)
- `scenarios/` - Classic, workspace, type blocking, config scanner (18 tests)
- `integration/` - E2E lifecycle (5 tests)

## 🤝 Contributing

```bash
git clone https://github.com/KpihX/viperx.git
cd viperx
uv sync
uv run viperx --help
```

---
*Built with ❤️ by KpihX*
