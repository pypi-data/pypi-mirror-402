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
        
        # Author - Robust parsing for string or table array
        # 1. Try standard string: authors = ["Name <email>"] (Not standard PEP 621 but possible)
        # 2. Try PEP 621 table: authors = [{ name = "Name", email = "..." }]
        
        # Try table format first (most specific)
        # authors = [ { name = "Ivann" ... } ]
        author_table_match = re.search(r'authors\s*=\s*\[\s*\{.*?name\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
        if author_table_match:
            project["author"] = author_table_match.group(1)
        else:
            # Fallback to simple name match if present in a standard way
            # This regex looks for 'name = "..."' anywhere after authors = ... which is risky but flexible
            legacy_author = re.search(r'authors\s*=\s*\[.*?["\']([^"\'\{]+)["\']', content, re.DOTALL)
            if legacy_author:
                 # Clean up potential <email>
                 raw = legacy_author.group(1).split('<')[0].strip()
                 if raw:
                     project["author"] = raw

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
        """Write config to viperx.yaml using template hydration (preserves comments)."""
        from viperx.constants import TEMPLATES_DIR
        import yaml
        
        # 1. Load Template
        template_path = TEMPLATES_DIR / "viperx_config.yaml.j2"
        if not template_path.exists():
            # Fallback if template missing (should vary rarely happen)
            return self._write_raw_yaml(config, annotations, output_path)

        content = template_path.read_text()

        # 2. Hydrate Project Section
        proj = config.get("project", {})
        if "name" in proj:
            content = re.sub(r'name: "my-project"', f'name: "{proj["name"]}"', content)
        if "description" in proj:
            # Uncomment description if present
            desc = proj["description"]
            # Look for commented out line
            content = re.sub(r'# description: ".*?"', f'description: "{desc}"', content)
            # Or existing line
            content = re.sub(r'description: ".*?"', f'description: "{desc}"', content)
        if "author" in proj:
            auth = proj["author"]
            content = re.sub(r'# author: ".*?"', f'author: "{auth}"', content)
            content = re.sub(r'author: ".*?"', f'author: "{auth}"', content)
        if "license" in proj:
            lic = proj["license"]
            content = re.sub(r'# license: ".*?"', f'license: "{lic}"', content)
            content = re.sub(r'license: ".*?"', f'license: "{lic}"', content)
        
        # 3. Hydrate Settings Section
        settings = config.get("settings", {})
        for key, val in settings.items():
            # Handle boolean lowercasing for YAML
            val_str = str(val).lower() if isinstance(val, bool) else f'"{val}"'
            
            # Regex to find key: value whether commented or not
            # We look for '  key: current_val' or '#   key: current_val'
            pattern = fr'^\s*{key}:\s*.*$'
            replacement = f'  {key}: {val_str}'
            
            # We use a specific replacement logic to preserve indentation
            content = re.sub(fr'^\s*{key}:.*$', replacement, content, flags=re.MULTILINE)

        # 4. Hydrate Workspace Packages
        packages = config.get("workspace", {}).get("packages", [])
        if packages:
            # Generate YAML block for packages
            pkg_yaml = yaml.dump(packages, default_flow_style=False, sort_keys=False)
            # Indent it
            pkg_yaml_indented = "\n".join(f"    - {line[2:]}" if line.startswith("- ") else f"      {line}" for line in pkg_yaml.splitlines())
            
            # Find packages: line and append
            # We assume the template ends with packages: or has example comments
            if "packages:" in content:
                # Remove any existing example under packages if it looks like empty list []
                content = re.sub(r'packages: \[\]', 'packages:', content)
                
                # Append to end of file if it ends with packages:
                # Or insert after 'packages:' line
                pattern = r'(packages:.*)'
                content = re.sub(pattern, f'\\1\n{pkg_yaml_indented}', content, count=1)
        
        # 5. Add Annotations Header
        header = ""
        if annotations:
            header += "# =============================================================================\n"
            header += "# ⚠️  SCAN ANNOTATIONS (Review Required)\n"
            for ann in annotations:
                header += f"#   - {ann}\n"
            header += "# =============================================================================\n\n"
        
        # Prepend header (after the main title block)
        # Find first blank line after header block
        split_idx = content.find("\n\n")
        if split_idx != -1:
            final_content = content[:split_idx+2] + header + content[split_idx+2:]
        else:
            final_content = header + content

        output_path.write_text(final_content)
        return len(annotations)

    def _write_raw_yaml(self, config: dict, annotations: list[str], output_path: Path):
        """Fallback: Write raw YAML if template is missing."""
        import yaml
        yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False, allow_unicode=True)
        header = "# 🐍 ViperX Project Configuration\n# Generated by 'viperx config update'\n\n"
        if annotations:
            for ann in annotations:
                header += f"# {ann}\n"
        output_path.write_text(header + yaml_content)
        return len(annotations)
