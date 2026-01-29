import pytest
from viperx.main import app

WORKSPACE_INIT_CONFIG = """
project:
  name: "pkg_test_ws"
workspace:
  packages: []
"""

def test_package_lifecycle(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Package Lifecycle (Add/Delete) via CLI.
    """
    # 1. Init Workspace
    with open("viperx.yaml", "w") as f:
        f.write(WORKSPACE_INIT_CONFIG)
    runner.invoke(app, ["config", "-c", "viperx.yaml"])
    
    root = temp_workspace / "pkg_test_ws"
    
    # 2. Add Package
    # We must run this INSIDE the workspace root
    import os
    os.chdir(root) 
    
    result = runner.invoke(app, [
        "package", "add", 
        "--name", "pkg_alpha",
        "--type", "classic"
    ])
    if result.exit_code != 0:
        print(result.stdout)
    assert result.exit_code == 0
    
    assert (root / "src" / "pkg_alpha").exists()
    assert (root / "src" / "pkg_alpha" / "__init__.py").exists()
    
    # 3. Delete Package
    result = runner.invoke(app, [
        "package", "delete",
        "--name", "pkg_alpha",
        "--force"
    ])
    assert result.exit_code == 0
    
    # Logic verification: Folder should be gone
    assert not (root / "src" / "pkg_alpha").exists()
