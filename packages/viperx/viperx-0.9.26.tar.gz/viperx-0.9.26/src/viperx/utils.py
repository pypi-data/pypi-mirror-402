import re
import shutil
from rich.console import Console

console = Console()

def check_uv_installed() -> bool:
    """Check if 'uv' is installed and accessible."""
    return shutil.which("uv") is not None

def sanitize_project_name(name: str) -> str:
    """
    Sanitize the project name to be a valid Python package name.
    Replaces hyphens with underscores and removes invalid characters.
    """
    # Replace - with _
    name = name.replace("-", "_")
    # Remove any characters that aren't alphanumerics or underscores
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    # Ensure it starts with a letter or underscore
    if not re.match(r"^[a-zA-Z_]", name):
        name = f"_{name}"
    return name.lower()

def validate_project_name(ctx, param, value):
    """
    Typer callback to validate project name.
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", value):
        from typer import BadParameter
        raise BadParameter("Project name must contain only letters, numbers, underscores, and hyphens.")
    return value

def check_builder_installed(builder: str) -> bool:
    """
    Check if the specified builder is installed.
    Uses shutil.which() for robust path detection.
    """
    return shutil.which(builder) is not None

def get_author_from_git() -> tuple[str, str]:
    """
    Attempt to get author name and email from git config.
    Returns (name, email) or defaults.
    """
    try:
        # Check if git is installed first
        if not shutil.which("git"):
             return "Nameless", "nameless@example.com"
             
        import git
        # Robust way using git command wrapper
        reader = git.Git().config
        name = reader("--global", "--get", "user.name")
        email = reader("--global", "--get", "user.email")
        
        # strip newlines if any
        return (name.strip() if name else "Nameless", 
                email.strip() if email else "nameless@example.com")
    except Exception:
        # Fallback if git call fails
        return "Nameless", "nameless@example.com"
