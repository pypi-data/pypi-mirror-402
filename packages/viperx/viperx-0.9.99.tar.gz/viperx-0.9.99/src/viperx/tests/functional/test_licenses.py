import pytest
from viperx.main import app

APACHE_CONFIG = """
project:
  name: "apache_proj"
  license: "Apache-2.0"
"""

MIT_CONFIG = """
project:
  name: "mit_proj"
  license: "MIT"
"""

def test_license_apache(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Apache-2.0 License Generation:
    - Verify LICENSE file content contains Apache text
    - Verify pyproject.toml has correct license field
    """
    with open("viperx.yaml", "w") as f:
        f.write(APACHE_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "apache_proj"
    assert root.exists()
    
    # Check LICENSE File Content
    license_text = (root / "LICENSE").read_text()
    assert "Apache License" in license_text
    assert "Version 2.0" in license_text
    
    # Check pyproject.toml
    pyproject = (root / "pyproject.toml").read_text()
    assert 'license = { text = "Apache-2.0" }' in pyproject

def test_license_mit_explicit(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Explicit MIT License (to verify default behavior is consistent).
    """
    with open("viperx.yaml", "w") as f:
        f.write(MIT_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "mit_proj"
    license_text = (root / "LICENSE").read_text()
    assert "MIT License" in license_text
