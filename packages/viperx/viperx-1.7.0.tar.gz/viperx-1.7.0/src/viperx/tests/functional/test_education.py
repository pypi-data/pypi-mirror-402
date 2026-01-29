
import json
from pathlib import Path
from typer.testing import CliRunner
from unittest import mock
import pytest

from viperx.main import app
from viperx.constants import USER_CONFIG_DIR

runner = CliRunner()

@pytest.fixture
def clean_settings(tmp_path):
    """
    Mock the USER_CONFIG_DIR to a temporary path to avoid messing with 
    the user's actual settings during tests.
    """
    # We need to patch the SETTINGS_FILE in settings.py
    # Since settings.py is already imported in main.py, we patch 'viperx.settings.SETTINGS_FILE'
    
    with mock.patch("viperx.settings.USER_CONFIG_DIR", tmp_path), \
         mock.patch("viperx.settings.SETTINGS_FILE", tmp_path / "settings.json"):
        yield tmp_path

def test_learn_command_listing():
    """Test 'viperx learn' lists topics."""
    result = runner.invoke(app, ["learn"])
    assert result.exit_code == 0
    assert "ViperX Learning Hub" in result.stdout
    assert "packaging" in result.stdout
    assert "uv" in result.stdout

def test_learn_command_topic():
    """Test 'viperx learn uv' shows content."""
    result = runner.invoke(app, ["learn", "uv"])
    assert result.exit_code == 0
    assert "Why uv?" in result.stdout
    assert "ViperX Academy: uv" in result.stdout

def test_learn_command_invalid():
    """Test 'viperx learn potato' shows error."""
    result = runner.invoke(app, ["learn", "potato"])
    assert result.exit_code == 0  # It prints error but doesn't crash
    # Checking simpler partial match or stripped
    from rich.console import Console
    # Rich prints to stdout with color codes. We can just check for 'potato' and 'not found' separately
    # or regex match.
    assert "potato" in result.stdout
    assert "not found" in result.stdout

def test_explain_persistence_toggle(clean_settings):
    """Test valid activate/deactivate flow."""
    settings_file = clean_settings / "settings.json"
    
    # 1. Activate
    result = runner.invoke(app, ["explain", "--activate"])
    assert result.exit_code == 0
    assert "Explain Mode ACTIVATED" in result.stdout
    
    # Verify file content
    assert settings_file.exists()
    data = json.loads(settings_file.read_text())
    assert data["explain_mode"] is True
    
    # 2. Deactivate
    result = runner.invoke(app, ["explain", "--deactivate"])
    assert result.exit_code == 0
    assert "Explain Mode DEACTIVATED" in result.stdout
    
    data = json.loads(settings_file.read_text())
    assert data["explain_mode"] is False

def test_explain_status(clean_settings):
    """Test status display."""
    result = runner.invoke(app, ["explain"])
    assert result.exit_code == 0
    assert "Explain Mode Status:" in result.stdout
    assert "ACTIVE" in result.stdout

def test_explain_conflict(clean_settings):
    """Test cannot activate and deactivate simultaneously."""
    result = runner.invoke(app, ["explain", "-a", "-d"])
    assert result.exit_code == 1
    assert "Cannot activate and deactivate" in result.stdout

def test_explain_impact_on_command(clean_settings, tmp_path):
    """Test that active explain mode affects other commands."""
    
    # 1. Activate Mode
    runner.invoke(app, ["explain", "--activate"])
    
    # 2. Run config update (requires a mock project)
    project_root = tmp_path / "dummy_proj"
    project_root.mkdir()
    (project_root / "pyproject.toml").write_text('[project]\nname="dummy"')
    
    with mock.patch("pathlib.Path.cwd", return_value=project_root):
        result = runner.invoke(app, ["config", "update"])
        
    assert result.exit_code == 0
    # Should see the Explain panel title we injected in ConfigScanner
    assert "🎓 Explain: Config Update" in result.stdout
