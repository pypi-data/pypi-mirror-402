from viperx.main import app

# Test Constants
VALID_CONFIG = """
project:
  name: "valid-project"
settings:
  type: "classic"
"""

INVALID_BUILDER = """
project:
  name: "bad-builder"
  builder: "poetry" # Unsupported
"""

INVALID_LICENSE = """
project:
  name: "bad-license"
  license: "WTFPL" # Unsupported
"""

INVALID_TYPE = """
project:
  name: "bad-type"
settings:
  type: "mobile" # Unsupported
"""

def test_missing_config_file(runner, temp_workspace):
    """Ensure graceful failure when config file is missing."""
    result = runner.invoke(app, ["config", "-c", "missing.yaml"])
    assert result.exit_code != 0
    assert "not found" in result.stdout

def test_invalid_yaml_syntax(runner, temp_workspace):
    """Ensure graceful failure on broken YAML."""
    with open("broken.yaml", "w") as f:
        f.write("project: name: broken: [")
    
    result = runner.invoke(app, ["config", "-c", "broken.yaml"])
    assert result.exit_code != 0
    # Current implementation might show Yaml Error or validation error
    # Robustness check: It shouldn't crash with unhandled exception
    assert "Error" in result.stdout

def test_invalid_builder(runner, temp_workspace):
    """Ensure unsupported builder is rejected."""
    with open("viperx.yaml", "w") as f:
        f.write(INVALID_BUILDER)
    
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code != 0
    assert "Invalid Builder" in result.stdout or "builder" in result.stdout.lower()

def test_invalid_license(runner, temp_workspace):
    """Ensure unsupported license is rejected."""
    with open("viperx.yaml", "w") as f:
        f.write(INVALID_LICENSE)
    
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code != 0
    # ConfigEngine validates license? Or just passes it?
    # Phase 2 improvement: Strict License Check
    # If not implemented cleanly yet, this test might FAIL or PASS depending on logic.
    # Current logic allows fallback or might accept it. 
    # Let's verify if we enforce it. 
    # If not enforcing, this test documents need for improvement.

def test_invalid_project_type(runner, temp_workspace):
    """Ensure unsupported project type is rejected."""
    with open("viperx.yaml", "w") as f:
        f.write(INVALID_TYPE)
    
    result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
    assert result.exit_code != 0
    assert "Invalid Project Type" in result.stdout or "type" in result.stdout.lower()

def test_update_config_none_packages(tmp_path):
    """Regression test: Ensure update_config handles 'packages: None' gracefully (V1.5.1 Hotfix)."""
    from viperx.config_scanner import ConfigScanner
    scanner = ConfigScanner(tmp_path)
    
    # Existing config with None packages (simulating the bug)
    existing_config = {
        "project": {"name": "test"},
        "settings": {"type": "classic"},
        "workspace": {"packages": None} # This caused the crash
    }
    
    # Run update (should not crash)
    new_config, annotations = scanner.update_config(existing_config)
    
    # Verify normalization
    assert new_config["workspace"]["packages"] == []
