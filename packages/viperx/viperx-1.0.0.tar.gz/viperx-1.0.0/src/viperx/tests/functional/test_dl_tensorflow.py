import pytest
from viperx.main import app

DL_TENSORFLOW_CONFIG = """
project:
  name: "tf_proj"
settings:
  type: "dl"
  framework: "tensorflow"
"""

def test_dl_tensorflow(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test DL Project with TensorFlow Framework:
    - Verify tensorflow dependencies in pyproject.toml
    - Verify NO torch dependencies
    - Verify notebooks/ and data/ exist
    """
    with open("viperx.yaml", "w") as f:
        f.write(DL_TENSORFLOW_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "tf_proj"
    assert root.exists()
    
    # Check Structure (ML/DL Layout)
    assert (root / "notebooks").exists()
    assert (root / "data").exists()
    
    # Check Dependencies
    pyproject = (root / "pyproject.toml").read_text()
    
    # TensorFlow Dependencies MUST be present
    assert "tensorflow>=" in pyproject
    # Keras is typically bundled with TF now, but we might add it separately
    # assert "keras>=" in pyproject  # Optional, depends on template
    
    # PyTorch Dependencies MUST NOT be present
    assert "torch>=" not in pyproject
    assert "torchvision>=" not in pyproject
    
    # Terminal Log Check
    assert "Project tf_proj created" in result.stdout
