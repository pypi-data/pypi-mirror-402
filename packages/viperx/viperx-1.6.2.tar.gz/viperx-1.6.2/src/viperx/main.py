"""
ViperX CLI - Professional Python Project Initializer

This module provides the command-line interface for ViperX, supporting:
- Project creation (viperx config -n name)
- Declarative configuration (viperx config -c viperx.yaml)
- Workspace management (viperx package add/delete/update)
- Config synchronization (viperx config update)
- Version migrations (viperx migrate)

CLI Structure:
    viperx config [OPTIONS]     Apply configuration or create project
    viperx config get           Generate viperx.yaml template
    viperx config update        Sync viperx.yaml with codebase
    viperx package add/delete   Manage workspace packages
    viperx migrate              Upgrade to newer ViperX versions
"""
import typer
from pathlib import Path
from rich.panel import Panel
from rich.console import Console

from viperx.core import ProjectGenerator, DEFAULT_LICENSE, DEFAULT_BUILDER
from viperx.config_engine import ConfigEngine
from viperx.constants import (
    TYPE_CLASSIC,
    PROJECT_TYPES,
    DL_FRAMEWORKS,
    FRAMEWORK_PYTORCH,
)
import importlib.metadata
try:
    version = importlib.metadata.version("viperx")
except importlib.metadata.PackageNotFoundError:
    version = "unknown"
    
HELP_TEXT = f"""
[bold green]ViperX[/bold green] (v{version}): Professional Python Project Initializer
.
    
    Automates the creation of professional-grade Python projects using `uv`.
    Supports Standard Libraries, Machine Learning, and Deep Learning templates.
    """

app = typer.Typer(
    help=HELP_TEXT,
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",  # Fix: Use 'rich' to support [bold green] tags
    epilog="Made with ❤️  by KpihX"
)

# Global state for verbose and explain flags
state = {"verbose": False, "explain": False}
console = Console(force_terminal=True)

def version_callback(value: bool):
    if value:
        console.print(f"ViperX CLI Version: [bold green]{version}[/bold green]")
        raise typer.Exit()

@app.callback(invoke_without_command=True)
def cli_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", "-v", "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit."
    ),
    explain: bool = typer.Option(
         False, "--explain",
         help="Enable educational mode: explains decisions and architectural choices."
    )
):
    """
    [bold green]ViperX[/bold green]: The Mentor-Based Python Project Initializer.
    
    Automates the creation of professional-grade Python projects using `uv`.
    Focuses on education, transparency, and freedom.
    """
    # Always verbose by default for transparency
    state["verbose"] = True
    state["explain"] = explain
    
    if explain and ctx.invoked_subcommand is None:
        console.print(Panel(
            "🎓 [bold green]Explain Mode Enabled[/bold green]\n\n"
            "ViperX will now explain its actions in detail.\n"
            "Try running a command to see it in action:\n"
            "  [cyan]viperx config -n my-project[/cyan]",
            border_style="green"
        ))

# --- Educational Content ---
KNOWLEDGE_BASE = {
    "uv": """
# Why uv?

**uv** is an extremely fast Python package installer and resolver, written in Rust.

### Why ViperX uses it:
1.  **Speed**: It's 10-100x faster than pip/poetry.
2.  **determinism**: It generates a universal `uv.lock` file.
3.  **workspace support**: It handles multi-package repos natively.
4.  **no python dependency**: You don't need Python installed to bootstrap Python.

ViperX leverages `uv` to ensure your project setup is instantaneous.
""",
    "packaging": """
# Modern Python Packaging

Gone are the days of `setup.py` and `requirements.txt`.

### The Standard: `pyproject.toml`
ViperX generates a PEP-621 compliant `pyproject.toml`.
- **[project]**: Metadata (name, version, dependencies).
- **[build-system]**: How to build the package (we use `hatchling` or `uv` backend).
- **[tool.uv]**: Dependency management (dev-dependencies, workspaces).

### Src Layout
We use the `src/` layout (e.g., `src/my_pkg/`).
- **Prevents import errors**: You can't accidentally import the local folder without installing it.
- **Forces installation**: Ensures you test the *installed* package, not the local files.
""",
    "structure": """
# The ViperX Project Structure

### `viperx.yaml`
The single source of truth. Defines your project as code.

### `src/<package_name>/`
Your actual code lives here.

### `src/<package_name>/.env`
**Security Feature**: We place `.env` inside the package, not at root.
- **Why?** When you distribute or deploy, the config travels with the package context (if needed) but is excluded via `.gitignore`.
- It keeps environment variables scoped to the specific package in a workspace.

### `src/<package_name>/config.py`
A robust configuration loader that reads `.env` and `config.yaml`.
- It uses `pydantic-settings` (if ML) or standard `os.environ` patterns.
- It ensures your code crashes *early* if secrets are missing.
"""
}

@app.command("learn")
def learn_command(
    topic: str = typer.Argument(None, help="Specific topic: 'uv', 'packaging', 'structure'")
):
    """
    🦅 **Access the Knowledge Base.**
    
    Lists curated resources and educational explanations.
    """
    from rich.markdown import Markdown
    
    if not topic:
        console.print(Panel(
            "📚 [bold blue]ViperX Learning Hub[/bold blue]\n\n"
            "Use [bold]viperx learn <topic>[/bold] to dive deeper.\n"
            "Available topics:\n"
            "- [green]packaging[/green]: Modern Python packaging (pyproject.toml)\n"
            "- [green]uv[/green]: Why we use uv over pip/poetry\n"
            "- [green]structure[/green]: The 'src' layout explained\n",
            border_style="blue"
        ))
        return

    content = KNOWLEDGE_BASE.get(topic.lower())
    if content:
        console.print(Panel(Markdown(content), title=f"🦅 ViperX Academy: {topic}", border_style="cyan"))
    else:
        console.print(f"[red]Topic '{topic}' not found.[/red] Try 'packaging', 'uv', or 'structure'.")
        



# Config Management Group (The Main Entry Point)
config_app = typer.Typer(
    help="Manage Declarative Configuration (viperx.yaml).",
    no_args_is_help=False,  # Allow running without subcommands (acts as apply)
)
app.add_typer(config_app, name="config")

# Alias: `viperx init` -> `viperx config` (UX improvement)
app.add_typer(config_app, name="init", help="Alias for 'config'. Initialize a new project.")


@config_app.callback(invoke_without_command=True)
def config_main(
    ctx: typer.Context,
    # --- Config Driven Mode ---
    config: Path = typer.Option(
        None, "--config", "-c",
        help="Path to a viperx.yaml configuration file. If provided, ignores other options."
    ),
    # --- Interactive Mode Options ---
    name: str = typer.Option(None, "--name", "-n", help="Name of the project"),
    description: str = typer.Option(None, "--description", "-d", help="Project description"),
    type: str = typer.Option(
        TYPE_CLASSIC, "--type", "-t", 
        help="Project type: [green]classic[/green], [blue]ml[/blue], [red]dl[/red]"
    ),
    author: str = typer.Option(
        None, "--author", "-a", 
        help="Author name. Defaults to git user."
    ),
    license: str = typer.Option(
        DEFAULT_LICENSE, "--license", "-l", 
        help="License type (MIT, Apache-2.0, GPLv3)"
    ),
    builder: str = typer.Option(
        DEFAULT_BUILDER, "--builder", "-b", 
        help="Build backend. Defaults to [bold]uv[/bold]."
    ),
    framework: str = typer.Option(
        FRAMEWORK_PYTORCH, "--framework", "-f",
        help=f"DL Framework ({'|'.join(DL_FRAMEWORKS)}). Defaults to pytorch."
    ),
    use_env: bool = typer.Option(True, "--env/--no-env", help="Generate .env file"),
    use_config: bool = typer.Option(True, "--embed-config/--no-embed-config", help="Generate embedded config"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """
    **Configure & Initialize**: Apply configuration to create or update a project.
    
    usage: [bold]viperx config [OPTIONS][/bold]
           [bold]viperx config get[/bold]
    """
    # Check if a subcommand (like 'get') is invoked
    if ctx.invoked_subcommand is not None:
        return

    # --- Apply Logic (Former Init) ---
    
    # 1. Declarative Mode
    if config:
        if not config.exists():
            console.print(f"[bold red]Error:[/bold red] Configuration file '{config}' not found.")
            raise typer.Exit(code=1)
            
        engine = ConfigEngine(config, verbose=verbose or state["verbose"])
        engine.apply()
        return

    # 2. Imperative / Interactive Mode
    
    # Check if we should trigger Wizard Mode
    # If NO config, NO name, and NO other flags that imply specific intent (except verbose)
    interactive_mode = False
    
    # We check if context has been invoked with arguments. 
    # Typer doesn't easily expose "were any options passed?" directly without checking context.
    # But checking if 'name' is None is a good proxy, as 'name' is required for non-interactive imperative mode.
    
    if not config and not name:
         # Trigger Wizard
         console.print(Panel("🧙 [bold blue]ViperX Interactive Wizard[/bold blue]", border_style="blue"))
         
         # 1. Name
         name = typer.prompt("Project Name")
         
         # 2. Type
         # We can present choices
         type = typer.prompt("Project Type", default=TYPE_CLASSIC, show_default=True)
         if type not in PROJECT_TYPES:
             if typer.confirm(f"'{type}' is not a standard type ({PROJECT_TYPES}). Use anyway?", default=False):
                 pass # User insists
             else:
                 # Retry once or default
                 type = typer.prompt("Project Type", default=TYPE_CLASSIC)

         # 3. Framework (if DL)
         if type == "dl":
             framework = typer.prompt("Deep Learning Framework", default=FRAMEWORK_PYTORCH)
         
         # 4. Author (Git detection is implicit, but we can ask)
         # author = typer.prompt("Author", default=git_user...) -> Let's stick to defaults for speed unless verbose
         
         console.print(f"\n[dim]Initializing {name} ({type})...[/dim]\n")
         interactive_mode = True

    if not name:
         console.print("[bold red]Error:[/bold red] Missing option '--name' / '-n' and interactive mode failed.")
         raise typer.Exit(code=1)

    if type not in PROJECT_TYPES:
        console.print(f"[bold red]Error:[/bold red] Invalid type '{type}'. Must be one of: {', '.join(PROJECT_TYPES)}")
        raise typer.Exit(code=1)

    console.print(Panel(f"Initializing [bold blue]{name}[/bold blue]", border_style="blue"))
    
    # Check if target directory (sanitized) exists
    from viperx.utils import sanitize_project_name
    name_clean = sanitize_project_name(name)
    target_dir = Path.cwd() / name_clean
    if target_dir.exists():
         console.print(f"[bold yellow]Warning:[/bold yellow] Directory {name_clean} already exists. Updating.")
    
    generator = ProjectGenerator(
        name=name,
        description=description,
        type=type,
        author=author,
        license=license,
        builder=builder,
        use_env=use_env,
        use_config=use_config,
        framework=framework,
        verbose=verbose or state["verbose"]
    )
    
    # Generate in current directory
    generator.generate(Path.cwd())




@config_app.command("get")
def config_get(
    filename: Path = typer.Option("viperx.yaml", "--output", "-o", help="Output filename")
):
    """
    Get the default configuration template (viperx.yaml).
    Use this to start a 'Project as Code' workflow.
    """
    from viperx.constants import TEMPLATES_DIR
    
    template_path = TEMPLATES_DIR / "viperx_config.yaml.j2"
    if not template_path.exists():
         console.print("[bold red]Error:[/bold red] Config template not found.")
         raise typer.Abort()
         
    with open(template_path, "r") as f:
        content = f.read()
        
    if filename.exists():
        if not typer.confirm(f"File {filename} already exists. Overwrite?"):
            raise typer.Abort()
            
    with open(filename, "w") as f:
        f.write(content)
        
    console.print(Panel(f"✅ Generated configuration template: [bold green]{filename}[/bold green]\n\nRun [bold]viperx init -c {filename}[/bold] to create your project.", border_style="green"))


@config_app.command("update")
def config_update(
    config_path: Path = typer.Option(
        Path("viperx.yaml"), "-c", "--config",
        help="Path to viperx.yaml (will be created/updated)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """
    **Rebuild viperx.yaml from existing codebase.**
    
    Scans the project structure and updates viperx.yaml to match reality.
    - Detects packages in src/
    - Detects use_config, use_env, use_tests from actual files
    - Adds annotations for any mismatches
    
    [bold]Safe Mode:[/bold] Never deletes config lines, only updates/adds.
    """
    from viperx.config_scanner import ConfigScanner
    import yaml
    
    project_root = Path.cwd()
    scanner = ConfigScanner(project_root, verbose=verbose)
    
    if config_path.exists():
        # Update existing config
        with open(config_path, "r") as f:
            existing_config = yaml.safe_load(f) or {}
        
        new_config, annotations = scanner.update_config(existing_config)
        num_annotations = scanner.write_config(new_config, annotations, config_path)
        
        if num_annotations > 0:
            console.print(Panel(
                f"✅ Updated [bold green]{config_path}[/bold green]\n\n"
                f"[yellow]{num_annotations}[/yellow] annotations added (see file header).\n"
                f"Review the file and resolve any mismatches.",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                f"✅ [bold green]{config_path}[/bold green] is in sync with codebase!",
                border_style="green"
            ))
    else:
        # Create new config from scan
        config = scanner.scan()
        scanner.write_config(config, [], config_path)
        console.print(Panel(
            f"✅ Created [bold green]{config_path}[/bold green] from codebase scan.\n\n"
            f"Run [bold]viperx config -c {config_path}[/bold] to validate.",
            border_style="green"
        ))


@config_app.command("eject")
def config_eject(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """
    **Eject ViperX**: Remove viperx.yaml and detach from the tool.
    
    Leaves your project as a standard Python/uv project.
    No lock-in. No hidden files.
    """
    config_path = Path("viperx.yaml")
    
    if not config_path.exists():
        console.print("[yellow]No viperx.yaml found. Nothing to eject.[/yellow]")
        raise typer.Exit()
        
    if not force:
        console.print(Panel(
            "[bold red]⚠️  Ejecting ViperX[/bold red]\n\n"
            "This will permanently delete [bold]viperx.yaml[/bold].\n"
            "Your project code, dependencies, and uv configuration will remain untouched.\n"
            "You will lose the ability to use 'viperx config update' or 'viperx migrate'.",
            border_style="red"
        ))
        if not typer.confirm("Are you sure you want to eject?"):
            raise typer.Abort()
            
    config_path.unlink()
    console.print("[bold green]Start[/bold green] Ejected successfully. You are now free! 🦅")


# Package management group
package_app = typer.Typer(
    help="Manage workspace packages (add, update, delete).",
    no_args_is_help=True
)
app.add_typer(package_app, name="package")

@package_app.command("add")
def package_add(
    name: str = typer.Option(..., "--name", "-n", help="Name of the new package"),
    type: str = typer.Option(
        TYPE_CLASSIC, "--type", "-t", 
        help="Project type: [green]classic[/green], [blue]ml[/blue], [red]dl[/red]"
    ),
    framework: str = typer.Option(
        FRAMEWORK_PYTORCH, "--framework", "-f",
        help=f"DL Framework ({'|'.join(DL_FRAMEWORKS)}). Defaults to pytorch."
    ),
    use_env: bool = typer.Option(True, "--env/--no-env", help="Generate .env file"),
    use_config: bool = typer.Option(True, "--embed-config/--no-embed-config", help="Generate embedded config"),
    use_readme: bool = typer.Option(False, "--readme/--no-readme", help="Generate README.md"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """
    Add a new package to the workspace.
    
    Detects if the current directory is a workspace. If so, adds the new package.
    If it's a standalone project, upgrades it to a workspace first.
    """
    console.print(Panel.fit("🚀 [bold yellow]ViperX[/bold yellow] - Initialize a new project", border_style="green"))

    generator = ProjectGenerator(
        name=name, 
        description="Workspace Member", 
        type=type, 
        author="Your Name", 
        # Defaults
        use_env=use_env, 
        use_config=use_config,
        use_readme=use_readme,
        framework=framework,
        verbose=verbose or state["verbose"]
    )
    generator.add_to_workspace(Path.cwd())

@package_app.command("delete")
def package_delete(
    name: str = typer.Option(..., "--name", "-n", help="Name of the package to delete"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Delete a package from the workspace.
    
    Removes the folder and the member entry from pyproject.toml.
    """
    verbose = verbose or state["verbose"]
    
    if not force:
        if not typer.confirm(f"Are you sure you want to delete package '{name}'?"):
            raise typer.Abort()

    console.print(Panel(f"Deleting package [bold red]{name}[/bold red]", border_style="red"))
    
    # We init generator just to use its helper methods (could be static, but this is fine)
    generator = ProjectGenerator(name=name, description="", type="classic", author="", use_env=False, use_config=False, verbose=verbose)
    generator.delete_from_workspace(Path.cwd())

@package_app.command("update")
def package_update(
    name: str = typer.Option(..., "--name", "-n", help="Name of the package to update"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """
    Update a package's dependencies (uv lock --upgrade).
    """
    verbose = verbose or state["verbose"]
    console.print(Panel(f"Updating package [bold blue]{name}[/bold blue]", border_style="blue"))
    
    generator = ProjectGenerator(name=name, description="", type="classic", author="", use_env=False, use_config=False, verbose=verbose)
    generator.update_package(Path.cwd())


# =============================================================================
# Template Management (V1.5.0 Freedom)
# =============================================================================

template_app = typer.Typer(
    help="Manage templates (eject, add, list).",
    no_args_is_help=True
)
app.add_typer(template_app, name="template")

@template_app.command("list")
def template_list():
    """List available templates and their source (System vs User)."""
    from viperx.templates import TemplateManager
    TemplateManager().list_templates()

@template_app.command("eject")
def template_eject(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing user templates")
):
    """
    Copy internal templates to ~/.config/viperx/templates/ for customization.
    """
    from viperx.templates import TemplateManager
    TemplateManager().eject_templates(force=force)

@template_app.command("add")
def template_add(
    url: str = typer.Argument(..., help="Git URL of the template pack")
):
    """
    Download templates from a Git repository (Plugin system).
    
    Flattens all .j2 files from the repo into your user template dir.
    """
    from viperx.templates import TemplateManager
    TemplateManager().add_template_pack(url)



# =============================================================================
# Migrate Command
# =============================================================================

@app.command()
def migrate(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying"),
    target_version: str = typer.Option(None, "--to", help="Target version (default: current ViperX version)"),
):
    """
    Migrate an existing project to a newer ViperX version.
    """
    from viperx.migrations import run_migrations, get_project_version
    # Import to register migrations
    import viperx.migrations.v1_0_x  # noqa
    
    project_root = Path.cwd()
    
    # Check if viperx.yaml exists
    if not (project_root / "viperx.yaml").exists():
        console.print("[bold red]Error:[/bold red] No viperx.yaml found in current directory.")
        raise typer.Exit(1)
    
    current = get_project_version(project_root)
    target = target_version or version
    
    console.print(Panel(
        f"Migrating from [bold]{current or 'unknown'}[/bold] to [bold]{target}[/bold]",
        title="🔄 ViperX Migration",
        border_style="blue"
    ))
    
    if dry_run:
        console.print("[dim]Dry run mode - no changes will be made[/dim]\n")
    
    changes = run_migrations(project_root, target, dry_run)
    
    if changes:
        console.print("[green]Changes:[/green]")
        for change in changes:
            console.print(f"  • {change}")
    else:
        console.print("[green]✓[/green] Project is already up to date!")
    
    if not dry_run and changes:
        console.print(f"\n[green]✓[/green] Migrated to version {target}")


if __name__ == "__main__":
    try:
        app()
    except SystemExit as e:
        if e.code != 0:
            # On error (non-zero exit), display help as requested
            from typer.main import get_command
            import click
            cli = get_command(app)
            # Create a dummy context to render help
            # We print it to stderr or stdout? Console prints to stdout usually.
            # User wants it displayed immediately.
            with click.Context(cli) as ctx:
                 console.print("\n")
                 console.print(cli.get_help(ctx))
            raise
