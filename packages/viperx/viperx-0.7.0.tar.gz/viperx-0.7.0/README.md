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

## 📦 Installation

**Recommended (Global Tool)**
```bash
pipx install viperx
```

**Alternative (uv)**
```bash
uv tool install viperx
```

## 🚀 Usage

### `init`
Initialize a new project (Classic, ML, or DL).

```bash
# Classic Lib (Standard Layout)
viperx init -n my-lib

# Machine Learning ( + Notebooks, Pandas, Scikit-learn, Smart Loader)
viperx init -n churn-pred -t ml

# Deep Learning ( + PyTorch/TensorFlow, CUDA checks)
viperx init -n deep-vision -t dl --framework pytorch
```

### `package`
Manage workspace packages (Monorepo style).

```bash
# Add a new package to the current workspace
viperx package add -n my-api -t classic

# Remove a package
viperx package delete -n my-api
```

## 🚀 Quick Start

Initialize a new project with a single command:

```bash
# Classic Package
pypro init -n my-lib -d "My awesome library"

# Deep Learning Project (PyTorch ready)
pypro init -n deep-vision -t dl --description "Vision Transformer implementation"

# Machine Learning Project (Scikit-learn ready)
pypro init -n churn-prediction -t ml
```

## 🏗️ Project### 🧱 Structure

<img src="https://raw.githubusercontent.com/vscode-icons/vscode-icons/master/icons/folder-src.svg" width="16" /> **Standard Layout**
```text
my-lib/
├── pyproject.toml      # Managed by uv
├── README.md
├── .gitignore
├── data/               # Local datasets (ignored by git)
└── src/
    └── my_lib/
        ├── __init__.py
        ├── main.py     # Entry point
        ├── config.yaml # Data URLs & Params
        ├── config.py   # Loader
        ├── .env        # Secrets (Isolated)
        └── utils/
            └── data_loader.py # Generic URL/CSV Loader
```

### 🧠 Machine Learning & Deep Learning
For type `ml` or `dl`, you get:
- **Notebooks**:
  - `Base_Kaggle.ipynb`: Loads data via `kagglehub`.
  - `Base_General.ipynb`: Loads data via `data_loader.py` (URL/Local).
- **Data Loader**: `src/<pkg>/data_loader.py` handles caching downloads to `data/`.
- **Config**: Pre-filled with "Hello World" datasets (Iris, Titanic).

### ⚙️ Configurationstalls dependencies (`torch`, `pandas`...).

```text
deep-vision/
├── pyproject.toml
├── notebooks/
│   └── Base.ipynb      # Pre-configured notebook (Colab/Kaggle ready)
└── src/
    └── deep_vision/
        ├── ...         # Same robust package structure
```

## 💻 CLI Usage

### `init` - Create a new project

```bash
uv run pypro init [OPTIONS]
```

**Options:**
- `-n, --name TEXT`: Project name **(Required)**.
- `-t, --type TEXT`: Project type (`classic`, `ml`, `dl`). Default: `classic`.
- `-d, --description TEXT`: Project description.
- `-a, --author TEXT`: Author name (defaults to git user).
- `-l, --license TEXT`: License type (`MIT`, `Apache-2.0`, `GPLv3`). Default: `MIT`.
- `-f, --framework TEXT`: DL Framework (`pytorch`, `tensorflow`). Default: `pytorch` (only for `-t dl`).
- `-v, --verbose`: Enable verbose logging for transparent output.

**Examples:**

```bash
# Classic Library
uv run pypro init -n my-lib

# Deep Learning (PyTorch Default)
uv run pypro init -n vision-ai -t dl

# Deep Learning (TensorFlow)
uv run pypro init -n tf-legacy -t dl -f tensorflow
```

### `package` - Manage Workspace

Manage packages in your workspace hierarchy (add, update, delete).

#### `add`
Add a new package to your project. Upgrades standalone projects to workspaces automatically.
```bash
uv run pypro package add -n worker-node -t classic --no-readme
```
**Options:**
- `--readme / --no-readme`: Generate a local `README.md` for the package. Default: `True`.
- `--env / --no-env`: Generate isolated `.env` and `.env.example` in `src/<pkg>/`.

#### `delete`
Remove a package from the workspace (deletes folder & updates `pyproject.toml`).
```bash
uv run pypro package delete -n worker-node
```

#### `update`
Update a package's dependencies (runs `uv lock --upgrade`).
```bash
uv run pypro package update -n worker-node
```

---## 📦 "Magical" Configuration

Every project comes with a robust `config.py` using `importlib.resources`.

**In your code / notebooks:**
```python
from my_package import SETTINGS, get_dataset_path

# Works everywhere: Local, Installed, Colab, Kaggle
print(SETTINGS['project_name'])
```

## 🤝 Contributing

This project is built 100% with `uv`.

1. Clone the repo
2. Sync dependencies: `uv sync`
3. Run the CLI: `uv run pypro`

---
*Built with ❤️ by KpihX*
