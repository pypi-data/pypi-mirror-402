import pytest
from viperx.main import app

INITIAL_WORKSPACE_CONFIG = """
project:
  name: "ws_deletion"
workspace:
  packages:
    - name: "pkg_a"
    - name: "pkg_b"
"""

REDUCED_WORKSPACE_CONFIG = """
project:
  name: "ws_deletion"
workspace:
  packages:
    - name: "pkg_a"
"""

def test_deletion_warning_package(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Package Deletion Detection:
    1. Init workspace with pkg_a and pkg_b
    2. Remove pkg_b from config
    3. Verify: pkg_b folder STILL exists (Safe Mode)
    4. Verify: Deletion warning in report
    """
    # 1. Init with both packages
    with open("viperx.yaml", "w") as f:
        f.write(INITIAL_WORKSPACE_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "ws_deletion"
    assert (root / "src" / "pkg_a").exists()
    assert (root / "src" / "pkg_b").exists()
    
    # 2. Remove pkg_b from config
    with open("viperx.yaml", "w") as f:
        f.write(REDUCED_WORKSPACE_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    # 3. Verify: pkg_b folder STILL exists (ViperX doesn't delete)
    assert (root / "src" / "pkg_b").exists()
    
    # 4. Verify: Deletion warning in report
    assert "pkg_b" in result.stdout
    assert "missing from config" in result.stdout or "Deletion" in result.stdout

def test_feature_disable_warning(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Feature Disable Detection:
    1. Init with use_tests: true
    2. Update to use_tests: false
    3. Verify: tests/ folder STILL exists (Safe Mode)
    4. Verify: Conflict/Warning reported
    """
    INITIAL_CONFIG = """
project:
  name: "feature_test"
settings:
  use_tests: true
"""
    
    UPDATED_CONFIG = """
project:
  name: "feature_test"
settings:
  use_tests: false
"""
    
    # 1. Init
    with open("viperx.yaml", "w") as f:
        f.write(INITIAL_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "feature_test"
    tests_dir = root / "src" / "feature_test" / "tests"
    assert tests_dir.exists()
    
    # 2. Disable tests
    with open("viperx.yaml", "w") as f:
        f.write(UPDATED_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    # 3. Verify: tests/ STILL exists
    assert tests_dir.exists()
    
    # 4. Verify: Conflict reported
    assert "use_tests=False" in result.stdout or "tests" in result.stdout.lower()
