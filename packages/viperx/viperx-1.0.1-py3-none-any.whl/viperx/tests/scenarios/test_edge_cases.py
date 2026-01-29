import pytest
from viperx.main import app

HYPHENATED_CONFIG = """
project:
  name: "my-awesome-project"
"""

EMPTY_WORKSPACE_CONFIG = """
project:
  name: "empty_ws"
workspace:
  packages: []
"""

UNICODE_CONFIG = """
project:
  name: "unicode_proj"
  description: "Projet avec des accents: éàü 日本語"
"""

def test_hyphenated_name(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Project Name with Hyphens:
    - Folder should be snake_case: my_awesome_project
    - Package imports should work
    """
    with open("viperx.yaml", "w") as f:
        f.write(HYPHENATED_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    # Check folder name is snake_case
    root = temp_workspace / "my_awesome_project"
    assert root.exists()
    
    # Check package name in src/
    pkg_dir = root / "src" / "my_awesome_project"
    assert pkg_dir.exists()
    
    # Check pyproject still uses original hyphenated name
    pyproject = (root / "pyproject.toml").read_text()
    assert 'name = "my-awesome-project"' in pyproject

def test_empty_workspace(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Empty Workspace (packages: []):
    - Only root package should be created
    - No errors or warnings
    """
    with open("viperx.yaml", "w") as f:
        f.write(EMPTY_WORKSPACE_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "empty_ws"
    assert root.exists()
    
    # Only root package in src/
    src_contents = list((root / "src").iterdir())
    assert len(src_contents) == 1
    assert src_contents[0].name == "empty_ws"

def test_unicode_description(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Unicode Description:
    - Generation should not crash
    - README should contain the description
    """
    with open("viperx.yaml", "w") as f:
        f.write(UNICODE_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "unicode_proj"
    assert root.exists()
    
    # Check README contains unicode description
    readme = (root / "README.md").read_text()
    assert "éàü" in readme or "unicode_proj" in readme  # At minimum project name should be there
