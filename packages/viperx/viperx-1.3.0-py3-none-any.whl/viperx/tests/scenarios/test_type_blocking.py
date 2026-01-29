"""
Tests for type change blocking and config scanning features.
"""

import os
import re
import pytest
from pathlib import Path
from typer.testing import CliRunner
from viperx.main import app


runner = CliRunner()


class TestTypeChangeBlocking:
    """Test that changing project type during update is blocked."""
    
    def test_type_change_blocked(self, temp_project, mock_git_config, mock_builder_check):
        """Changing type from classic to ml should be blocked."""
        import os
        
        # Create initial classic project
        config1 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "test_proj"
        
        # Now try to change type to ml
        config2 = """
project:
  name: "test-proj"
  
settings:
  type: "ml"
"""
        (project_root / "viperx.yaml").write_text(config2)
        os.chdir(project_root)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        
        # Should mention type change blocked
        assert "Type Change Blocked" in result.stdout or "blocked" in result.stdout.lower()
    
    def test_type_same_allowed(self, temp_project, mock_git_config, mock_builder_check):
        """Keeping same type should be allowed."""
        import os
        
        # Create initial classic project
        config1 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "test_proj"
        
        # Update with same type
        config2 = """
project:
  name: "test-proj"
  description: "Updated description"
  
settings:
  type: "classic"
"""
        (project_root / "viperx.yaml").write_text(config2)
        os.chdir(project_root)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        
        # Should succeed without blocking
        assert "Type Change Blocked" not in result.stdout


class TestReadmeActualFiles:
    """Test that README is generated based on actual files, not flags."""
    
    def test_readme_detects_actual_config(self, temp_project, mock_git_config, mock_builder_check):
        """README should show config section if config.py exists, regardless of flag."""
        import os
        
        # Create project with config
        config1 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_config: true
  
workspace:
  packages:
    - name: "my-pkg"
      use_config: true
      use_readme: false
"""
        (temp_project / "viperx.yaml").write_text(config1)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "test_proj"
        pkg_path = project_root / "src" / "my_pkg"
        
        # Verify config.py exists
        assert (pkg_path / "config.py").exists()
        
        # Now enable README with use_config: false (but config.py still exists)
        config2 = """
project:
  name: "test-proj"
  
settings:
  type: "classic"
  use_config: true
  
workspace:
  packages:
    - name: "my-pkg"
      use_config: false
      use_readme: true
"""
        (project_root / "viperx.yaml").write_text(config2)
        os.chdir(project_root)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        # README should exist and mention config (detected from actual file)
        readme_path = pkg_path / "README.md"
        assert readme_path.exists()
        readme_content = readme_path.read_text()
        assert "config" in readme_content.lower() or "Config" in readme_content


class TestConfigScanner:
    """Test the config scanner functionality."""
    
    def test_scanner_detects_packages(self, temp_project, mock_git_config, mock_builder_check):
        """Scanner should detect packages in src/ directory."""
        import os
        from viperx.config_scanner import ConfigScanner
        
        # Create a project
        config = """
project:
  name: "scan-test"
  
settings:
  type: "classic"
  
workspace:
  packages:
    - name: "pkg-a"
    - name: "pkg-b"
      use_tests: false
"""
        (temp_project / "viperx.yaml").write_text(config)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "scan_test"
        
        # Now scan
        scanner = ConfigScanner(project_root)
        scanned = scanner.scan()
        
        # Should detect packages
        package_names = [p["name"] for p in scanned.get("workspace", {}).get("packages", [])]
        assert "pkg_a" in package_names
        assert "pkg_b" in package_names
    
    def test_scanner_detects_features(self, temp_project, mock_git_config, mock_builder_check):
        """Scanner should detect use_config, use_tests based on actual files."""
        import os
        from viperx.config_scanner import ConfigScanner
        
        # Create a project with mixed features
        config = """
project:
  name: "feat-test"
  
settings:
  type: "classic"
  use_config: true
  use_tests: true
  
workspace:
  packages:
    - name: "with-config"
      use_config: true
      use_tests: false
    - name: "no-config"
      use_config: false
      use_tests: true
"""
        (temp_project / "viperx.yaml").write_text(config)
        
        os.chdir(temp_project)
        result = runner.invoke(app, ["config", "-c", "viperx.yaml"])
        assert result.exit_code == 0
        
        project_root = temp_project / "feat_test"
        scanner = ConfigScanner(project_root)
        scanned = scanner.scan()
        
        # Find packages
        pkgs = {p["name"]: p for p in scanned.get("workspace", {}).get("packages", [])}
        
        # with-config should have use_config=True
        assert pkgs.get("with_config", {}).get("use_config") == True
        # no-config should have use_config=False
        assert pkgs.get("no_config", {}).get("use_config") == False


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir
