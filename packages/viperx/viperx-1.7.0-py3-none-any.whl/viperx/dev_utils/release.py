
"""
ViperX Release Automator 🦅

Usage:
  uv run release all --msg "feat: New awesome stuff"
"""

import subprocess
import sys
import shutil
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="ViperX Release Automation Tool")
console = Console()

# src/viperx/dev_utils/release.py -> ../../../.. -> PROJECT_ROOT
# Adjust based on actual depth.
# If installed as package: We need to find the project root dynamically or assume CWD is root (safe for dev tool).
PROJECT_ROOT = Path.cwd()

def run_cmd(cmd: str, cwd: Path = PROJECT_ROOT, exit_on_fail: bool = True):
    """Run a shell command with transparency."""
    console.print(f"[dim]$ {cmd}[/dim]")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0 and exit_on_fail:
        console.print(f"[bold red]❌ Command failed: {cmd}[/bold red]")
        sys.exit(result.returncode)
    return result.returncode == 0

@app.command("test")
def task_test():
    """Run full test suite."""
    console.print(Panel("🧪 Running Tests", style="blue"))
    run_cmd("uv run pytest src/viperx/tests")

@app.command("build")
def task_build(clean: bool = True):
    """Clean dist/ and build package."""
    console.print(Panel("📦 Building Package", style="yellow"))
    
    dist_dir = PROJECT_ROOT / "dist"
    if clean and dist_dir.exists():
        console.print("[dim]Cleaning dist/...[/dim]")
        shutil.rmtree(dist_dir)
    
    run_cmd("uv build")

@app.command("site")
def task_site(deploy: bool = True):
    """Build and deploy docs."""
    console.print(Panel("📚 Documentation", style="magenta"))
    # Ensure mkdocs is installed
    run_cmd("uv run mkdocs build")
    if deploy:
        # mkdocs defaults to 'origin', but user has 'github'
        run_cmd("uv run mkdocs gh-deploy --force --remote-name github")

@app.command("git")
def task_git(msg: str = typer.Option(..., "--msg", "-m", help="Commit message")):
    """Git Add, Commit, Push (All Remotes)."""
    console.print(Panel("🐙 Git Sync", style="green"))
    
    if not msg:
        console.print("[red]Commit message required![/red]")
        raise typer.Exit(1)
        
    run_cmd("git add .")
    run_cmd("git commit -m '{}'".format(msg), exit_on_fail=False)
    
    console.print("[bold]Pushing to all remotes...[/bold]")
    run_cmd("git remote | xargs -n1 git push", exit_on_fail=False)

@app.command("pypi")
def task_pypi():
    """Publish to PyPI."""
    console.print(Panel("🚀 PyPI Publish", style="red"))
    run_cmd("uv publish")

@app.command("all")
def task_all(
    msg: str = typer.Option(..., "--msg", "-m", help="Commit message"),
    deploy_site: bool = True,
    publish: bool = True
):
    """
    ⚡ RUN EVERYTHING (The Full Release Cycle)
    """
    console.print(Panel(f"🦅 ViperX Release Sequence: {msg}", style="bold green"))
    
    # Check we are in root (simple check)
    if not (PROJECT_ROOT / "pyproject.toml").exists():
        console.print("[bold red]❌ Run this from project root![/bold red]")
        raise typer.Exit(1)

    task_test()
    task_build()
    
    if deploy_site:
        task_site(deploy=True)
    
    task_git(msg=msg)
    
    if publish:
        if typer.confirm("Ready to publish to PyPI?", default=True):
            task_pypi()
        else:
            console.print("[yellow]Skipping PyPI publish.[/yellow]")

if __name__ == "__main__":
    app()
