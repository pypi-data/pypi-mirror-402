import pytest
from viperx.main import app

def test_init_imperative_classic(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Pure Imperative Mode (No viperx.yaml):
    viperx config -n my_project (without config file)
    """
    result = runner.invoke(app, ["config", "-n", "imperative_proj"])
    assert result.exit_code == 0
    
    root = temp_workspace / "imperative_proj"
    assert root.exists()
    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "imperative_proj" / "main.py").exists()
    
    # viperx.yaml IS created when using config command (even imperative)
    # This is expected behavior - config command always creates viperx.yaml
    
    # Terminal Logs
    assert "Project imperative_proj created" in result.stdout

def test_init_imperative_ml_with_env(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Imperative Mode with ML Type and Env:
    viperx config -n ml_imp -t ml --env
    """
    result = runner.invoke(app, ["config", "-n", "ml_imp", "-t", "ml", "--env"])
    assert result.exit_code == 0
    
    root = temp_workspace / "ml_imp"
    
    # ML Structure
    assert (root / "notebooks").exists()
    assert (root / "data").exists()
    
    # .env in package (strict isolation)
    pkg_dir = root / "src" / "ml_imp"
    assert (pkg_dir / ".env").exists()

def test_init_imperative_dl_pytorch(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test Imperative Mode with DL Type:
    viperx config -n dl_imp -t dl -f pytorch
    """
    result = runner.invoke(app, ["config", "-n", "dl_imp", "-t", "dl", "-f", "pytorch"])
    assert result.exit_code == 0
    
    root = temp_workspace / "dl_imp"
    pyproject = (root / "pyproject.toml").read_text()
    
    # PyTorch dependencies
    assert "torch>=" in pyproject
    assert "notebooks" in [d.name for d in root.iterdir() if d.is_dir()]
