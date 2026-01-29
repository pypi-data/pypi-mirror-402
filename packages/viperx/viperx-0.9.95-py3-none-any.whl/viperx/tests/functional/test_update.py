import pytest
from viperx.main import app

INITIAL_CONFIG = """
project:
  name: "update_test"
settings:
  use_env: false
"""

UPDATED_CONFIG_ENABLE_ENV = """
project:
  name: "update_test"
settings:
  use_env: true
"""

UPDATED_CONFIG_DISABLE_ENV = """
project:
  name: "update_test"
settings:
  use_env: false
"""

def test_update_workflow(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test the Update Workflow:
    1. Init (No Env)
    2. Update (Enable Env) -> Should Create .env and Report Added
    3. Update (Disable Env) -> Should Warn and NOT delete .env
    """
    # 1. Initial State
    with open("viperx.yaml", "w") as f:
        f.write(INITIAL_CONFIG)
    
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    project_root = temp_workspace / "update_test"
    src_dir = project_root / "src" / "update_test"
    assert src_dir.exists()
    assert not (src_dir / ".env").exists()
    
    # 2. Update: Enable Env
    with open("viperx.yaml", "w") as f:
        f.write(UPDATED_CONFIG_ENABLE_ENV)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    if result.exit_code != 0:
        print(result.stdout)
    assert result.exit_code == 0
    
    # Debug: Print structure
    print("\nDEBUG STRUCTURE:")
    import os
    for root, dirs, files in os.walk(str(project_root)):
         print(root, files)
         
    # Check logic: Classic project puts .env in src/pkg (via check_feature in apply)?
    # Or root? 
    # Let's check where it expects it.
    
    # Logic: .env is in ROOT for Classic
    assert (project_root / ".env").exists()
    
    # 3. Update: Disable Env (Expect Conflict/Warning)
    with open("viperx.yaml", "w") as f:
        f.write(UPDATED_CONFIG_DISABLE_ENV)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    # Critical: File must STILL exist (ViperX is safe by default)
    assert (project_root / ".env").exists()
    
    # Verify the warning is in the output (Manual Check)
    # The output format is roughly: "Conflicts" ... "use_env=False but .env exists"
    assert "use_env=False but .env exists" in result.stdout
