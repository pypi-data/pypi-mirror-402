import pytest
from viperx.main import app

CONTENT_CONFIG = """
project:
  name: "content_check"
  description: "A project for content verification"
"""

def test_gitignore_content(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test .gitignore Content:
    - Should contain .env, __pycache__, dist/, .venv/
    """
    with open("viperx.yaml", "w") as f:
        f.write(CONTENT_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "content_check"
    gitignore = (root / ".gitignore").read_text()
    
    assert ".env" in gitignore
    assert "__pycache__" in gitignore
    assert "dist/" in gitignore
    assert ".venv" in gitignore

def test_readme_content(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test README.md Content:
    - Should contain project name
    - Should contain description
    - Should contain installation section
    """
    with open("viperx.yaml", "w") as f:
        f.write(CONTENT_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "content_check"
    readme = (root / "README.md").read_text()
    
    # Project Name
    assert "content_check" in readme or "content-check" in readme
    
    # Description
    assert "A project for content verification" in readme
    
    # Installation Section (should mention uv or pip)
    assert "uv" in readme.lower() or "pip" in readme.lower() or "install" in readme.lower()

def test_main_py_content(runner, temp_workspace, mock_git_config, mock_builder_check):
    """
    Test main.py Content:
    - Should contain greeting with project name
    """
    with open("viperx.yaml", "w") as f:
        f.write(CONTENT_CONFIG)
        
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code == 0
    
    root = temp_workspace / "content_check"
    main_py = (root / "src" / "content_check" / "main.py").read_text()
    
    # Greeting
    assert "Hi from content-check" in main_py or "content_check" in main_py
