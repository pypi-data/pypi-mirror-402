import pytest
from viperx.main import app

CUSTOM_CONFIG = """
project:
  name: "custom-proj"
  builder: "hatch"
  license: "GPLv3"

settings:
  type: "ml"
  use_config: false
  use_env: true
  use_tests: false
"""

def test_classic_custom(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Verify that custom configuration yields the expected structure.
    Checks: Hatch builder, GPLv3, ML structure, Config Disabled, Tests Disabled.
    """
    with open("viperx.yaml", "w") as f:
        f.write(CUSTOM_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    if result.exit_code != 0:
        print("STDOUT:", result.stdout)
    assert result.exit_code == 0
    
    project_root = temp_workspace / "custom_proj"
    assert project_root.exists()
    
    # Check Structure (ML Layout)
    # custom_proj/
    #   notebooks/ (ML Feature)
    #   src/custom_proj/
    #     .env (Enabled)
    #     config.py (Disabled)
    #     tests/ (Disabled)
    
    assert (project_root / "notebooks").exists()
    
    pkg_dir = project_root / "src" / "custom_proj"
    assert pkg_dir.exists()
    assert (pkg_dir / ".env").exists()
    assert not (pkg_dir / "config.py").exists()
    assert not (pkg_dir / "tests").exists()
    
    # Check PyProject (Builder: Hatch)
    pyproject = (project_root / "pyproject.toml").read_text()
    assert 'build-backend = "hatchling.build"' in pyproject
    assert 'requires = ["hatchling"]' in pyproject
    
    # Check License (GPLv3)
    license_text = (project_root / "LICENSE").read_text()
    assert "GNU GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3" in license_text
