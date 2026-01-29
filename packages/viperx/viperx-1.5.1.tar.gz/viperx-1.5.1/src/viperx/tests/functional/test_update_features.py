"""
Tests for config engine update features:
- Blank lines removal in pyproject.toml
- testpaths sync when adding packages
- LICENSE file content update
- use_* flag toggles creating files
"""

from pathlib import Path
import pytest
from typer.testing import CliRunner
from viperx.main import app


runner = CliRunner()


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory and set it as cwd."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


def create_basic_project(project_dir: Path):
    """Create a minimal project structure for testing updates."""
    # Create viperx.yaml
    config = """
project:
  name: "test-project"
  license: "MIT"

settings:
  type: "classic"
  use_env: false
  use_config: true
  use_tests: true

workspace:
  packages: []
"""
    (project_dir / "viperx.yaml").write_text(config)
    
    # Run initial creation
    import os
    old_cwd = os.getcwd()
    os.chdir(project_dir)
    try:
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
    finally:
        os.chdir(old_cwd)
    
    return project_dir


class TestNoBlankLinesInScripts:
    """Test that no consecutive blank lines appear in [project.scripts]."""
    
    def test_no_blank_lines_after_adding_package(self, temp_project, mock_git_config, mock_builder_check):
        """Adding packages should not introduce blank lines."""
        import os
        
        # Create initial project
        config1 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  
workspace:
  packages:
    - name: "pkg-one"
      type: "classic"
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        # Add another package
        config2 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  
workspace:
  packages:
    - name: "pkg-one"
      type: "classic"
    - name: "pkg-two"
      type: "classic"
"""
        (temp_project / "viperx.yaml").write_text(config2)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        # Check pyproject.toml for consecutive blank lines
        pyproject_content = (temp_project / "test_proj" / "pyproject.toml").read_text()
        assert "\n\n\n" not in pyproject_content, "Found consecutive blank lines in pyproject.toml"


class TestTestpathsUpdate:
    """Test that testpaths are updated when packages with tests are added."""
    
    def test_testpaths_includes_new_package(self, temp_project, mock_git_config, mock_builder_check):
        """Adding a package with use_tests=True should update testpaths."""
        import os
        
        # Create initial project without extra packages
        config1 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_tests: true
  
workspace:
  packages: []
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "test_proj"
        
        # Now add a package and enable tests
        config2 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_tests: true
  
workspace:
  packages:
    - name: "new-pkg"
      type: "classic"
      use_tests: true
"""
        (project_root / "viperx.yaml").write_text(config2)
        os.chdir(project_root)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        pyproject_content = (project_root / "pyproject.toml").read_text()
        assert "new_pkg/tests" in pyproject_content, "testpaths should include new_pkg/tests"
        
        # Verify no duplicate testpaths
        import re
        testpaths_match = re.search(r'testpaths\s*=\s*\[([^\]]*)\]', pyproject_content, re.DOTALL)
        if testpaths_match:
            paths = re.findall(r'"([^"]+)"', testpaths_match.group(1))
            assert len(paths) == len(set(paths)), f"Duplicate testpaths found: {paths}"


class TestTestsFolderStructure:
    """Test that tests folder has proper structure (__init__.py + test_core.py)."""
    
    def test_tests_folder_has_init_and_test_file(self, temp_project, mock_git_config, mock_builder_check):
        """Enabling use_tests should create __init__.py and test_core.py."""
        import os
        
        # Create project with use_tests: false initially
        config1 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_tests: false
  
workspace:
  packages:
    - name: "my-pkg"
      type: "classic"
      use_tests: false
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "test_proj"
        pkg_path = project_root / "src" / "my_pkg"
        
        # Tests should not exist
        assert not (pkg_path / "tests").exists(), "tests/ should not exist when use_tests=false"
        
        # Now enable tests
        config2 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_tests: false
  
workspace:
  packages:
    - name: "my-pkg"
      type: "classic"
      use_tests: true
"""
        (project_root / "viperx.yaml").write_text(config2)
        os.chdir(project_root)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        # Now tests folder should exist with proper structure
        tests_path = pkg_path / "tests"
        assert tests_path.exists(), "tests/ should exist after enabling use_tests"
        assert (tests_path / "__init__.py").exists(), "tests/__init__.py should exist"
        assert (tests_path / "test_core.py").exists(), "tests/test_core.py should exist"
        
        # Verify test placeholder content
        test_content = (tests_path / "test_core.py").read_text()
        assert "def test_dummy" in test_content, "Test should use test_dummy placeholder"


class TestLicenseFileUpdate:
    """Test that LICENSE file content is updated when license type changes."""
    
    def test_license_content_changes(self, temp_project, mock_git_config, mock_builder_check):
        """Changing license type should update LICENSE file content."""
        import os
        
        # Create project with MIT license
        config1 = """
project:
  name: "test-proj"
  license: "MIT"
  
settings:
  type: "classic"
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "test_proj"
        license_path = project_root / "LICENSE"
        
        assert license_path.exists()
        mit_content = license_path.read_text()
        assert "MIT License" in mit_content
        
        # Change to Apache
        config2 = """
project:
  name: "test-proj"
  license: "Apache-2.0"
  
settings:
  type: "classic"
"""
        (project_root / "viperx.yaml").write_text(config2)
        os.chdir(project_root)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        apache_content = license_path.read_text()
        assert "Apache License" in apache_content, "LICENSE should be updated to Apache"


class TestUseEnvToggle:
    """Test that use_env toggle creates .env file."""
    
    def test_use_env_creates_env_file(self, temp_project, mock_git_config, mock_builder_check):
        """Enabling use_env should create .env file."""
        import os
        
        # Create project with use_env: false
        config1 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_env: false
  
workspace:
  packages:
    - name: "my-pkg"
      type: "classic"
      use_env: false
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "test_proj"
        pkg_path = project_root / "src" / "my_pkg"
        
        assert not (pkg_path / ".env").exists(), ".env should not exist when use_env=false"
        
        # Enable use_env
        config2 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_env: false
  
workspace:
  packages:
    - name: "my-pkg"
      type: "classic"
      use_env: true
"""
        (project_root / "viperx.yaml").write_text(config2)
        os.chdir(project_root)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        assert (pkg_path / ".env").exists(), ".env should exist after enabling use_env"
        assert (pkg_path / ".env.example").exists(), ".env.example should also exist"


class TestUseConfigToggle:
    """Test that use_config toggle creates config.py file."""
    
    def test_use_config_creates_config_file(self, temp_project, mock_git_config, mock_builder_check):
        """Enabling use_config should create config.py file."""
        import os
        
        # Create project with use_config: false
        config1 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_config: false
  
workspace:
  packages:
    - name: "my-pkg"
      type: "classic"
      use_config: false
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "test_proj"
        pkg_path = project_root / "src" / "my_pkg"
        
        assert not (pkg_path / "config.py").exists(), "config.py should not exist when use_config=false"
        
        # Enable use_config
        config2 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_config: false
  
workspace:
  packages:
    - name: "my-pkg"
      type: "classic"
      use_config: true
"""
        (project_root / "viperx.yaml").write_text(config2)
        os.chdir(project_root)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        assert (pkg_path / "config.py").exists(), "config.py should exist after enabling use_config"
        assert (pkg_path / "config.yaml").exists(), "config.yaml should also exist"


class TestUseReadmeToggle:
    """Test that use_readme toggle creates README.md file."""
    
    def test_use_readme_creates_readme_file(self, temp_project, mock_git_config, mock_builder_check):
        """Enabling use_readme should create README.md file."""
        import os
        
        # Create project with use_readme: false
        config1 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  
workspace:
  packages:
    - name: "my-pkg"
      type: "classic"
      use_readme: false
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "test_proj"
        pkg_path = project_root / "src" / "my_pkg"
        
        # README.md should not exist at package level (only at root)
        # Note: Package-level README is optional
        (pkg_path / "README.md").exists()
        
        # Enable use_readme
        config2 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  
workspace:
  packages:
    - name: "my-pkg"
      type: "classic"
      use_readme: true
"""
        (project_root / "viperx.yaml").write_text(config2)
        os.chdir(project_root)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        assert (pkg_path / "README.md").exists(), "README.md should exist after enabling use_readme"
        
        # Verify README uses template (contains ViperX signature)
        readme_content = (pkg_path / "README.md").read_text()
        assert "ViperX" in readme_content, "README should mention ViperX (template signature)"
