from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from viperx.constants import TEMPLATES_DIR, USER_TEMPLATES_DIR
import shutil
import tempfile
import subprocess

console = Console()

class TemplateManager:
    """
    Manages ViperX templates (Listing, Ejection, installation).
    Follows the 'Freedom' philosophy: User templates > Internal templates.
    """
    
    def __init__(self):
        self.user_dir = USER_TEMPLATES_DIR
        self.internal_dir = TEMPLATES_DIR

    def list_templates(self):
        """Show available templates and their source (User vs System)."""
        table = Table(title="🦅 ViperX Templates", border_style="blue")
        table.add_column("Template File", style="cyan")
        table.add_column("Source", style="bold")
        table.add_column("Status", style="dim")

        # Get all internal templates
        internal_files = {f.name for f in self.internal_dir.glob("*.j2")}
        user_files = set()
        if self.user_dir.exists():
            user_files = {f.name for f in self.user_dir.glob("*.j2")}

        all_files = sorted(internal_files | user_files)

        for f in all_files:
            if f in user_files:
                source = "[green]User Override 🦅[/green]"
                status = f"~/.config/viperx/templates/{f}"
            else:
                source = "[dim]System Default[/dim]"
                status = "Internal"
            
            table.add_row(f, source, status)

        console.print(table)
        console.print(f"\n[dim]User templates location: {self.user_dir}[/dim]")

    def eject_templates(self, force: bool = False):
        """Copy all internal templates to user directory."""
        if not self.user_dir.exists():
            self.user_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]Created {self.user_dir}[/green]")

        internal_files = list(self.internal_dir.glob("*.j2"))
        
        for file in internal_files:
            target = self.user_dir / file.name
            if target.exists() and not force:
                console.print(f"[yellow]Skipped {file.name} (Exists). Use --force to overwrite.[/yellow]")
                continue
            
            shutil.copy2(file, target)
            console.print(f"Copied [cyan]{file.name}[/cyan]")
            
        console.print(Panel("✅ Templates Ejected! You can now edit them freely.", border_style="green"))

    def add_template_pack(self, url: str):
        """
        Download templates from a git repository.
        Strategies:
        1. Clone to temp dir.
        2. Find all .j2 files.
        3. Copy them to USER_TEMPLATES_DIR (flattened).
        """
        console.print(f"[blue]Fetching templates from {url}...[/blue]")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", url, temp_dir],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                console.print(f"[bold red]Error:[/bold red] Failed to clone {url}")
                return

            # Find .j2 files
            temp_path = Path(temp_dir)
            j2_files = list(temp_path.rglob("*.j2"))
            
            if not j2_files:
                console.print("[yellow]No .j2 templates found in this repository.[/yellow]")
                return
                
            if not self.user_dir.exists():
                self.user_dir.mkdir(parents=True, exist_ok=True)

            count = 0
            for j2 in j2_files:
                target = self.user_dir / j2.name
                shutil.copy2(j2, target)
                console.print(f"Installed [cyan]{j2.name}[/cyan]")
                count += 1
                
            console.print(f"[bold green]Successfully installed {count} templates![/bold green]")
