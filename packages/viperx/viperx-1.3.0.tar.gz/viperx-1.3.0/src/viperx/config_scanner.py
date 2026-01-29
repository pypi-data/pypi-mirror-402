"""
Config Scanner: Rebuilds viperx.yaml from existing project structure.
"""

import re
from pathlib import Path
from rich.console import Console

console = Console()


class ConfigScanner:
    """Scans existing project and generates/updates viperx.yaml."""
    
    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = project_root
        self.verbose = verbose
    
    def scan(self) -> dict:
        """Scan project and generate viperx.yaml config dict."""
        config = {
            "project": {},
            "settings": {},
            "workspace": {"packages": []}
        }
        
        # 1. Read pyproject.toml for project metadata
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            config["project"] = self._parse_pyproject(pyproject_path)
        
        # 2. Detect project type from structure
        config["settings"]["type"] = self._detect_type()
        
        # 3. Scan src/ for packages
        src_dir = self.project_root / "src"
        if src_dir.exists():
            packages = self._scan_packages(src_dir, config["project"].get("name", ""))
            if packages:
                config["workspace"]["packages"] = packages
        
        return config
    
    def _parse_pyproject(self, pyproject_path: Path) -> dict:
        """Parse project metadata from pyproject.toml."""
        content = pyproject_path.read_text()
        project = {}
        
        # Name
        name_match = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if name_match:
            project["name"] = name_match.group(1)
        
        # Description
        desc_match = re.search(r'^description\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if desc_match:
            project["description"] = desc_match.group(1)
        
        # License
        lic_match = re.search(r'license\s*=\s*{\s*text\s*=\s*["\']([^"\']+)["\']', content)
        if lic_match:
            project["license"] = lic_match.group(1)
        
        # Author
        author_match = re.search(r'name\s*=\s*["\']([^"\']+)["\'].*?email', content, re.DOTALL)
        if author_match:
            project["author"] = author_match.group(1)
        
        return project
    
    def _detect_type(self) -> str:
        """Detect project type from structure and dependencies."""
        from viperx.constants import TYPE_CLASSIC, TYPE_ML, TYPE_DL
        
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text().lower()
            
            if "torch" in content or "tensorflow" in content:
                return TYPE_DL
            if "scikit-learn" in content or "sklearn" in content:
                return TYPE_ML
        
        if (self.project_root / "notebooks").exists():
            return TYPE_ML
        
        return TYPE_CLASSIC
    
    def _scan_packages(self, src_dir: Path, root_name: str) -> list:
        """Scan src/ directory for packages."""
        from viperx.utils import sanitize_project_name
        
        packages = []
        root_clean = sanitize_project_name(root_name) if root_name else ""
        
        for pkg_dir in src_dir.iterdir():
            if not pkg_dir.is_dir():
                continue
            if pkg_dir.name.startswith("_") or pkg_dir.name.startswith("."):
                continue
            
            # Skip root package (it's in settings, not workspace)
            if pkg_dir.name == root_clean:
                continue
            
            pkg_config = {
                "name": pkg_dir.name,
                "use_env": (pkg_dir / ".env").exists() or (pkg_dir / ".env.example").exists(),
                "use_config": (pkg_dir / "config.py").exists() or (pkg_dir / "config.yaml").exists(),
                "use_tests": (pkg_dir / "tests").exists(),
                "use_readme": (pkg_dir / "README.md").exists()
            }
            
            # Get description from __init__.py docstring if exists
            init_py = pkg_dir / "__init__.py"
            if init_py.exists():
                init_content = init_py.read_text()
                docstring_match = re.search(r'^"""([^"]+)"""', init_content, re.MULTILINE)
                if docstring_match:
                    pkg_config["description"] = docstring_match.group(1).strip()
            
            packages.append(pkg_config)
        
        return packages
    
    def update_config(self, existing_config: dict) -> tuple[dict, list[str]]:
        """Update existing config with detected changes. Returns (new_config, annotations)."""
        scanned = self.scan()
        annotations = []
        
        # Merge project section
        for key, value in scanned["project"].items():
            if key not in existing_config.get("project", {}):
                existing_config.setdefault("project", {})[key] = value
                annotations.append(f"project.{key}: ADDED - detected from codebase")
            elif existing_config["project"].get(key) != value:
                old_val = existing_config["project"].get(key)
                existing_config["project"][key] = value
                annotations.append(f"project.{key}: CHANGED - was '{old_val}'")
        
        # Merge settings
        if "type" in scanned["settings"]:
            existing_type = existing_config.get("settings", {}).get("type")
            scanned_type = scanned["settings"]["type"]
            if existing_type and existing_type != scanned_type:
                annotations.append(f"settings.type: MISMATCH - config says '{existing_type}', codebase suggests '{scanned_type}'")
        
        # Merge packages
        existing_pkgs = {p.get("name"): p for p in existing_config.get("workspace", {}).get("packages", [])}
        scanned_pkgs = {p.get("name"): p for p in scanned.get("workspace", {}).get("packages", [])}
        
        # Add new packages
        for pkg_name, pkg_config in scanned_pkgs.items():
            if pkg_name not in existing_pkgs:
                existing_config.setdefault("workspace", {}).setdefault("packages", []).append(pkg_config)
                annotations.append(f"workspace.packages: ADDED - '{pkg_name}' detected in src/")
            else:
                # Check for mismatches
                for key in ["use_env", "use_config", "use_tests", "use_readme"]:
                    config_val = existing_pkgs[pkg_name].get(key)
                    actual_val = pkg_config.get(key)
                    if config_val is not None and config_val != actual_val:
                        annotations.append(f"packages.{pkg_name}.{key}: MISMATCH - config says {config_val}, actual is {actual_val}")
        
        return existing_config, annotations
    
    def write_config(self, config: dict, annotations: list[str], output_path: Path):
        """Write config to viperx.yaml with annotations."""
        import yaml
        
        # Generate YAML
        yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        # Add header with annotations if any
        header = "# 🐍 ViperX Project Configuration\n"
        header += "# Generated/Updated by 'viperx config update'\n"
        
        if annotations:
            header += "#\n# === SCAN ANNOTATIONS ===\n"
            for ann in annotations:
                header += f"# {ann}\n"
            header += "# ========================\n"
        
        header += "\n"
        
        output_path.write_text(header + yaml_content)
        return len(annotations)
