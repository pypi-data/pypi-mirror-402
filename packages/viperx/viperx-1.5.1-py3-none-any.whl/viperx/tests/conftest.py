import pytest
import os
from typer.testing import CliRunner

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_workspace(tmp_path):
    """
    Creates a temporary workspace directory and changes CWD to it.
    Cleans up after test.
    """
    # Create a dedicated temp directory for the test
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Store original CWD
    original_cwd = os.getcwd()
    
    # Switch to temp workspace
    os.chdir(workspace)
    
    yield workspace
    
    # Restore CWD
    os.chdir(original_cwd)

@pytest.fixture
def mock_git_config(mocker):
    """
    Mocks get_author_from_git to return predictable values.
    """
    # Patch where it is USED (core.py imports it)
    mock_auth = mocker.patch("viperx.core.get_author_from_git")
    mock_auth.return_value = ("Test User", "test@example.com")
    return mock_auth

@pytest.fixture
def mock_builder_check(mocker):
    """
    Mock check_builder_installed to always return True.
    """
    # Patch where it is DEFINED (local import in core __init__ picks this up)
    mock_check = mocker.patch("viperx.utils.check_builder_installed")
    mock_check.return_value = True
    return mock_check
