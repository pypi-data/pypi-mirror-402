"""
Example migration: 1.0.0 to 1.0.1 (No-op, just demonstrates the pattern)
"""

from pathlib import Path
from viperx.migrations import Migration, register


@register
class Migration_1_0_0_to_1_0_1(Migration):
    """No-op migration for version tracking."""
    
    from_version = "1.0.0"
    to_version = "1.0.1"
    description = "Test reorganization (no file changes needed)"
    
    def check(self, project_root: Path) -> bool:
        # Always applicable for version tracking
        return True
    
    def apply(self, project_root: Path, dry_run: bool = False) -> list[str]:
        # No actual changes needed
        return [f"Updated viperx_version to {self.to_version}"]


@register
class Migration_1_0_1_to_1_0_2(Migration):
    """Add viperx_version field if missing."""
    
    from_version = "1.0.1"
    to_version = "1.0.2"
    description = "Add viperx init alias support (no file changes needed)"
    
    def check(self, project_root: Path) -> bool:
        return True
    
    def apply(self, project_root: Path, dry_run: bool = False) -> list[str]:
        return [f"Updated viperx_version to {self.to_version}"]
