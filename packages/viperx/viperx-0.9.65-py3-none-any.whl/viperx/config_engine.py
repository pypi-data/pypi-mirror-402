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
        
        target_name = project_conf.get("name")
        clean_name = sanitize_project_name(target_name)
        
        # Determine Root
        current_root = self.root_path / clean_name
        # Heuristic: Are we already inside?
        if self.root_path.name == target_name or self.root_path.name == clean_name:
            current_root = self.root_path

        # ---------------------------------------------------------
        # Phase 0: Global Aggregation (Scripts & Dependencies)
        # ---------------------------------------------------------
        # We need to gather ALL scripts and cumulative flags (use_env, use_config)
        # to ensure the Root Project is provisioned correctly.
        
        all_scripts = {target_name: f"{clean_name}.main:main"}
        
        # Start with Root Settings
        glob_use_env = settings_conf.get("use_env", False)
        glob_use_config = settings_conf.get("use_config", True)
        
        packages = workspace_conf.get("packages", [])
        for pkg in packages:
             # Scripts
             pkg_name = pkg.get("name")
             pkg_clean = pkg_name.replace("-", "_")
             all_scripts[pkg_name] = f"{pkg_clean}.main:main"
             
             # Dependency Aggregation
             # If ANY package needs .env, the root should probably have python-dotenv
             if pkg.get("use_env", settings_conf.get("use_env", False)):
                 glob_use_env = True
             if pkg.get("use_config", settings_conf.get("use_config", True)):
                 glob_use_config = True

        # ---------------------------------------------------------
        # Phase 1: Root Project (Hydration vs Update)
        # ---------------------------------------------------------
        if not (current_root / "pyproject.toml").exists():
            # CASE A: New Project (Hydration)
            if not current_root.exists() and current_root != self.root_path:
                report.added.append(f"Project '{target_name}' (Scaffolding)")
            else:
                report.added.append(f"Project Scaffolding in existing '{current_root.name}'")
                
            gen = ProjectGenerator(
                name=target_name,
                description=project_conf.get("description", ""),
                type=settings_conf.get("type", TYPE_CLASSIC),
                author=project_conf.get("author", None),
                license=project_conf.get("license", DEFAULT_LICENSE),
                builder=project_conf.get("builder", DEFAULT_BUILDER),
                # PASS GLOBAL FLAGS causing dependencies to be added
                use_env=glob_use_env,
                use_config=glob_use_config,
                use_tests=settings_conf.get("use_tests", True),
                framework=settings_conf.get("framework", FRAMEWORK_PYTORCH),
                scripts=all_scripts, 
                verbose=self.verbose
            )
            # We generate at parent if we are creating subfolder, or current if inside
            target_gen_path = current_root.parent if current_root != self.root_path else self.root_path
            gen.generate(target_gen_path)
        else:
            # CASE B: Update Existing Project
            self._update_root_metadata(current_root, project_conf, report)
            
            # --- SAFE INJECTION ---
            self._ensure_scripts_in_pyproject(current_root, all_scripts, report)
            self._ensure_dependencies(current_root, glob_use_env, glob_use_config, report)

            pass

        # ---------------------------------------------------------
        # Phase 2: Workspace Packages (Iterative Sync)
        # ---------------------------------------------------------
        # packages list already retrieved above
        
        # Build Context (Shared) -> Can be optimized
        # But for now, we process packages
        
        existing_pkgs = set()
        if (current_root / "src").exists():
             existing_pkgs = {p.name for p in (current_root / "src").iterdir() if p.is_dir()}

        config_pkg_names = set()

        for pkg in packages:
            pkg_name = pkg.get("name")
            config_pkg_names.add(pkg_name)
            pkg_name_clean = pkg_name.replace("-", "_") # Approx
            
            pkg_path = current_root / "src" / pkg_name_clean
            
            if pkg_path.exists():
                # --- UPDATE CHECK ---
                # Check conflicts logic here (simplified for user request)
                # Verify description/author/etc if we wanted deep warnings
                
                # Check for REMOVAL of features
                # e.g. Config says use_env=False, but .env exists
                p_use_env = pkg.get("use_env", settings_conf.get("use_env", False))
                if not p_use_env and (pkg_path / ".env").exists():
                    report.deletions.append(f"Package '{pkg_name}': use_env=False but .env exists (Manual Delete Required)")
                
                # We do NOT run generation for existing packages to avoid overwrite
                # But we might update metadata if supported later
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
                    verbose=self.verbose
                )
                pkg_gen.add_to_workspace(current_root)

        # Check for Deletions (Packages on disk not in config)
        # Note: clean_names vs raw_names mismatch makes this tricky without strict mapping
        # skipping strictly strictly for now to avoid false positives on diff naming
        
        # ---------------------------------------------------------
        # Phase 3: Config Sync & Reporting
        # ---------------------------------------------------------
        # Sync viperx.yaml
        system_config_path = current_root / "viperx.yaml"
        if self.config_path.absolute() != system_config_path.absolute():
            import shutil
            shutil.copy2(self.config_path, system_config_path)
            
        self._print_report(report)

    def _ensure_dependencies(self, root: Path, need_env: bool, need_config: bool, report):
        """Ensure core dependencies exist in pyproject.toml."""
        import toml
        pyproject_path = root / "pyproject.toml"
        if not pyproject_path.exists():
            return
            
        with open(pyproject_path, "r") as f:
            data = toml.load(f)
            
        project = data.get("project", {})
        deps = project.get("dependencies", [])
        
        changed = False
        
        # Check python-dotenv
        if need_env:
            has_dotenv = any("python-dotenv" in d for d in deps)
            if not has_dotenv:
                deps.append("python-dotenv>=1.0.0")
                report.added.append("Dependency 'python-dotenv>=1.0.0'")
                changed = True

        # Check pyyaml
        if need_config:
            has_pyyaml = any("pyyaml" in d for d in deps)
            if not has_pyyaml:
                deps.append("pyyaml>=6.0")
                report.added.append("Dependency 'pyyaml>=6.0'")
                changed = True
                
        if changed:
            project["dependencies"] = deps
            data["project"] = project
            with open(pyproject_path, "w") as f:
                toml.dump(data, f)

    def _update_root_metadata(self, root: Path, project_conf: dict, report):
        """Safely update pyproject.toml metadata."""
        import toml
        pyproject_path = root / "pyproject.toml"
        if not pyproject_path.exists():
            return

        with open(pyproject_path, "r") as f:
            data = toml.load(f)

        changed = False
        proj = data.get("project", {})
        
        # 1. Description
        new_desc = project_conf.get("description")
        if new_desc and proj.get("description") != new_desc:
            proj["description"] = new_desc
            report.updated.append(f"Root description -> '{new_desc}'")
            changed = True
            
        # 2. Author (simplified, assumes list of dicts)
        new_author = project_conf.get("author")
        if new_author:
             # Very basic check: replace first author name
             authors = proj.get("authors", [])
             if authors and authors[0].get("name") != new_author:
                 authors[0]["name"] = new_author
                 report.updated.append(f"Root author -> '{new_author}'")
                 changed = True
                 
        # 3. License
        new_license = project_conf.get("license")
        current_lic = proj.get("license", {}).get("text")
        if new_license and current_lic != new_license:
            proj["license"] = {"text": new_license}
            report.updated.append(f"Root license -> '{new_license}'")
            changed = True
            # TODO: Regenerate LICENSE file too?
            report.manual_checks.append("License type changed. Verify LICENSE file content.")

        if changed:
            data["project"] = proj
            with open(pyproject_path, "w") as f:
                toml.dump(data, f)

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
            updated_node = tree.add("[blue]Updated[/blue]")
            for item in report.updated:
                updated_node.add(f"[blue]~ {item}[/blue]")
                
        if report.deletions:
            del_node = tree.add("[yellow]Manual Deletions Required[/yellow]")
            for item in report.deletions:
                del_node.add(f"[yellow]- {item}[/yellow]")
                
        if report.manual_checks:
            check_node = tree.add("[magenta]Manual Checks[/magenta]")
            for item in report.manual_checks:
                check_node.add(f"[magenta]? {item}[/magenta]")

        console.print(tree)
        console.print("\n[dim]Run completed.[/dim]")
