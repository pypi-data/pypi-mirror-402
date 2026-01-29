import pytest
from viperx.main import app

ML_CONFIG = """
project:
  name: "ml_proj"
settings:
  type: "ml"
  use_env: true
"""

DL_CONFIG = """
project:
  name: "dl_proj"
settings:
  type: "dl"
  framework: "pytorch"
"""

def test_ml_scenarios(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test ML Project Generation:
    - Verify Notebooks folder
    - Verify ML dependencies
    """
    with open("viperx.yaml", "w") as f:
        f.write(ML_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "ml_proj"
    
    # Structure
    assert (root / "notebooks").exists()
    assert (root / "data").exists()
    
    # Dependencies (pyproject.toml)
    pyproject = (root / "pyproject.toml").read_text()
    assert "numpy>=" in pyproject
    assert "pandas>=" in pyproject
    assert "seaborn>=" in pyproject
    
def test_dl_scenarios(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test DL Project Generation (PyTorch):
    - Verify Torch dependencies
    """
    with open("viperx.yaml", "w") as f:
        f.write(DL_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "dl_proj"
    pyproject = (root / "pyproject.toml").read_text()
    
    assert "torch>=" in pyproject
    assert "torchvision>=" in pyproject
    
    # Verify Notebooks (Inherited from ML trait?)
    # DL usually also gets notebooks.
    # ConfigEngine logic: if p_type in [ML, DL] -> glob_is_ml_dl = True
    # If glob_is_ml_dl -> notebooks created?
    # Wait, ProjectGenerator handles notebooks creation?
    # Let's check logic: config_engine sets is_ml_dl in dependency_context.
    # ProjectGenerator uses this context for Dependencies.
    # What about folder structure? 
    # It's likely in ProjectGenerator.generate(). Default behavior for ML/DL logic.
    assert (root / "notebooks").exists()
