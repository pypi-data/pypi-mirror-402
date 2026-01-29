import typer
from typing_extensions import Annotated
from pathlib import Path
from rich import print
from rich.panel import Panel
from rich.console import Console
import shutil

from viperx.core import ProjectGenerator, TYPE_CLASSIC, TYPE_ML, TYPE_DL, DEFAULT_LICENSE, DEFAULT_BUILDER
from viperx.utils import validate_project_name, check_uv_installed
from viperx.config_engine import ConfigEngine
from viperx.constants import (
    PROJECT_TYPES,
    DL_FRAMEWORKS,
    FRAMEWORK_PYTORCH,
)

HELP_TEXT = """
[bold green]ViperX[/bold green]: Professional Python Project Initializer
.
    
    Automates the creation of professional-grade Python projects using `uv`.
    Supports Standard Libraries, Machine Learning, and Deep Learning templates.
    """

app = typer.Typer(
    help=HELP_TEXT,
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="markdown",
    epilog="Made with ❤️ by KpihX"
)

# Global state for verbose flag
state = {"verbose": False}
console = Console(force_terminal=True)

@app.callback()
def cli_callback(
    verbose: bool = typer.Option(
        False, "-v", "--verbose", 
        help="Enable verbose logging."
    )
):
    """
    **ViperX**: Professional Python Project Initializer.
    
    Automates the creation of professional-grade Python projects using `uv`.
    Supports Standard Libraries, Machine Learning, and Deep Learning templates.
    """
    if verbose:
        state["verbose"] = True
        console.print("[dim]Verbose mode enabled[/dim]")


@app.command()
def init(
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
    use_config: bool = typer.Option(True, "--config/--no-config", help="Generate embedded config"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """
    Initialize a new Python project.
    
    Can stem from a config file (Declarative) or CLI arguments (Imperative).
    """
    # 1. Declarative Mode
    if config:
        if not config.exists():
            console.print(f"[bold red]Error:[/bold red] Configuration file '{config}' not found.")
            raise typer.Exit(code=1)
            
        engine = ConfigEngine(config, verbose=verbose or state["verbose"])
        engine.apply()
        return

    # 2. Imperative Mode (Validation)
    if not name:
         console.print("[bold red]Error:[/bold red] Missing option '--name' / '-n'. Required in manual mode.")
         raise typer.Exit(code=1)

    if type not in PROJECT_TYPES:
        console.print(f"[bold red]Error:[/bold red] Invalid type '{type}'. Must be one of: {', '.join(PROJECT_TYPES)}")
        raise typer.Exit(code=1)

    console.print(Panel(f"Initializing [bold blue]{name}[/bold blue]", border_style="blue"))
    
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

# Config Management Group
config_app = typer.Typer(
    help="Manage Declarative Configuration (viperx.yaml).",
    no_args_is_help=True
)
app.add_typer(config_app, name="config")

@config_app.command("get")
def config_get(
    filename: Path = typer.Option("viperx.yaml", "--output", "-o", help="Output filename")
):
    """
    Get the default configuration template (viperx.yaml).
    Use this to start a 'Project as Code' workflow.
    """
    from viperx.constants import TEMPLATES_DIR
    import jinja2
    
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
    use_config: bool = typer.Option(True, "--config/--no-config", help="Generate embedded config"),
    use_readme: bool = typer.Option(True, "--readme/--no-readme", help="Generate README.md"),
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

if __name__ == "__main__":
    app()
