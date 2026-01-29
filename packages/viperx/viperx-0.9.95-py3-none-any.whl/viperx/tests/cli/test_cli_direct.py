import pytest
from viperx.main import app

def test_cli_direct_classic(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Creating Project via CLI Flags (No config).
    command: viperx config -n cli_classic -t classic
    """
    result = runner.invoke(app, [
        "config", 
        "--name", "cli_classic",
        "--type", "classic",
        "--no-env"
    ])
    assert result.exit_code == 0
    
    root = temp_workspace / "cli_classic"
    assert root.exists()
    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "cli_classic" / "main.py").exists()
    # Expect NO .env
    assert not (root / ".env").exists()
    
def test_cli_direct_ml(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Creating ML Project via CLI Flags.
    """
    result = runner.invoke(app, [
        "config", 
        "--name", "cli_ml", 
        "--type", "ml",
        "--env"
    ])
    assert result.exit_code == 0
    
    root = temp_workspace / "cli_ml"
    
    # Check ML Structure
    assert (root / "notebooks").exists()
    assert (root / "data").exists() # Should pass now
    
    # Check .env (Classic/ML root behavior)
    # import os
    # print(f"\\nDEBUG: {root} contents:")
    # for r, d, f in os.walk(root):
    #     print(r, f)
        
    assert (root / ".env").exists()
