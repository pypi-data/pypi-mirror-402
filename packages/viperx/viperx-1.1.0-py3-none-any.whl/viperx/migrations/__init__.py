"""
ViperX Migration System

Handles project upgrades between ViperX versions.
"""

from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class Migration:
    """Base class for migrations."""
    
    from_version: str
    to_version: str
    description: str
    
    def check(self, project_root: Path) -> bool:
        """Check if migration is needed. Override in subclass."""
        return True
    
    def apply(self, project_root: Path, dry_run: bool = False) -> list[str]:
        """Apply migration. Returns list of changes. Override in subclass."""
        return []
    
    def __repr__(self):
        return f"Migration({self.from_version} → {self.to_version})"


# Migration Registry
MIGRATIONS: list[Migration] = []


def register(migration_class):
    """Decorator to register a migration."""
    MIGRATIONS.append(migration_class())
    return migration_class


def get_project_version(project_root: Path) -> Optional[str]:
    """Get ViperX version from viperx.yaml."""
    import yaml
    
    config_path = project_root / "viperx.yaml"
    if not config_path.exists():
        return None
    
    with open(config_path) as f:
        try:
            data = yaml.safe_load(f)
            return data.get("viperx_version")
        except yaml.YAMLError:
            return None


def set_project_version(project_root: Path, version: str):
    """Set ViperX version in viperx.yaml."""
    import yaml
    
    config_path = project_root / "viperx.yaml"
    if not config_path.exists():
        return
    
    with open(config_path) as f:
        content = f.read()
    
    # Check if viperx_version exists
    if "viperx_version:" in content:
        # Replace existing
        import re
        content = re.sub(
            r'^viperx_version:.*$',
            f'viperx_version: "{version}"',
            content,
            flags=re.MULTILINE
        )
    else:
        # Add at top after first line
        lines = content.splitlines()
        lines.insert(1, f'viperx_version: "{version}"')
        content = "\n".join(lines)
    
    with open(config_path, "w") as f:
        f.write(content)


def get_applicable_migrations(from_version: Optional[str], to_version: str) -> list[Migration]:
    """Get list of migrations to apply."""
    # Sort migrations by from_version
    sorted_migrations = sorted(MIGRATIONS, key=lambda m: m.from_version)
    
    applicable = []
    for m in sorted_migrations:
        # If no from_version, apply all migrations up to to_version
        if from_version is None:
            if m.to_version <= to_version:
                applicable.append(m)
        else:
            # Apply migrations that are newer than current version
            if m.from_version >= from_version and m.to_version <= to_version:
                applicable.append(m)
    
    return applicable


def run_migrations(project_root: Path, to_version: str, dry_run: bool = False) -> list[str]:
    """Run all applicable migrations."""
    current = get_project_version(project_root)
    migrations = get_applicable_migrations(current, to_version)
    
    all_changes = []
    
    for m in migrations:
        if m.check(project_root):
            changes = m.apply(project_root, dry_run)
            all_changes.extend(changes)
            
            if not dry_run:
                set_project_version(project_root, m.to_version)
    
    return all_changes
