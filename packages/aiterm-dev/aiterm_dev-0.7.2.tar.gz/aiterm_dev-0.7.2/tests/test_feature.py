"""Tests for feature branch workflow CLI commands."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aiterm.cli.feature import (
    FeatureBranch,
    WorktreeInfo,
    _get_current_branch,
    _get_feature_branches,
    _get_repo_root,
    _get_worktrees,
    _run_git,
)


class TestRunGit:
    """Tests for _run_git helper."""

    def test_run_git_success(self):
        """Test successful git command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="main\n",
                returncode=0,
            )
            result = _run_git(["branch", "--show-current"])
            assert result == "main"
            mock_run.assert_called_once()

    def test_run_git_failure(self):
        """Test failed git command returns None."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            result = _run_git(["nonexistent", "command"])
            assert result is None


class TestGetCurrentBranch:
    """Tests for _get_current_branch."""

    def test_get_current_branch(self):
        """Test getting current branch name."""
        with patch("aiterm.cli.feature._run_git") as mock_git:
            mock_git.return_value = "feature/my-feature"
            result = _get_current_branch()
            assert result == "feature/my-feature"
            mock_git.assert_called_with(["branch", "--show-current"])


class TestGetRepoRoot:
    """Tests for _get_repo_root."""

    def test_get_repo_root(self):
        """Test getting repository root."""
        with patch("aiterm.cli.feature._run_git") as mock_git:
            mock_git.return_value = "/path/to/repo"
            result = _get_repo_root()
            assert result == Path("/path/to/repo")

    def test_get_repo_root_not_a_repo(self):
        """Test returns None when not in a repo."""
        with patch("aiterm.cli.feature._run_git") as mock_git:
            mock_git.return_value = None
            result = _get_repo_root()
            assert result is None


class TestGetFeatureBranches:
    """Tests for _get_feature_branches."""

    def test_get_feature_branches_empty(self):
        """Test with no feature branches."""
        with patch("aiterm.cli.feature._run_git") as mock_git:
            mock_git.return_value = None  # branch --list returns nothing
            result = _get_feature_branches()
            assert result == []

    def test_get_feature_branches_with_branches(self):
        """Test with multiple feature branches."""
        with patch("aiterm.cli.feature._run_git") as mock_git:
            with patch("aiterm.cli.feature._get_current_branch") as mock_current:
                mock_current.return_value = "feature/current"
                mock_git.side_effect = [
                    "feature/current\nfeature/other",  # branch --list
                    "3",  # commits ahead for current
                    "",   # merged check for current (not merged)
                    "1",  # commits ahead for other
                    "feature/other",  # merged check for other (is merged)
                ]
                result = _get_feature_branches()
                assert len(result) == 2

                # Check current branch
                current = [b for b in result if b.name == "current"][0]
                assert current.is_current is True
                assert current.commits_ahead == 3
                assert current.is_merged is False

                # Check other branch
                other = [b for b in result if b.name == "other"][0]
                assert other.is_current is False
                assert other.commits_ahead == 1
                assert other.is_merged is True


class TestGetWorktrees:
    """Tests for _get_worktrees."""

    def test_get_worktrees_empty(self):
        """Test with no worktrees."""
        with patch("aiterm.cli.feature._run_git") as mock_git:
            mock_git.return_value = None
            result = _get_worktrees()
            assert result == []

    def test_get_worktrees_with_worktrees(self):
        """Test parsing worktree list."""
        with patch("aiterm.cli.feature._run_git") as mock_git:
            mock_git.return_value = (
                "worktree /path/to/main\n"
                "HEAD abc12345\n"
                "branch refs/heads/main\n"
                "\n"
                "worktree /path/to/feature\n"
                "HEAD def67890\n"
                "branch refs/heads/feature/test\n"
            )
            result = _get_worktrees()
            assert len(result) == 2

            main_wt = [w for w in result if w.branch == "main"][0]
            assert main_wt.path == Path("/path/to/main")
            assert main_wt.commit == "abc12345"

            feature_wt = [w for w in result if w.branch == "feature/test"][0]
            assert feature_wt.path == Path("/path/to/feature")


class TestFeatureBranchDataclass:
    """Tests for FeatureBranch dataclass."""

    def test_feature_branch_defaults(self):
        """Test default values."""
        branch = FeatureBranch(name="test", full_name="feature/test")
        assert branch.is_current is False
        assert branch.commits_ahead == 0
        assert branch.worktree_path is None
        assert branch.is_merged is False
        assert branch.has_pr is False
        assert branch.pr_number is None

    def test_feature_branch_with_values(self):
        """Test with custom values."""
        branch = FeatureBranch(
            name="test",
            full_name="feature/test",
            is_current=True,
            commits_ahead=5,
            worktree_path=Path("/path/to/worktree"),
            is_merged=True,
        )
        assert branch.is_current is True
        assert branch.commits_ahead == 5
        assert branch.worktree_path == Path("/path/to/worktree")
        assert branch.is_merged is True


class TestWorktreeInfoDataclass:
    """Tests for WorktreeInfo dataclass."""

    def test_worktree_info_defaults(self):
        """Test default values."""
        wt = WorktreeInfo(
            path=Path("/path"),
            branch="main",
            commit="abc1234",
        )
        assert wt.is_bare is False
        assert wt.is_main is False

    def test_worktree_info_bare(self):
        """Test bare worktree."""
        wt = WorktreeInfo(
            path=Path("/path"),
            branch="",
            commit="abc1234",
            is_bare=True,
        )
        assert wt.is_bare is True


class TestFeatureStatusCommand:
    """Tests for feature status command."""

    def test_status_not_in_repo(self):
        """Test status when not in a git repo."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner()

        with patch("aiterm.cli.feature._get_repo_root") as mock_root:
            mock_root.return_value = None
            result = runner.invoke(app, ["feature", "status"])
            assert result.exit_code == 1
            assert "Not in a git repository" in result.stdout


class TestFeatureListCommand:
    """Tests for feature list command."""

    def test_list_no_features(self):
        """Test list with no feature branches."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner()

        with patch("aiterm.cli.feature._get_repo_root") as mock_root:
            mock_root.return_value = Path("/path/to/repo")
            with patch("aiterm.cli.feature._get_feature_branches") as mock_features:
                mock_features.return_value = []
                with patch("aiterm.cli.feature._get_worktrees") as mock_wt:
                    mock_wt.return_value = []
                    result = runner.invoke(app, ["feature", "list"])
                    assert result.exit_code == 0
                    assert "No feature branches" in result.stdout


class TestFeatureCleanupCommand:
    """Tests for feature cleanup command."""

    def test_cleanup_no_merged(self):
        """Test cleanup with no merged branches."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner()

        with patch("aiterm.cli.feature._get_repo_root") as mock_root:
            mock_root.return_value = Path("/path/to/repo")
            with patch("aiterm.cli.feature._get_feature_branches") as mock_features:
                mock_features.return_value = [
                    FeatureBranch(name="active", full_name="feature/active", is_merged=False)
                ]
                result = runner.invoke(app, ["feature", "cleanup"])
                assert result.exit_code == 0
                assert "No merged feature branches" in result.stdout

    def test_cleanup_dry_run(self):
        """Test cleanup with dry run."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner()

        with patch("aiterm.cli.feature._get_repo_root") as mock_root:
            mock_root.return_value = Path("/path/to/repo")
            with patch("aiterm.cli.feature._get_feature_branches") as mock_features:
                mock_features.return_value = [
                    FeatureBranch(name="merged", full_name="feature/merged", is_merged=True)
                ]
                with patch("aiterm.cli.feature._get_worktrees") as mock_wt:
                    mock_wt.return_value = []
                    result = runner.invoke(app, ["feature", "cleanup", "--dry-run"])
                    assert result.exit_code == 0
                    assert "Dry run" in result.stdout
                    assert "feature/merged" in result.stdout


class TestFeaturePromoteCommand:
    """Tests for feature promote command."""

    def test_promote_no_gh(self):
        """Test promote when gh CLI is not installed."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner()

        with patch("aiterm.cli.feature._check_gh_installed") as mock_gh:
            mock_gh.return_value = False
            result = runner.invoke(app, ["feature", "promote"])
            assert result.exit_code == 1
            assert "gh" in result.stdout.lower()

    def test_promote_not_in_repo(self):
        """Test promote when not in a git repo."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner()

        with patch("aiterm.cli.feature._check_gh_installed") as mock_gh:
            mock_gh.return_value = True
            with patch("aiterm.cli.feature._get_repo_root") as mock_root:
                mock_root.return_value = None
                result = runner.invoke(app, ["feature", "promote"])
                assert result.exit_code == 1
                assert "Not in a git repository" in result.stdout

    def test_promote_pr_exists(self):
        """Test promote when PR already exists."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner()

        with patch("aiterm.cli.feature._check_gh_installed") as mock_gh:
            mock_gh.return_value = True
            with patch("aiterm.cli.feature._get_repo_root") as mock_root:
                mock_root.return_value = Path("/path/to/repo")
                with patch("aiterm.cli.feature._get_current_branch") as mock_branch:
                    mock_branch.return_value = "feature/existing"
                    with patch("aiterm.cli.feature._get_pr_for_branch") as mock_pr:
                        mock_pr.return_value = {
                            "number": 42,
                            "title": "Existing PR",
                            "state": "OPEN",
                            "url": "https://github.com/test/repo/pull/42"
                        }
                        result = runner.invoke(app, ["feature", "promote"])
                        assert result.exit_code == 0
                        assert "PR already exists" in result.stdout
                        assert "#42" in result.stdout

    def test_promote_help(self):
        """Test promote --help shows options."""
        import re
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner(env={"NO_COLOR": "1"})
        result = runner.invoke(app, ["feature", "promote", "--help"])
        assert result.exit_code == 0

        # Strip ANSI codes for reliable assertion
        clean_output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        assert "--draft" in clean_output
        assert "--title" in clean_output
        assert "--base" in clean_output
        assert "--web" in clean_output


class TestFeatureReleaseCommand:
    """Tests for feature release command."""

    def test_release_no_gh(self):
        """Test release when gh CLI is not installed."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner()

        with patch("aiterm.cli.feature._check_gh_installed") as mock_gh:
            mock_gh.return_value = False
            result = runner.invoke(app, ["feature", "release"])
            assert result.exit_code == 1
            assert "gh" in result.stdout.lower()

    def test_release_not_in_repo(self):
        """Test release when not in a git repo."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner()

        with patch("aiterm.cli.feature._check_gh_installed") as mock_gh:
            mock_gh.return_value = True
            with patch("aiterm.cli.feature._get_repo_root") as mock_root:
                mock_root.return_value = None
                result = runner.invoke(app, ["feature", "release"])
                assert result.exit_code == 1
                assert "Not in a git repository" in result.stdout

    def test_release_pr_exists(self):
        """Test release when PR from dev to main already exists."""
        from typer.testing import CliRunner
        from aiterm.cli.main import app
        import json

        runner = CliRunner()

        with patch("aiterm.cli.feature._check_gh_installed") as mock_gh:
            mock_gh.return_value = True
            with patch("aiterm.cli.feature._get_repo_root") as mock_root:
                mock_root.return_value = Path("/path/to/repo")
                with patch("aiterm.cli.feature._get_current_branch") as mock_branch:
                    mock_branch.return_value = "dev"
                    with patch("aiterm.cli.feature._get_pr_for_branch") as mock_pr:
                        mock_pr.return_value = None  # No PR for "dev" branch directly
                        with patch("aiterm.cli.feature._run_gh") as mock_run_gh:
                            # Return existing PR from dev to main
                            mock_run_gh.return_value = json.dumps([{
                                "number": 99,
                                "title": "Release: merge dev to main",
                                "state": "OPEN",
                                "url": "https://github.com/test/repo/pull/99"
                            }])
                            result = runner.invoke(app, ["feature", "release"])
                            assert result.exit_code == 0
                            assert "Release PR already exists" in result.stdout
                            assert "#99" in result.stdout

    def test_release_help(self):
        """Test release --help shows options."""
        import re
        from typer.testing import CliRunner
        from aiterm.cli.main import app

        runner = CliRunner(env={"NO_COLOR": "1"})
        result = runner.invoke(app, ["feature", "release", "--help"])
        assert result.exit_code == 0

        # Strip ANSI codes for reliable assertion
        clean_output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        assert "--draft" in clean_output
        assert "--title" in clean_output
        assert "--body" in clean_output
        assert "--web" in clean_output
