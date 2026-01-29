import pytest
from pathlib import Path
from viperx.main import app

MINIMAL_CONFIG = """
project:
  name: "classic-default"
"""

def test_classic_defaults(runner, temp_workspace, mock_git_config):
    """
    Verify that a minimal configuration yields the expected default structure.
    """
    with open("viperx.yaml", "w") as f:
        f.write(MINIMAL_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    if result.exit_code != 0:
        print("STDOUT:", result.stdout)
    assert result.exit_code == 0
    
    project_root = temp_workspace / "classic_default"
    if not project_root.exists():
        print("STDOUT (Success Exit but Dir Missing):", result.stdout)
    assert project_root.exists()
    
    # Check Structure (Flat Layout for Root)
    # Expected:
    # classic-default/
    #   src/
    #     classic_default/
    #       __init__.py
    #       config.py (Default: True)
    #       main.py
    #       .env (Default: False ?? No, settings defaults: use_env=False in Engine? 
    #             Let's check constants/defaults.
    #             Code says: defaults are pulled from get(x, DEFAULT).
    #             src/viperx/config_engine.py line 145: use_env default is False.
    #             use_config default is True.
    #             use_tests default is True.
    
    pkg_dir = project_root / "src" / "classic_default"
    assert pkg_dir.exists()
    assert (pkg_dir / "__init__.py").exists()
    assert (pkg_dir / "config.py").exists()
    assert (pkg_dir / "main.py").exists()
    assert not (pkg_dir / ".env").exists() # Default use_env is False
    
    # Check Root Files
    assert (project_root / "pyproject.toml").exists()
    assert (project_root / "README.md").exists()
    assert (project_root / "LICENSE").exists()
    
    # Check Metadata Defaults
    pyproject = (project_root / "pyproject.toml").read_text()
    assert 'name = "classic-default"' in pyproject
    # Author should be mocked value
    assert 'name = "Test User"' in pyproject
    assert 'email = "test@example.com"' in pyproject
    
    # Check License Default (MIT)
    license_text = (project_root / "LICENSE").read_text()
    assert "MIT License" in license_text
    
    # Check Tests Default (True)
    tests_dir = project_root / "src" / "classic_default" / "tests"
    assert tests_dir.exists()
    assert (tests_dir / "__init__.py").exists()
