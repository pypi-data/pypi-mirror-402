import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from viperx.core import ProjectGenerator
from viperx.constants import DEFAULT_LICENSE, DEFAULT_BUILDER, TYPE_CLASSIC, FRAMEWORK_PYTORCH

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
        project_conf = self.config.get("project", {})
        settings_conf = self.config.get("settings", {})
        workspace_conf = self.config.get("workspace", {})
        
        project_name = project_conf.get("name")
        target_dir = self.root_path / project_name
        
        # 1. Root Project Handling
        # If we are NOT already in the project dir (checking name), we might need to create it
        # Or if we are running in the root of where `viperx init` is called.
        
        # Heuristic: Are we already in a folder named 'project_name'?
        if self.root_path.name == project_name:
            # We are inside the project folder
            if not (self.root_path / "pyproject.toml").exists():
                 console.print(Panel(f"⚠️  [bold yellow]Current directory matches name but is not initialized. Hydrating:[/bold yellow] {project_name}", border_style="yellow"))
                 gen = ProjectGenerator(
                    name=project_name,
                    description=project_conf.get("description", ""),
                    type=settings_conf.get("type", TYPE_CLASSIC),
                    author=project_conf.get("author", None),
                    license=project_conf.get("license", DEFAULT_LICENSE),
                    builder=project_conf.get("builder", DEFAULT_BUILDER),
                    use_env=settings_conf.get("use_env", False),
                    use_config=settings_conf.get("use_config", True),
                    use_tests=settings_conf.get("use_tests", True),
                    framework=settings_conf.get("framework", FRAMEWORK_PYTORCH),
                    scripts={project_name: f"{project_name}.main:main"}, # Simple default for hydration 
                    verbose=self.verbose
                )
                 # generate() expects parent dir, and will operate on parent/name (which is self.root_path)
                 gen.generate(self.root_path.parent)
            else:
                console.print(Panel(f"♻️  [bold blue]Syncing Project:[/bold blue] {project_name}", border_style="blue"))
            current_root = self.root_path
        else:
            # We are outside, check if it exists
            if target_dir.exists() and (target_dir / "pyproject.toml").exists():
                console.print(Panel(f"♻️  [bold blue]Updating Existing Project:[/bold blue] {project_name}", border_style="blue"))
                current_root = target_dir
            else:
                if target_dir.exists():
                     console.print(Panel(f"⚠️  [bold yellow]Directory exists but not initialized. Hydrating:[/bold yellow] {project_name}", border_style="yellow"))
                # Prepare Scripts & Dependency Context
                packages = workspace_conf.get("packages", [])
                
                # --- Aggregate Global Dependencies ---
                # Start with Root Settings
                # Root is always present (ProjectGenerator uses these)
                root_use_config = settings_conf.get("use_config", True)
                root_use_env = settings_conf.get("use_env", False)
                root_type = settings_conf.get("type", TYPE_CLASSIC)
                root_framework = settings_conf.get("framework", FRAMEWORK_PYTORCH)
                
                glob_has_config = root_use_config
                glob_has_env = root_use_env
                glob_is_ml_dl = root_type in [TYPE_ML, TYPE_DL]
                glob_is_dl = root_type == TYPE_DL
                glob_frameworks = {root_framework} if glob_is_dl else set()

                project_scripts = {project_name: f"{project_name}.main:main"}
                
                for pkg in packages:
                    # Scripts
                    pkg_name = pkg.get("name")
                    from viperx.utils import sanitize_project_name
                    pkg_name_clean = sanitize_project_name(pkg_name)
                    project_scripts[pkg_name_clean] = f"{pkg_name_clean}.main:main"
                    
                    # Dependency Aggregation
                    # Inherit defaults if not defined in pkg
                    p_config = pkg.get("use_config", settings_conf.get("use_config", True))
                    p_env = pkg.get("use_env", settings_conf.get("use_env", False))
                    p_type = pkg.get("type", TYPE_CLASSIC)
                    p_framework = pkg.get("framework", FRAMEWORK_PYTORCH) # Defaults to pytorch if implicit

                    if p_config: glob_has_config = True
                    if p_env: glob_has_env = True
                    if p_type in [TYPE_ML, TYPE_DL]: glob_is_ml_dl = True
                    if p_type == TYPE_DL: 
                         glob_is_dl = True
                         glob_frameworks.add(p_framework)

                dep_context = {
                    "has_config": glob_has_config,
                    "has_env": glob_has_env,
                    "is_ml_dl": glob_is_ml_dl,
                    "is_dl": glob_is_dl,
                    "frameworks": list(glob_frameworks)
                }

                # Create Root (or Hydrate)
                gen = ProjectGenerator(
                    name=project_name,
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
                gen.generate(self.root_path)
                current_root = target_dir
        
        # 2. Copy Config to Root (Source of Truth)
        # Only if we aren't reading the one already there
        system_config_path = current_root / "viperx.yaml"
        if self.config_path.absolute() != system_config_path.absolute():
            import shutil
            shutil.copy2(self.config_path, system_config_path)
            console.print(f"[dim]Saved configuration to {system_config_path.name}[/dim]")

        # 3. Handle Workspace Packages
        packages = workspace_conf.get("packages", [])
        if packages:
            console.print(f"\n📦 [bold]Processing {len(packages)} workspace packages...[/bold]")
            
            for pkg in packages:
                pkg_name = pkg.get("name")
                pkg_path = current_root / "src" / pkg_name.replace("-", "_") # Approximate check
                
                # We instantiate a generator for this package
                pkg_gen = ProjectGenerator(
                    name=pkg_name,
                    description=pkg.get("description", ""),
                    type=pkg.get("type", TYPE_CLASSIC),
                    author=project_conf.get("author", "Your Name"), # Inherit author
                    use_env=pkg.get("use_env", settings_conf.get("use_env", False)),     # Inherit settings or default False
                    use_config=pkg.get("use_config", settings_conf.get("use_config", True)), # Inherit or default True
                    use_readme=pkg.get("use_readme", False),
                    use_tests=pkg.get("use_tests", settings_conf.get("use_tests", True)),
                    framework=pkg.get("framework", FRAMEWORK_PYTORCH),
                    verbose=self.verbose
                )
                
                # Check if package seems to exist (ProjectGenerator handles upgrade logic too)
                pkg_gen.add_to_workspace(current_root)

        console.print(Panel(f"✨ [bold green]Configuration Applied Successfully![/bold green]\nProject is up to date with {self.config_path.name}", border_style="green"))
