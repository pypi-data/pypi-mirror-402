import pytest
from viperx.main import app

# This test verifies that the 'hatch' builder works correctly (alternative to default 'uv')
# This test verifies that the 'hatch' builder works correctly
HATCH_CONFIG = """
project:
  name: "hatch_proj"
  builder: "hatch"
"""

def test_builder_hatch(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Hatch Builder (Alternative to default uv):
    - Verify build-backend = "hatchling.build"
    - Verify requires = ["hatchling"]
    """
    with open("viperx.yaml", "w") as f:
        f.write(HATCH_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "hatch_proj"
    assert root.exists()
    
    # Check pyproject.toml Build System
    pyproject = (root / "pyproject.toml").read_text()
    assert 'build-backend = "hatchling.build"' in pyproject
    assert 'requires = ["hatchling"]' in pyproject
    
    # Terminal Log
    assert "Project hatch_proj created" in result.stdout
