import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from viperx.core import ProjectGenerator
from viperx.constants import DEFAULT_LICENSE, DEFAULT_BUILDER, TYPE_CLASSIC, TYPE_ML, TYPE_DL, FRAMEWORK_PYTORCH

console = Console()

class ConfigEngine:
    """
    Orchestrates project creation and updates based on a declarative YAML config.
    Implements the 'Infrastructure as Code' pattern for ViperX.
    """
    
    def __init__(self, config_path: Path, verbose: bool = False):
        self.config_path = config_path
        self.verbose = verbose
        self.config = self._load_config()
        self.root_path = Path.cwd()

    def _load_config(self) -> dict:
        """Load and validate the YAML configuration."""
        if not self.config_path.exists():
            console.print(f"[bold red]Error:[/bold red] Config file not found at {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, "r") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                console.print(f"[bold red]Error:[/bold red] Invalid YAML format: {e}")
                raise ValueError("Invalid YAML")
                
        # Basic Validation
        if "project" not in data or "name" not in data["project"]:
            console.print("[bold red]Error:[/bold red] Config must contain 'project.name'")
            raise ValueError("Missing project.name")
            
        return data

    def apply(self):
        """Apply the configuration to the current directory."""
        from viperx.report import UpdateReport
        from viperx.utils import sanitize_project_name
        
        report = UpdateReport()
        project_conf = self.config.get("project", {})
        settings_conf = self.config.get("settings", {})
        workspace_conf = self.config.get("workspace", {})
        
        project_name = project_conf.get("name")
        clean_name = sanitize_project_name(project_name)
        
        # Determine Root
        current_root = self.root_path / clean_name
        # Heuristic: Are we already inside?
        if self.root_path.name == project_name or self.root_path.name == clean_name:
            current_root = self.root_path

        # ---------------------------------------------------------
        # Phase 0: Context Aggregation (PRESERVED LOGIC)
        # ---------------------------------------------------------
        # We assume dependencies logic is required for both generation and validation.
        
        root_use_config = settings_conf.get("use_config", True)
        root_use_env = settings_conf.get("use_env", False)
        root_use_tests = settings_conf.get("use_tests", True)
        root_type = settings_conf.get("type", TYPE_CLASSIC)
        root_framework = settings_conf.get("framework", FRAMEWORK_PYTORCH)
        
        glob_has_config = root_use_config
        glob_has_env = root_use_env
        glob_is_ml_dl = root_type in [TYPE_ML, TYPE_DL]
        glob_is_dl = root_type == TYPE_DL
        glob_frameworks = {root_framework} if glob_is_dl else set()

        project_scripts = {project_name: f"{clean_name}.main:main"} # Use clean mapping
        
        # List for README generation (Order: Root, then packages)
        packages_list = [{
            "raw_name": project_name,
            "clean_name": clean_name,
            "use_config": root_use_config,
            "use_tests": root_use_tests,
            "use_env": root_use_env
        }]
        
        packages = workspace_conf.get("packages", [])
        for pkg in packages:
            # Scripts
            pkg_name = pkg.get("name")
            pkg_name_clean = sanitize_project_name(pkg_name)
            project_scripts[pkg_name] = f"{pkg_name_clean}.main:main"
            
            # Dependency Aggregation
            p_config = pkg.get("use_config", settings_conf.get("use_config", True))
            p_env = pkg.get("use_env", settings_conf.get("use_env", False))
            p_tests = pkg.get("use_tests", settings_conf.get("use_tests", True))
            p_type = pkg.get("type", TYPE_CLASSIC)
            p_framework = pkg.get("framework", FRAMEWORK_PYTORCH)

            if p_config: glob_has_config = True
            if p_env: glob_has_env = True
            if p_type in [TYPE_ML, TYPE_DL]: glob_is_ml_dl = True
            if p_type == TYPE_DL: 
                 glob_is_dl = True
                 glob_frameworks.add(p_framework)
                 
            packages_list.append({
                "raw_name": pkg_name,
                "clean_name": pkg_name_clean,
                "use_config": p_config,
                "use_tests": p_tests,
                "use_env": p_env
            })

        dep_context = {
            "has_config": glob_has_config,
            "has_env": glob_has_env,
            "is_ml_dl": glob_is_ml_dl,
            "is_dl": glob_is_dl,
            "frameworks": list(glob_frameworks),
            "packages": packages_list
        }

        # ---------------------------------------------------------
        # Phase 1: Root Project (Hydration vs Update)
        # ---------------------------------------------------------
        if not (current_root / "pyproject.toml").exists():
            # CASE A: New Project (Hydration)
            if not current_root.exists() and current_root != self.root_path:
                report.added.append(f"Project '{project_name}' (Scaffolding)")
            else:
                report.added.append(f"Project Scaffolding in existing '{current_root.name}'")
                
            gen = ProjectGenerator(
                name=project_name, # Raw name
                description=project_conf.get("description", ""),
                type=settings_conf.get("type", TYPE_CLASSIC),
                author=project_conf.get("author", None),
                license=project_conf.get("license", DEFAULT_LICENSE),
                builder=project_conf.get("builder", DEFAULT_BUILDER),
                use_env=settings_conf.get("use_env", False),
                use_config=settings_conf.get("use_config", True),
                use_tests=settings_conf.get("use_tests", True),
                framework=settings_conf.get("framework", FRAMEWORK_PYTORCH),
                scripts=project_scripts,
                dependency_context=dep_context,
                verbose=self.verbose
            )
            # We generate at parent if we are creating subfolder, or current if inside
            target_gen_path = current_root.parent if current_root != self.root_path else self.root_path
            gen.generate(target_gen_path)
            
            # Verify creation reference for packages
            if not current_root.exists():
                     if (self.root_path / project_name).exists():
                         current_root = self.root_path / project_name

        else:
            # CASE B: Update Existing Project
            self._update_root_metadata(current_root, project_conf, report)
            
            # Conflict Checks (Root)
            # Check use_env
            if not root_use_env and (current_root / ".env").exists():
                 report.conflicts.append("Root: use_env=False but .env exists")
            pass

        # ---------------------------------------------------------
        # Phase 2: Workspace Packages (Iterative Sync)
        # ---------------------------------------------------------
        
        for pkg in packages:
            pkg_name = pkg.get("name")
            pkg_name_clean = sanitize_project_name(pkg_name)
            
            # Approximate check for existing package src directory
            pkg_path = current_root / "src" / pkg_name_clean
            # Also check if user used hyphens in folder name (classic behavior)
            if not pkg_path.exists():
                 pkg_path_hyphen = current_root / "src" / pkg_name
                 if pkg_path_hyphen.exists():
                      pkg_path = pkg_path_hyphen

            if pkg_path.exists():
                # --- UPDATE CHECK ---
                # Check for REMOVAL of features (Conflict Reporting)
                p_use_env = pkg.get("use_env", settings_conf.get("use_env", False))
                if not p_use_env and (pkg_path / ".env").exists():
                    report.conflicts.append(f"Package '{pkg_name}': use_env=False but .env exists")
                
                # Check for Metadata updates (Assuming we don't sub-update dependencies often)
                # We skip regeneration to be SAFE.
                pass
            else:
                # --- NEW PACKAGE ---
                report.added.append(f"Package '{pkg_name}'")
                
                pkg_gen = ProjectGenerator(
                    name=pkg_name,
                    description=pkg.get("description", ""),
                    type=pkg.get("type", TYPE_CLASSIC),
                    author=project_conf.get("author", "Your Name"),
                    use_env=pkg.get("use_env", settings_conf.get("use_env", False)),
                    use_config=pkg.get("use_config", settings_conf.get("use_config", True)),
                    use_readme=pkg.get("use_readme", False),
                    use_tests=pkg.get("use_tests", settings_conf.get("use_tests", True)),
                    framework=pkg.get("framework", FRAMEWORK_PYTORCH),
                    scripts=project_scripts, 
                    dependency_context=dep_context,
                    verbose=self.verbose
                )
                pkg_gen.add_to_workspace(current_root)

        # Check for Deletions (Packages on disk not in config)
        existing_pkgs = set()
        if (current_root / "src").exists():
             existing_pkgs = {p.name for p in (current_root / "src").iterdir() if p.is_dir()}
        
        # We need to map config names to folder names to check existence
        config_folder_names = {p["clean_name"] for p in packages_list}
        
        # Also include raw names if they exist on disk (classic case)
        config_raw_names = {p["raw_name"] for p in packages_list}
        
        for ep in existing_pkgs:
            if ep not in config_folder_names and ep not in config_raw_names:
                report.deletions.append(f"Package '{ep}' found on disk but missing from config.")

        # ---------------------------------------------------------
        # Phase 3: Config Sync & Reporting
        # ---------------------------------------------------------
        # Sync viperx.yaml
        system_config_path = current_root / "viperx.yaml"
        if self.config_path.absolute() != system_config_path.absolute():
            import shutil
            shutil.copy2(self.config_path, system_config_path)
        
        # Sync Scripts (Safe Update)
        # We recalculate all expected scripts from the current config
        self._update_root_scripts(current_root, project_scripts, report)
        
        # ---------------------------------------------------------
        # Phase 4: Smart Feature Toggle (Hydration & Cleanup Nags)
        # ---------------------------------------------------------
        # Helper to check toggles
        def check_feature(path_check: Path, use_flag: bool, feature_name: str, pkg_label: str):
            if use_flag:
                # ENABLED: Check if missing -> Create
                
                # Heuristic: Is this package/project new?
                # If so, Generator already created files. Don't report "Using/Enabling".
                is_pkg_new = False
                for added_msg in report.added:
                    # Check for Package addition
                    if f"Package '{pkg_label.replace('Package ', '').strip("'")}'" in added_msg:
                        is_pkg_new = True
                    # Check for Root addition (Scaffolding of ANY kind)
                    if "(Scaffolding)" in added_msg and pkg_label == "Root":
                         is_pkg_new = True
                
                if is_pkg_new:
                    return

                if not path_check.exists():
                    report.updated.append(f"{pkg_label}: Enabling {feature_name} (Creating {path_check.name})")
                    if feature_name == "env":
                        # Create .env and .env.example
                        with open(path_check, "w") as f: f.write("ENV=development\n")
                        with open(path_check.with_suffix(".example"), "w") as f: f.write("ENV=development\n")
                    elif feature_name == "config":
                        # Create config.py and config.yaml
                        yaml_path = path_check.parent / "config.yaml"
                        with open(path_check, "w") as f:
                            f.write("import yaml\nfrom pathlib import Path\n\nSETTINGS = {}\n\ndef get_config():\n    return SETTINGS\n")
                        with open(yaml_path, "w") as f: f.write("app:\n  name: 'app'\n")
                        
                        # Fix __init__.py
                        init_path = path_check.parent / "__init__.py"
                        if init_path.exists():
                             with open(init_path, "r") as f: c = f.read()
                             if "from .config import" not in c:
                                 with open(init_path, "w") as f:
                                     f.write("from .config import SETTINGS, get_config\n" + c)
                    elif feature_name == "tests":
                        # Create tests directory and dummy
                        path_check.mkdir(parents=True, exist_ok=True)
                        with open(path_check / "__init__.py", "w") as f: pass
                        with open(path_check / "test_core.py", "w") as f: f.write("def test_dummy(): assert True\n")
            else:
                # DISABLED: Check if exists -> Warn
                if path_check.exists():
                    report.manual_checks.append(f"{pkg_label}: {feature_name}=False but '{path_check.name}' exists. Review/Delete it.")

        # 1. Root Project Features
        check_feature(current_root / ".env", root_use_env, "env", "Root")
        # For config/tests, Root usually follows src layout, but let's check basic locations
        # Root config usually at src/root/config.py, wait ProjectGenerator handles structure
        # Implementation Detail: ViperX Root is complex. Let's focus on Packages for now as Root structure varies (src/root vs root).
        # Actually logic applies to packages more clearly.
        
        # 2. Package Features
        for pkg in packages:
             pkg_name = pkg.get("name")
             pkg_clean = sanitize_project_name(pkg_name)
             pkg_root = current_root / "src" / pkg_clean
             
             if pkg_root.exists():
                 p_env = pkg.get("use_env", settings_conf.get("use_env", False))
                 p_config = pkg.get("use_config", settings_conf.get("use_config", True))
                 p_tests = pkg.get("use_tests", settings_conf.get("use_tests", True))
                 
                 check_feature(pkg_root / ".env", p_env, "env", f"Package '{pkg_name}'")
                 check_feature(pkg_root / "config.py", p_config, "config", f"Package '{pkg_name}'")
                 check_feature(pkg_root / "tests", p_tests, "tests", f"Package '{pkg_name}'")
            
        is_fresh_init = any("Scaffolding" in item for item in report.added)
        if (report.added or report.updated) and not is_fresh_init:
             report.manual_checks.append("Review README.md for any necessary updates (e.g. Project Name, Description).")

        self._print_report(report)

    def _update_root_metadata(self, root: Path, project_conf: dict, report):
        """Safely update pyproject.toml metadata using text manipulation to preserve comments."""
        import re
        pyproject_path = root / "pyproject.toml"
        if not pyproject_path.exists():
            return

        with open(pyproject_path, "r") as f:
            content = f.read()

        changed = False
        
        # Helper to replace Key = "Value"
        def replace_key(key, new_val, text):
            # Regex for 'key = "value"' or "key = 'value'"
            # We assume standard formatting from our template
            pattern = re.compile(f'^{key}\\s*=\\s*["\'].*["\']', re.MULTILINE)
            if pattern.search(text):
                # Check if value actually changed
                match = pattern.search(text)
                current_line = match.group(0)
                new_line = f'{key} = "{new_val}"'
                if current_line != new_line:
                    return pattern.sub(new_line, text), True
            return text, False

        # 1. Description
        new_desc = project_conf.get("description")
        if new_desc:
            content, mod = replace_key("description", new_desc, content)
            if mod:
                report.updated.append(f"Root description -> '{new_desc}'")
                changed = True
        
        # 2. License (Complex because it's a dict inline usually: license = { text = "MIT" })
        new_license = project_conf.get("license")
        if new_license:
             # Look for license = { text = "..." }
             pattern = re.compile(r'^license\s*=\s*\{\s*text\s*=\s*["\'].*["\']\s*\}', re.MULTILINE)
             if pattern.search(content):
                 match = pattern.search(content)
                 current_line = match.group(0)
                 new_line = f'license = {{ text = "{new_license}" }}'
                 if current_line != new_line:
                     content = pattern.sub(new_line, content)
                     report.updated.append(f"Root license -> '{new_license}'")
                     report.manual_checks.append("License type changed. Verify LICENSE file content.")
                     changed = True

        if changed:
            with open(pyproject_path, "w") as f:
                f.write(content)

    def _update_root_scripts(self, root: Path, scripts: dict, report):
        """Safely update [project.scripts] in pyproject.toml using text injection."""
        pyproject_path = root / "pyproject.toml"
        if not pyproject_path.exists():
            return

        with open(pyproject_path, "r") as f:
            content = f.read()

        lines = content.splitlines()
        scripts_header_index = -1
        for i, line in enumerate(lines):
            if line.strip() == "[project.scripts]":
                scripts_header_index = i
                break
        
        if scripts_header_index == -1:
            # Append Header if missing
            lines.append("")
            lines.append("[project.scripts]")
            scripts_header_index = len(lines) - 1

        changed = False
        existing_scripts = {}
        
        # Parse existing scripts (simple line scanning after header)
        # Stop at next section [Section]
        insert_idx = scripts_header_index + 1
        for i in range(scripts_header_index + 1, len(lines)):
            line = lines[i].strip()
            if line.startswith("["):
                break # Next section
            if "=" in line:
                key, val = line.split("=", 1)
                existing_scripts[key.strip()] = val.strip().strip('"').strip("'")
            insert_idx = i + 1

        # Calculate Scripts to Add
        scripts_to_add = []
        for name, entry in scripts.items():
            if name not in existing_scripts:
                 scripts_to_add.append(f'{name} = "{entry}"')
                 report.updated.append(f"Script '{name}' -> '{entry}'")
                 changed = True
            elif existing_scripts[name] != entry:
                # Update logic (Harder with text, for now we skip or simple output)
                # We prioritize ADDING missing scripts. Changing existing lines is risky without regex.
                pass 
        
        if changed:
            # Insert at end of script block
            for s in scripts_to_add:
                lines.insert(insert_idx, s)
                insert_idx += 1
            
            with open(pyproject_path, "w") as f:
                f.write("\n".join(lines) + "\n")
                
    def _print_report(self, report):
        from rich.tree import Tree
        
        if not report.has_events:
            console.print(Panel("✨ [bold green]Start[/bold green]\nNothing to change. Project is in sync.", border_style="green"))
            return

        tree = Tree("📝 [bold]Update Report[/bold]")
        
        if report.added:
            added_node = tree.add("[green]Added[/green]")
            for item in report.added:
                added_node.add(f"[green]+ {item}[/green]")
                
        if report.updated:
            updated_node = tree.add("[blue]Updated (Safe)[/blue]")
            for item in report.updated:
                updated_node.add(f"[blue]~ {item}[/blue]")
                
        if report.conflicts:
            con_node = tree.add("[yellow]Conflicts (No Action Taken)[/yellow]")
            for item in report.conflicts:
                con_node.add(f"[yellow]! {item}[/yellow]")

        if report.deletions:
            del_node = tree.add("[red]Deletions Detected (No Action Taken)[/red]")
            for item in report.deletions:
                del_node.add(f"[red]- {item}[/red]")
                
        if report.manual_checks:
            check_node = tree.add("[magenta]Manual Checks Required[/magenta]")
            for item in report.manual_checks:
                check_node.add(f"[magenta]? {item}[/magenta]")

        console.print(tree)
        console.print("\n[dim]Run completed.[/dim]")
