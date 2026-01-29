from viperx.main import app

WORKSPACE_CONFIG = """
project:
  name: "ws-root"

workspace:
  packages:
    - name: "pkg_core"
    - name: "pkg_utils"
"""

def test_workspace_structure(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Verify workspace Structure (Mono-Repo).
    Key check: Subpackages should NOT have pyproject.toml.
    """
    with open("viperx.yaml", "w") as f:
        f.write(WORKSPACE_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    if result.exit_code != 0:
        print("STDOUT:", result.stdout)
    assert result.exit_code == 0
    
    root = temp_workspace / "ws_root"
    assert root.exists()
    assert (root / "pyproject.toml").exists()
    
    # Check pkg_core
    core_pkg = root / "src" / "pkg_core"
    assert core_pkg.exists()
    assert (core_pkg / "__init__.py").exists()
    # CRITICAL: No pyproject.toml in subpackage
    assert not (core_pkg / "pyproject.toml").exists()
    
    # Check pkg_utils
    utils_pkg = root / "src" / "pkg_utils"
    assert utils_pkg.exists()
    assert (utils_pkg / "__init__.py").exists()
    assert not (utils_pkg / "pyproject.toml").exists()
    
    # Verify Imports logic implies defaults (use_config=True)
    assert (core_pkg / "config.py").exists()
