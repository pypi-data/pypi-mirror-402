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

# --- License Change Detection Tests ---

INITIAL_MIT_CONFIG = """
project:
  name: "license_test"
  license: "MIT"
"""

UPDATED_APACHE_CONFIG = """
project:
  name: "license_test"
  license: "Apache-2.0"
"""

def test_license_change_warning(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test License Change Detection:
    1. Init with MIT
    2. Update config to Apache-2.0
    3. Verify: License file NOT overwritten, manual check reported
    """
    # 1. Init with MIT
    with open("viperx.yaml", "w") as f:
        f.write(INITIAL_MIT_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "license_test"
    license_text = (root / "LICENSE").read_text()
    assert "MIT License" in license_text
    
    # 2. Change to Apache-2.0
    with open("viperx.yaml", "w") as f:
        f.write(UPDATED_APACHE_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    # 3. Verify: LICENSE file should STILL be MIT (Safe Mode)
    license_text_after = (root / "LICENSE").read_text()
    assert "MIT License" in license_text_after
    
    # 4. Verify: Manual check reported
    # The update report should mention license change
    assert "license" in result.stdout.lower() or "License" in result.stdout
