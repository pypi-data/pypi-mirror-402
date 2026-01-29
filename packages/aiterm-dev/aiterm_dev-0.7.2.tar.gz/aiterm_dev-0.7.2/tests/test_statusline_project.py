"""Tests for StatusLine project context detection.

Tests project-specific context features including:
- Python environment detection (venv/conda/pyenv)
- Node.js version detection
- R package health checks
- Dependency status warnings
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from aiterm.statusline.segments import ProjectSegment
from aiterm.statusline.config import StatusLineConfig


class TestPythonEnvDetection:
    """Test Python environment detection."""

    @pytest.fixture
    def segment(self):
        config = StatusLineConfig()
        config.set('project.detect_python_env', True)
        return ProjectSegment(config)

    def test_detect_venv_with_version(self, segment, tmp_path):
        """Should detect venv and extract Python version."""
        # Create mock venv
        venv_dir = tmp_path / "venv" / "bin"
        venv_dir.mkdir(parents=True)
        python_bin = venv_dir / "python"
        python_bin.touch()

        # Mock Python version output
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Python 3.11.5\n"
            mock_run.return_value = mock_result

            result = segment._get_python_env(str(tmp_path))
            assert result == "venv: py3.11"

    def test_detect_venv_without_version(self, segment, tmp_path):
        """Should detect venv even without version."""
        venv_dir = tmp_path / "venv" / "bin"
        venv_dir.mkdir(parents=True)
        python_bin = venv_dir / "python"
        python_bin.touch()

        # Mock subprocess to fail (no version available)
        with patch('subprocess.run', side_effect=Exception("No version")):
            result = segment._get_python_env(str(tmp_path))
            assert result == "venv"

    def test_detect_dot_venv(self, segment, tmp_path):
        """Should detect .venv directory."""
        venv_dir = tmp_path / ".venv" / "bin"
        venv_dir.mkdir(parents=True)
        python_bin = venv_dir / "python"
        python_bin.touch()

        with patch('subprocess.run', side_effect=Exception("No version")):
            result = segment._get_python_env(str(tmp_path))
            assert result == "venv"

    def test_detect_conda_env(self, segment, tmp_path, monkeypatch):
        """Should detect conda environment."""
        monkeypatch.setenv('CONDA_DEFAULT_ENV', 'stats-env')

        result = segment._get_python_env(str(tmp_path))
        assert result == "conda: stats-env"

    def test_ignore_conda_base(self, segment, tmp_path, monkeypatch):
        """Should ignore conda base environment."""
        monkeypatch.setenv('CONDA_DEFAULT_ENV', 'base')

        result = segment._get_python_env(str(tmp_path))
        # Should return None (no venv detected)
        assert result is None

    def test_detect_pyenv(self, segment, tmp_path):
        """Should detect pyenv from .python-version file."""
        version_file = tmp_path / ".python-version"
        version_file.write_text("3.11.5\n")

        result = segment._get_python_env(str(tmp_path))
        assert result == "pyenv: 3.11.5"

    def test_disabled_by_config(self, tmp_path):
        """Should return None when config disabled."""
        config = StatusLineConfig()
        config.set('project.detect_python_env', False)
        segment = ProjectSegment(config)

        # Even with venv present
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()

        result = segment._get_python_env(str(tmp_path))
        assert result is None

    def test_no_env_detected(self, segment, tmp_path):
        """Should return None when no environment detected."""
        result = segment._get_python_env(str(tmp_path))
        assert result is None


class TestNodeVersionDetection:
    """Test Node.js version detection."""

    @pytest.fixture
    def segment(self):
        config = StatusLineConfig()
        config.set('project.detect_node_version', True)
        return ProjectSegment(config)

    def test_detect_from_nvmrc(self, segment, tmp_path):
        """Should detect version from .nvmrc file."""
        nvmrc = tmp_path / ".nvmrc"
        nvmrc.write_text("20.11.0\n")

        result = segment._get_node_version(str(tmp_path))
        assert result == "v20.11.0"

    def test_nvmrc_with_v_prefix(self, segment, tmp_path):
        """Should handle .nvmrc with 'v' prefix."""
        nvmrc = tmp_path / ".nvmrc"
        nvmrc.write_text("v20.11.0\n")

        result = segment._get_node_version(str(tmp_path))
        assert result == "v20.11.0"

    def test_fallback_to_node_version(self, segment, tmp_path):
        """Should fallback to current node version."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "v20.11.0\n"
            mock_run.return_value = mock_result

            result = segment._get_node_version(str(tmp_path))
            assert result == "v20.11.0"

    def test_node_not_installed(self, segment, tmp_path):
        """Should return None when node not installed."""
        with patch('subprocess.run', side_effect=Exception("Node not found")):
            result = segment._get_node_version(str(tmp_path))
            assert result is None

    def test_disabled_by_config(self, tmp_path):
        """Should return None when config disabled."""
        config = StatusLineConfig()
        config.set('project.detect_node_version', False)
        segment = ProjectSegment(config)

        result = segment._get_node_version(str(tmp_path))
        assert result is None


class TestRPackageHealth:
    """Test R package health checks."""

    @pytest.fixture
    def segment(self):
        config = StatusLineConfig()
        config.set('project.detect_r_package_health', True)
        return ProjectSegment(config)

    def test_not_r_package(self, segment, tmp_path):
        """Should return None for non-R packages."""
        result = segment._get_r_package_health(str(tmp_path))
        assert result is None

    def test_r_package_with_tests(self, segment, tmp_path):
        """Should return ✓ for package with tests."""
        desc = tmp_path / "DESCRIPTION"
        desc.write_text("Package: testpkg\nVersion: 1.0.0\n")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        result = segment._get_r_package_health(str(tmp_path))
        assert result == "✓"

    def test_r_package_no_tests(self, segment, tmp_path):
        """Should return ⚠ for package without tests."""
        desc = tmp_path / "DESCRIPTION"
        desc.write_text("Package: testpkg\nVersion: 1.0.0\n")

        result = segment._get_r_package_health(str(tmp_path))
        assert result == "⚠"

    def test_r_package_check_errors(self, segment, tmp_path):
        """Should return ❌ for packages with check errors."""
        desc = tmp_path / "DESCRIPTION"
        desc.write_text("Package: testpkg\nVersion: 1.0.0\n")

        # Create R CMD check results
        check_dir = tmp_path / "testpkg.Rcheck"
        check_dir.mkdir()
        check_log = check_dir / "00check.log"
        check_log.write_text("ERROR: Something failed\n")

        result = segment._get_r_package_health(str(tmp_path))
        assert result == "❌"

    def test_r_package_check_warnings(self, segment, tmp_path):
        """Should return ⚠ for packages with warnings."""
        desc = tmp_path / "DESCRIPTION"
        desc.write_text("Package: testpkg\nVersion: 1.0.0\n")

        check_dir = tmp_path / "testpkg.Rcheck"
        check_dir.mkdir()
        check_log = check_dir / "00check.log"
        check_log.write_text("WARNING: Undocumented function\n")

        result = segment._get_r_package_health(str(tmp_path))
        assert result == "⚠"

    def test_r_package_check_notes(self, segment, tmp_path):
        """Should return ⚠ for packages with notes."""
        desc = tmp_path / "DESCRIPTION"
        desc.write_text("Package: testpkg\nVersion: 1.0.0\n")

        check_dir = tmp_path / "testpkg.Rcheck"
        check_dir.mkdir()
        check_log = check_dir / "00check.log"
        check_log.write_text("NOTE: Something to improve\n")

        result = segment._get_r_package_health(str(tmp_path))
        assert result == "⚠"

    def test_disabled_by_config(self, tmp_path):
        """Should return None when config disabled."""
        config = StatusLineConfig()
        config.set('project.detect_r_package_health', False)
        segment = ProjectSegment(config)

        desc = tmp_path / "DESCRIPTION"
        desc.write_text("Package: testpkg\nVersion: 1.0.0\n")

        result = segment._get_r_package_health(str(tmp_path))
        assert result is None


class TestDependencyWarnings:
    """Test dependency status warnings."""

    @pytest.fixture
    def segment(self):
        config = StatusLineConfig()
        config.set('project.show_dependency_warnings', True)
        return ProjectSegment(config)

    def test_python_outdated_deps(self, segment, tmp_path):
        """Should detect outdated Python dependencies."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps([
                {"name": "requests", "version": "2.28.0"},
                {"name": "numpy", "version": "1.23.0"}
            ])
            mock_run.return_value = mock_result

            result = segment._get_dependency_warnings(str(tmp_path), "python")
            assert result == "⚠ 2 outdated"

    def test_python_no_outdated(self, segment, tmp_path):
        """Should return None when no outdated deps."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "[]"
            mock_run.return_value = mock_result

            result = segment._get_dependency_warnings(str(tmp_path), "python")
            assert result is None

    def test_node_outdated_deps(self, segment, tmp_path):
        """Should detect outdated Node dependencies."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = json.dumps({
                "express": {},
                "lodash": {},
                "react": {}
            })
            mock_run.return_value = mock_result

            result = segment._get_dependency_warnings(str(tmp_path), "node")
            assert result == "⚠ 3 outdated"

    def test_node_no_outdated(self, segment, tmp_path):
        """Should return None when no outdated Node deps."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "{}"
            mock_run.return_value = mock_result

            result = segment._get_dependency_warnings(str(tmp_path), "node")
            assert result is None

    def test_subprocess_error(self, segment, tmp_path):
        """Should return None when subprocess fails."""
        with patch('subprocess.run', side_effect=Exception("Command failed")):
            result = segment._get_dependency_warnings(str(tmp_path), "python")
            assert result is None

    def test_disabled_by_config(self, tmp_path):
        """Should return None when config disabled."""
        config = StatusLineConfig()
        config.set('project.show_dependency_warnings', False)
        segment = ProjectSegment(config)

        result = segment._get_dependency_warnings(str(tmp_path), "python")
        assert result is None

    def test_r_package_type(self, segment, tmp_path):
        """Should skip R packages (not implemented yet)."""
        result = segment._get_dependency_warnings(str(tmp_path), "r-package")
        assert result is None

    def test_unknown_project_type(self, segment, tmp_path):
        """Should return None for unknown project types."""
        result = segment._get_dependency_warnings(str(tmp_path), "unknown")
        assert result is None
