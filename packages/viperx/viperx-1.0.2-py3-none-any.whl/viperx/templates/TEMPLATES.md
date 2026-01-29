# ViperX Templates Documentation

This document explains the Jinja2 templates used by ViperX to generate project files.

## Template Location

All templates are in `src/viperx/templates/`.

## Available Variables

All templates receive a **context dictionary** with these variables:

### Project Metadata
| Variable         | Type | Description                            | Example              |
| ---------------- | ---- | -------------------------------------- | -------------------- |
| `name`           | str  | Raw project name (may contain hyphens) | `"my-project"`       |
| `clean_name`     | str  | Sanitized name (underscores)           | `"my_project"`       |
| `description`    | str  | Project description                    | `"A cool project"`   |
| `author`         | str  | Author name                            | `"John Doe"`         |
| `email`          | str  | Author email                           | `"john@example.com"` |
| `version`        | str  | Initial version                        | `"0.1.0"`            |
| `python_version` | str  | Python requirement                     | `"3.11"`             |
| `license`        | str  | License type                           | `"MIT"`              |

### Feature Flags
| Variable     | Type | Description          | Default |
| ------------ | ---- | -------------------- | ------- |
| `use_env`    | bool | Generate `.env` file | `False` |
| `use_config` | bool | Generate `config.py` | `True`  |
| `use_tests`  | bool | Generate `tests/`    | `True`  |
| `use_readme` | bool | Generate `README.md` | `True`  |

### Project Type
| Variable    | Type | Description                                 |
| ----------- | ---- | ------------------------------------------- |
| `type`      | str  | `"classic"`, `"ml"`, or `"dl"`              |
| `is_ml`     | bool | True if ML or DL project                    |
| `is_dl`     | bool | True if DL project                          |
| `framework` | str  | DL framework: `"pytorch"` or `"tensorflow"` |

### Build System
| Variable         | Type | Description         |
| ---------------- | ---- | ------------------- |
| `builder`        | str  | `"uv"` or `"hatch"` |
| `build_backend`  | str  | Full backend path   |
| `build_requires` | list | Build dependencies  |

### Workspace Context (for multi-package)
| Variable        | Type | Description                          |
| --------------- | ---- | ------------------------------------ |
| `is_subpackage` | bool | True if adding to existing workspace |
| `scripts`       | dict | CLI entry points                     |
| `packages`      | list | All packages in workspace            |

### Dependency Context (aggregated)
| Variable     | Type | Description             |
| ------------ | ---- | ----------------------- |
| `has_config` | bool | Any package uses config |
| `has_env`    | bool | Any package uses env    |
| `is_ml_dl`   | bool | Any package is ML/DL    |
| `frameworks` | list | All DL frameworks used  |

---

## Template Files

### Core Templates

| File                | Purpose                   |
| ------------------- | ------------------------- |
| `pyproject.toml.j2` | Main project config       |
| `README.md.j2`      | Project documentation     |
| `__init__.py.j2`    | Package init with exports |
| `main.py.j2`        | CLI entry point           |
| `config.py.j2`      | Config loader             |
| `config.yaml.j2`    | Config values             |

### ML/DL Templates

| File                    | Purpose               |
| ----------------------- | --------------------- |
| `data_loader.py.j2`     | Smart data caching    |
| `Base_General.ipynb.j2` | General notebook      |
| `Base_Kaggle.ipynb.j2`  | Kaggle-ready notebook |

### Other Templates

| File                    | Purpose                |
| ----------------------- | ---------------------- |
| `.gitignore.j2`         | Git ignore patterns    |
| `.env.example.j2`       | Example env file       |
| `viperx_config.yaml.j2` | ViperX config template |

---

## Conditional Rendering Examples

### In `pyproject.toml.j2`:
```jinja2
{% if use_config %}
"pyyaml>=6.0.1",
{% endif %}

{% if is_ml %}
"numpy>=1.26.0",
"pandas>=2.2.0",
{% endif %}

{% if is_dl and framework == "pytorch" %}
"torch>=2.5.0",
{% elif is_dl and framework == "tensorflow" %}
"tensorflow>=2.19.0",
{% endif %}
```

### In `__init__.py.j2`:
```jinja2
{% if use_config %}
from .config import SETTINGS, get_config
{% endif %}
```

---

## Adding a New Template

1. Create `src/viperx/templates/myfile.j2`
2. Add rendering logic in `core.py`:
   ```python
   self._render_template("myfile.j2", target_dir / "myfile.ext", context)
   ```
3. Add conditional logic if needed:
   ```python
   if context.get("my_flag"):
       self._render_template(...)
   ```

---

## Testing Templates

After modifying templates, run:
```bash
uv run pytest src/viperx/tests -v
```

Ensure the `test_file_content.py` tests still pass.
