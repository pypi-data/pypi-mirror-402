import pytest
from viperx.main import app

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
