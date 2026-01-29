import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from viperx.core import ProjectGenerator
from viperx.constants import (
    DEFAULT_LICENSE, DEFAULT_BUILDER,
    TYPE_CLASSIC, TYPE_ML, TYPE_DL, PROJECT_TYPES,
    FRAMEWORK_PYTORCH, FRAMEWORK_TENSORFLOW, DL_FRAMEWORKS,
    SUPPORTED_BUILDERS, SUPPORTED_LICENSES
)

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
            
        return self._validate_options(data)

    def _validate_options(self, data: dict) -> dict:
        """Strictly validate configuration options."""
        proj = data.get("project", {})
        sets = data.get("settings", {})
        
        # 1. Project Options
        if "builder" in proj:
            b = proj["builder"]
            if b not in SUPPORTED_BUILDERS:
                console.print(f"[bold red]Error:[/bold red] Invalid Builder '{b}'. Supported: {SUPPORTED_BUILDERS}")
                raise ValueError(f"Invalid Builder '{b}'")
        
        if "license" in proj:
           l = proj["license"]
           if l not in SUPPORTED_LICENSES:
               console.print(f"[bold red]Error:[/bold red] Invalid License '{l}'. Supported: {SUPPORTED_LICENSES}")
               raise ValueError(f"Invalid License '{l}'")
               
        # 2. Settings Options
        if "type" in sets:
            t = sets["type"]
            if t not in PROJECT_TYPES:
                console.print(f"[bold red]Error:[/bold red] Invalid Project Type '{t}'. Supported: {PROJECT_TYPES}")
                raise ValueError(f"Invalid Project Type '{t}'")

        if "framework" in sets and sets.get("type") == TYPE_DL:
             f = sets["framework"]
             if f not in DL_FRAMEWORKS:
                 console.print(f"[bold red]Error:[/bold red] Invalid Framework '{f}'. Supported: {DL_FRAMEWORKS}")
                 raise ValueError(f"Invalid Framework '{f}'")
        
        # 3. Boolean Flags (Strict Check)
        for key in ["use_env", "use_config", "use_tests", "use_readme"]:
            if key in sets and not isinstance(sets[key], bool):
                 console.print(f"[bold red]Error:[/bold red] '{key}' must be 'true' or 'false' (boolean), not '{sets[key]}'")
                 raise ValueError(f"Invalid Boolean '{key}'")
        
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
            # Check use_env at Root? No, strictly in packages now.

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
                # Strict: .env must be at package root
                if not p_use_env and (pkg_path / ".env").exists():
                    report.conflicts.append(f"Package '{pkg_name}': use_env=False but .env exists")
                
                # Check for Metadata updates (Assuming we don't sub-update dependencies often)
                # We skip regeneration to be SAFE.
                pass
            else:
                # --- NEW PACKAGE ---
                report.added.append(f"Package '{pkg_name}'")
                
                p_use_tests = pkg.get("use_tests", settings_conf.get("use_tests", True))
                
                pkg_gen = ProjectGenerator(
                    name=pkg_name,
                    description=pkg.get("description", ""),
                    type=pkg.get("type", TYPE_CLASSIC),
                    author=project_conf.get("author", "Your Name"),
                    use_env=pkg.get("use_env", settings_conf.get("use_env", False)),
                    use_config=pkg.get("use_config", settings_conf.get("use_config", True)),
                    use_readme=pkg.get("use_readme", False),
                    use_tests=p_use_tests,
                    framework=pkg.get("framework", FRAMEWORK_PYTORCH),
                    scripts=project_scripts, 
                    dependency_context=dep_context,
                    verbose=self.verbose
                )
                pkg_gen.add_to_workspace(current_root)
                
                # Update testpaths if package has tests enabled
                if p_use_tests:
                    pkg_name_clean = sanitize_project_name(pkg_name)
                    self._update_testpaths(current_root, pkg_name_clean, report)

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
        def check_feature(path_check: Path, use_flag: bool, feature_name: str, pkg_label: str, pkg_clean_name: str = ""):
            if feature_name == "use_env":
                feature_path = path_check / ".env"
            elif feature_name == "use_config":
                feature_path = path_check / "config.py"
            elif feature_name == "use_tests":
                feature_path = path_check / "tests"
            elif feature_name == "use_readme":
                feature_path = path_check / "README.md"
            else:
                return

            if use_flag:
                # ENABLED: Check if missing -> Create
                
                # Heuristic: Is this package/project new?
                is_pkg_new = False
                pkg_name_in_label = pkg_label.replace("Package '", "").rstrip("'")
                for added_msg in report.added:
                    # Check for Package addition
                    if f"Package '{pkg_name_in_label}'" in added_msg:
                         is_pkg_new = True
                    # Check for Root addition (Scaffolding of ANY kind)
                    if "(Scaffolding)" in added_msg and pkg_label == "Root":
                         is_pkg_new = True
                
                if not feature_path.exists():
                     if is_pkg_new:
                          # Generator likely handled it.
                          pass
                     else:
                          # Generate it!
                          report.added.append(f"{pkg_label}: Enabled {feature_name} (Created {feature_path.name})")
                          if feature_name == "use_env":
                               with open(feature_path, "w") as f:
                                   f.write("# Environment Variables (Hydrated)\n")
                               with open(path_check / ".env.example", "w") as f:
                                   f.write("# Example\n")
                          elif feature_name == "use_config":
                               # Minimal Config
                               with open(feature_path, "w") as f:
                                   f.write("import os\nfrom pathlib import Path\n\n# Configuration\n")
                               with open(path_check / "config.yaml", "w") as f:
                                   f.write("# Config\n")
                               # Inject imports into __init__.py if exists
                               init_py = path_check / "__init__.py"
                               if init_py.exists():
                                   content = init_py.read_text()
                                   if "SETTINGS" not in content:
                                       with open(init_py, "a") as f:
                                           f.write("\nfrom .config import SETTINGS, get_config\n")

                          elif feature_name == "use_tests":
                               feature_path.mkdir(exist_ok=True)
                               with open(feature_path / "__init__.py", "w") as f: 
                                   pass
                               with open(feature_path / "test_core.py", "w") as f:
                                   f.write("def test_placeholder():\n    \"\"\"Placeholder test.\"\"\"\n    assert True\n")
                               # Update testpaths in pyproject.toml
                               if pkg_clean_name:
                                   self._update_testpaths(current_root, pkg_clean_name, report)
                          
                          elif feature_name == "use_readme":
                               # Create minimal README for package
                               pkg_title = pkg_name_in_label.replace("-", " ").replace("_", " ").title()
                               readme_content = f"# {pkg_title}\n\nPackage description.\n"
                               with open(feature_path, "w") as f:
                                   f.write(readme_content)
            else:
                # DISABLED: Check if exists -> Warn/Conflict
                if feature_path.exists():
                    report.conflicts.append(f"{pkg_label}: {feature_name}=False but {feature_path.name} exists")

        # 1. Root Project Features
        # Strict Isolation: Skip Root .env check
        # check_feature(current_root, root_use_env, "use_env", "Root") -> SKIPPED
        # Other Root Checks (if needed):
        # check_feature(current_root, root_use_config, "use_config", "Root") -> SKIPPED
        # check_feature(current_root, root_use_tests, "use_tests", "Root") -> SKIPPED
        
        # 2. Package Features
        # Iterate packages and check features
        # Note: 'packages_list' contains ALL packages, including Root if classic.
        # But here 'packages' comes from config yaml. We should use 'packages_list' logic or re-derive?
        # 'packages' variable iterates `workspace_conf.get("packages", [])`.
        # What about the MAIN Project package?
        # In `ProjectGenerator`, main package is created in `src/{clean_name}`.
        # We need to ensure we check THAT one too.
        
        # Let's check the main project package:
        main_pkg_path = current_root / "src" / clean_name
        if not main_pkg_path.exists():
             main_pkg_path = current_root / "src" / project_name
             
        if main_pkg_path.exists():
             check_feature(main_pkg_path, root_use_env, "use_env", f"Package '{project_name}'", clean_name)
             check_feature(main_pkg_path, root_use_config, "use_config", f"Package '{project_name}'", clean_name)
             check_feature(main_pkg_path, root_use_tests, "use_tests", f"Package '{project_name}'", clean_name)

        # Now check additional packages
        for pkg in packages:
             pkg_name = pkg.get("name")
             pkg_clean = sanitize_project_name(pkg_name)
             p_path = current_root / "src" / pkg_clean
             if not p_path.exists():
                  p_path = current_root / "src" / pkg_name
             
             if p_path.exists():
                  p_env = pkg.get("use_env", settings_conf.get("use_env", False))
                  p_config = pkg.get("use_config", settings_conf.get("use_config", True))
                  p_tests = pkg.get("use_tests", settings_conf.get("use_tests", True))
                  p_readme = pkg.get("use_readme", False)
                  
                  check_feature(p_path, p_env, "use_env", f"Package '{pkg_name}'", pkg_clean)
                  check_feature(p_path, p_config, "use_config", f"Package '{pkg_name}'", pkg_clean)
                  check_feature(p_path, p_tests, "use_tests", f"Package '{pkg_name}'", pkg_clean)
                  check_feature(p_path, p_readme, "use_readme", f"Package '{pkg_name}'", pkg_clean)

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
                     
                     # Try to update LICENSE file if it matches a known template
                     self._update_license_file(root, new_license, report)
                     changed = True

        if changed:
            with open(pyproject_path, "w") as f:
                f.write(content)

    def _update_license_file(self, root: Path, new_license: str, report):
        """Update LICENSE file content if old license is a recognized template."""
        from viperx.licenses import LICENSE_TEMPLATES
        
        license_path = root / "LICENSE"
        if not license_path.exists():
            return
        
        current_content = license_path.read_text()
        
        # Check if current content matches any known license by signature phrases
        is_known_license = False
        license_signatures = {
            "MIT": "MIT License",
            "Apache-2.0": "Apache License",
            "GPLv3": "GNU GENERAL PUBLIC LICENSE"
        }
        
        for lic_type, signature in license_signatures.items():
            if signature in current_content:
                is_known_license = True
                break
        
        if is_known_license and new_license in LICENSE_TEMPLATES:
            # Safe to update
            new_content = LICENSE_TEMPLATES[new_license]
            license_path.write_text(new_content)
            report.updated.append(f"LICENSE file updated to {new_license}")
        else:
            # Not safe, just warn
            report.manual_checks.append("License type changed. Verify LICENSE file content.")

    def _update_testpaths(self, root: Path, pkg_clean_name: str, report):
        """Add package tests path to testpaths in pyproject.toml."""
        import re
        pyproject_path = root / "pyproject.toml"
        if not pyproject_path.exists():
            return
        
        content = pyproject_path.read_text()
        new_testpath = f'"src/{pkg_clean_name}/tests"'
        
        # Check if testpaths section exists
        testpaths_pattern = re.compile(r'testpaths\s*=\s*\[([^\]]*)\]', re.MULTILINE | re.DOTALL)
        match = testpaths_pattern.search(content)
        
        if match:
            # Section exists, check if path already included
            existing_paths = match.group(1)
            if new_testpath in existing_paths:
                return  # Already present
            
            # Add to existing list
            # Find last entry and add after it
            if existing_paths.strip():
                # There are existing entries
                new_paths = existing_paths.rstrip() + f',\n    {new_testpath},'
            else:
                new_paths = f'\n    {new_testpath},'
            
            new_section = f'testpaths = [{new_paths}\n]'
            content = testpaths_pattern.sub(new_section, content)
            report.updated.append(f"Added {pkg_clean_name}/tests to testpaths")
        else:
            # Section doesn't exist, check for [tool.pytest.ini_options]
            pytest_section = re.search(r'\[tool\.pytest\.ini_options\]', content)
            if pytest_section:
                # Insert testpaths after section header
                insert_pos = pytest_section.end()
                insert_text = f'\ntestpaths = [\n    {new_testpath},\n]'
                content = content[:insert_pos] + insert_text + content[insert_pos:]
                report.updated.append(f"Created testpaths with {pkg_clean_name}/tests")
            else:
                # No pytest section, append one
                content += f'\n[tool.pytest.ini_options]\ntestpaths = [\n    {new_testpath},\n]\n'
                report.updated.append(f"Created [tool.pytest.ini_options] with testpaths")
        
        # Clean up duplicate commas and format
        content = re.sub(r',\s*,', ',', content)
        content = re.sub(r',\s*\]', '\n]', content)
        
        pyproject_path.write_text(content)

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
        section_end_idx = len(lines)
        for i in range(scripts_header_index + 1, len(lines)):
            line = lines[i].strip()
            if line.startswith("["):
                section_end_idx = i
                break  # Next section
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
            # Insert at end of script block (before next section)
            for s in scripts_to_add:
                lines.insert(insert_idx, s)
                insert_idx += 1
            
            # Clean up consecutive blank lines in entire file
            cleaned_lines = []
            prev_blank = False
            for line in lines:
                is_blank = line.strip() == ""
                if is_blank and prev_blank:
                    continue  # Skip consecutive blank lines
                cleaned_lines.append(line)
                prev_blank = is_blank
            
            with open(pyproject_path, "w") as f:
                f.write("\n".join(cleaned_lines) + "\n")
                
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
