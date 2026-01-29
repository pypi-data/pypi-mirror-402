from viperx.main import app

OVERRIDES_CONFIG = """
project:
  name: "ws-overrides"

workspace:
  packages:
    - name: "pkg_rich"
      use_config: true
      use_env: true
      
    - name: "pkg_lean"
      use_config: false
      use_env: false
"""

def test_workspace_overrides(runner, temp_workspace, mock_git_config, mock_builder_check):
    with open("viperx.yaml", "w") as f:
        f.write(OVERRIDES_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    if result.exit_code != 0:
        print("STDOUT:", result.stdout)
    assert result.exit_code == 0
    
    root = temp_workspace / "ws_overrides"
    
    # Check pkg_rich
    pkg_rich = root / "src" / "pkg_rich"
    assert pkg_rich.exists()
    assert (pkg_rich / "config.py").exists()
    assert (pkg_rich / ".env").exists()
    
    # Verify Content (Init should import config)
    init_rich = (pkg_rich / "__init__.py").read_text()
    assert "from .config import SETTINGS" in init_rich
    
    # Check pkg_lean
    pkg_lean = root / "src" / "pkg_lean"
    assert pkg_lean.exists()
    assert not (pkg_lean / "config.py").exists()
    assert not (pkg_lean / ".env").exists()
    
    # Verify Content (Init should NOT import config)
    init_lean = (pkg_lean / "__init__.py").read_text()
    assert "from .config import SETTINGS" not in init_lean
    
    # Check Smart Test Config (Root pyproject)
    pyproject = (root / "pyproject.toml").read_text()
    
    # Expect pkg_rich (Default use_tests=True via inheritance/template logic? 
    # Wait, workspace config iterates packages.
    # In OVERRIDES_CONFIG, use_tests isn't specified, defaults to True in ProjectGenerator?
    # No, ConfigEngine passes settings_conf.get("use_tests", True).
    # But for individual packages? ConfigEngine line 254: p_tests = pkg.get("use_tests", settings_conf...
    # In OVERRIDES_CONFIG:
    # pkg_rich: use_env=True, use_config=True. use_tests -> Default (True)
    # pkg_lean: use_env=False, use_config=False. use_tests -> Default (True)
    # So BOTH should be in testpaths?
    # Let's verify what we want. Usually explicit override is better.
    # Let's update config to be explicit for test clarity.
    
    assert '"src/pkg_rich/tests"' in pyproject
    assert '"src/pkg_lean/tests"' in pyproject
