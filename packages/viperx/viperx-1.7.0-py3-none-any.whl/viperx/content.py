
"""
ViperX Knowledge Base (Rich Markdown Content).
"""

KNOWLEDGE_BASE = {
    "uv": """
# Why uv? 🦀

**uv** is an extremely fast Python package installer and resolver, written in Rust.
It replaces `pip`, `pip-tools`, `poetry`, and `virtualenv` with a single, ultra-fast tool.

### 🚀 Why ViperX uses it:

1.  **Speed**: It's 10-100x faster than pip/poetry. It uses a global content-addressable cache.
2.  **Determinism**: It generates a universal `uv.lock` file that works across platforms.
3.  **Workspace Support**: It handles multi-package repos natively (monorepos) without hacks.
4.  **No Python Dependency**: You don't need Python installed to bootstrap Python. `uv` installs Python for you.

ViperX leverages `uv` to ensure your project setup is instantaneous.
""",

    "packaging": """
# Modern Python Packaging 📦

Gone are the days of `setup.py` and `requirements.txt`. The unified standard is **PEP 621**.

### 1. The Standard: `pyproject.toml`
ViperX generates a PEP-621 compliant `pyproject.toml`. This single file contains:
- **[project]**: Usage metadata (name, version, dependencies).
- **[build-system]**: How to build the package (we use `hatchling` or `uv` backend).
- **[tool.uv]**: Dependency management (dev-dependencies, workspaces).

### 2. The `src` Layout
We use the `src/` layout (e.g., `src/my_pkg/`) instead of the flat layout (`my_pkg/` at root).

*   **Prevents Import Parity Errors**: In a flat layout, `import my_pkg` might import the *local folder* instead of the *installed package*. This creates "it works on my machine" bugs where you test uninstalled files.
*   **Forces Installation**: With `src/`, you MUST install the package (`uv sync`) to test it. This guarantees you are testing exactly what your users will run.
""",

    "structure": """
# The ViperX Project Structure 🏗️

### `viperx.yaml`
The **Single Source of Truth**. Instead of remembering CLI flags, you define your project as code (PaC).
This allows `viperx config update` to ensure your config always matches your codebase.

### `src/<package_name>/.env`
**Security Feature**: We place `.env` inside the package, not at root.
- **Why?** When you distribute or deploy, the config context travels with the package source.
- **Isolation**: In a workspace with 3 packages (api, worker, ml), each needs its own secrets. A root `.env` would leak secrets between services.
- **Safety**: `config.py` loads it specifically.

### `src/<package_name>/config.py`
A robust configuration loader that reads `.env`.
- It uses `pydantic-settings` (if ML/DL) or standard `os.environ` patterns.
- It ensures your code crashes *early* (at import time) if secrets are missing, rather than failing silently later.
""",

    "testing": """
# Testing Strategy 🧪

ViperX sets up `pytest` by default because it is the industry standard.

### 1. `conftest.py`
ViperX prepares a `conftest.py` that handles common fixtures.

### 2. Integration vs Unit
- **`tests/unit`**: Fast, isolated tests. No DB, no Network.
- **`tests/integration`**: Real tests against databases or APIs. 

### Why explicit `tests/` folder?
We place tests inside the package (or alongside `src`) to ensure they are packaged (or excluded) correctly via `pyproject.toml` exclusion rules.
""",

    "config": """
# Configuration Philosophy ⚙️

**"Strict on Inputs, Liberal on Outputs"**

1.  **Defaults**: ViperX provides sensible defaults for everything.
2.  **Overrides**: Environment variables ALWAYS override config files.
    - `DB_HOST` env var > `config.yaml` setting.
3.  **Typed Config**: We prefer Pydantic for configuration.
    - It validates types at runtime (e.g. ensures `PORT` is an `int`).
    - It fails fast if configuration is invalid.
"""
}
