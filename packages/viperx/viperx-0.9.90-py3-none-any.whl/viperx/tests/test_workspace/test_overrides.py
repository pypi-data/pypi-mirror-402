import pytest
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
