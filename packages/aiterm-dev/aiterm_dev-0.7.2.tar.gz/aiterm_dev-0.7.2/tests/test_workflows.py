"""Tests for workflow CLI commands including session-aware execution."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from aiterm.cli.workflows import (
    app,
    get_current_live_session,
    update_session_task,
    RUNNABLE_WORKFLOWS,
    WORKFLOW_TEMPLATES,
    WorkflowTemplate,
    load_workflow,
    save_workflow,
    get_workflows_dir,
    get_custom_workflows_dir,
    load_custom_workflow,
    list_custom_workflows,
    get_all_workflows,
    run_single_workflow,
)

runner = CliRunner()


class TestWorkflowTemplates:
    """Test workflow template management."""

    def test_builtin_workflows_exist(self):
        """Test that built-in workflow templates are defined."""
        assert len(WORKFLOW_TEMPLATES) > 0
        # Check for any workflow templates (names may vary)
        assert any(wf for wf in WORKFLOW_TEMPLATES.values())

    def test_workflow_template_dataclass(self):
        """Test WorkflowTemplate dataclass."""
        wf = WorkflowTemplate(
            name="test-workflow",
            description="A test workflow",
            context_type="python",
            auto_approvals=["pytest"],
            claude_commands=["/test"],
        )

        assert wf.name == "test-workflow"
        assert wf.description == "A test workflow"
        assert wf.context_type == "python"
        assert "pytest" in wf.auto_approvals

    def test_workflow_to_dict(self):
        """Test workflow serialization."""
        wf = WorkflowTemplate(
            name="test",
            description="Test",
            auto_approvals=["command1"],
        )

        data = wf.to_dict()
        assert data["name"] == "test"
        assert "auto_approvals" in data

    def test_get_workflows_dir(self):
        """Test workflows directory path."""
        dir_path = get_workflows_dir()
        assert ".config" in str(dir_path) or ".claude" in str(dir_path)

    def test_save_and_load_workflow(self, tmp_path: Path):
        """Test saving and loading custom workflow."""
        wf = WorkflowTemplate(
            name="custom-test",
            description="Custom test workflow",
        )

        with patch("aiterm.cli.workflows.get_workflows_dir", return_value=tmp_path):
            result = save_workflow(wf)
            assert result is True

            loaded = load_workflow("custom-test")
            assert loaded is not None
            assert loaded.name == "custom-test"


class TestWorkflowListCommand:
    """Test workflow list command."""

    def test_workflows_list(self):
        """Test listing workflows."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        # Should show some workflow templates
        assert "Workflow" in result.output or "workflow" in result.output


class TestWorkflowShowCommand:
    """Test workflow show command."""

    def test_workflows_show_builtin(self):
        """Test showing a built-in workflow."""
        # Get a builtin workflow name
        if WORKFLOW_TEMPLATES:
            name = list(WORKFLOW_TEMPLATES.keys())[0]
            result = runner.invoke(app, ["show", name])
            assert result.exit_code == 0

    def test_workflows_show_not_found(self):
        """Test showing non-existent workflow."""
        result = runner.invoke(app, ["show", "nonexistent-workflow-xyz"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestRunnableWorkflows:
    """Test built-in runnable workflows."""

    def test_runnable_workflows_defined(self):
        """Test that runnable workflows are defined."""
        assert "test" in RUNNABLE_WORKFLOWS
        assert "lint" in RUNNABLE_WORKFLOWS
        assert "docs" in RUNNABLE_WORKFLOWS
        assert "release" in RUNNABLE_WORKFLOWS

    def test_runnable_workflow_structure(self):
        """Test runnable workflow structure."""
        wf = RUNNABLE_WORKFLOWS["test"]
        assert "name" in wf
        assert "description" in wf
        assert "steps" in wf
        assert "requires_session" in wf


class TestSessionIntegration:
    """Test session-aware workflow features."""

    def test_get_current_session_none(self, tmp_path: Path):
        """Test getting session when none exists."""
        # Patch at the source - where load_live_sessions is defined
        with patch("aiterm.cli.sessions.load_live_sessions", return_value=[]):
            session = get_current_live_session()
            assert session is None

    def test_get_current_session_exists(self, tmp_path: Path):
        """Test getting existing session."""
        from aiterm.cli.sessions import LiveSession

        mock_session = MagicMock(spec=LiveSession)
        mock_session.path = str(Path.cwd())
        mock_session.session_id = "test-123"

        # Patch at the source
        with patch("aiterm.cli.sessions.load_live_sessions", return_value=[mock_session]):
            session = get_current_live_session()
            assert session is not None
            assert session.session_id == "test-123"

    def test_update_session_task_no_session(self):
        """Test updating task when no session exists."""
        with patch("aiterm.cli.workflows.get_current_live_session", return_value=None):
            result = update_session_task("Test task")
            assert result is False

    def test_update_session_task_success(self, tmp_path: Path):
        """Test successfully updating session task."""
        from aiterm.cli.sessions import LiveSession

        # Create session directory and file
        sessions_dir = tmp_path / "active"
        sessions_dir.mkdir(parents=True)
        session_file = sessions_dir / "test-123.json"
        session_file.write_text(json.dumps({
            "session_id": "test-123",
            "project": "test",
            "path": str(Path.cwd()),
            "started": datetime.now().isoformat(),
        }))

        mock_session = MagicMock(spec=LiveSession)
        mock_session.path = str(Path.cwd())
        mock_session.session_id = "test-123"

        with patch("aiterm.cli.workflows.get_current_live_session", return_value=mock_session):
            with patch("aiterm.cli.sessions.get_live_sessions_dir", return_value=tmp_path):
                result = update_session_task("Working on feature")
                assert result is True

                # Verify task was updated
                data = json.loads(session_file.read_text())
                assert data["task"] == "Working on feature"


class TestWorkflowStatusCommand:
    """Test workflow status command."""

    def test_workflows_status_no_session(self):
        """Test status when no session active."""
        with patch("aiterm.cli.workflows.get_current_live_session", return_value=None):
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "No active session" in result.output or "no active session" in result.output.lower()

    def test_workflows_status_with_session(self):
        """Test status when session is active."""
        from aiterm.cli.sessions import LiveSession

        mock_session = MagicMock(spec=LiveSession)
        mock_session.session_id = "test-session-123"
        mock_session.duration_str = "5m"
        mock_session.task = "Testing"

        with patch("aiterm.cli.workflows.get_current_live_session", return_value=mock_session):
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 0
            assert "Active" in result.output or "session" in result.output.lower()


class TestWorkflowRunCommand:
    """Test workflow run command."""

    def test_workflows_run_unknown(self):
        """Test running unknown workflow."""
        result = runner.invoke(app, ["run", "nonexistent-xyz"])
        assert result.exit_code == 1
        assert "Unknown" in result.output or "not found" in result.output.lower()

    def test_workflows_run_dry_run(self):
        """Test dry run mode."""
        result = runner.invoke(app, ["run", "test", "--dry-run"])
        assert result.exit_code == 0
        assert "dry run" in result.output.lower() or "Would run" in result.output

    def test_workflows_run_requires_session(self):
        """Test workflow that requires session."""
        with patch("aiterm.cli.workflows.get_current_live_session", return_value=None):
            result = runner.invoke(app, ["run", "release"])
            # Should fail or warn about session requirement
            assert "session" in result.output.lower()

    def test_workflows_run_no_session_flag(self):
        """Test running with --no-session flag."""
        with patch("aiterm.cli.workflows.get_current_live_session", return_value=None):
            # lint doesn't require session, should work
            result = runner.invoke(app, ["run", "lint", "--dry-run", "--no-session"])
            assert result.exit_code == 0


class TestWorkflowTaskCommand:
    """Test workflow task command."""

    def test_workflows_task_no_session(self):
        """Test setting task when no session."""
        with patch("aiterm.cli.workflows.get_current_live_session", return_value=None):
            result = runner.invoke(app, ["task", "My task"])
            assert result.exit_code == 1
            assert "No active session" in result.output or "no active" in result.output.lower()

    def test_workflows_task_success(self, tmp_path: Path):
        """Test successfully setting task."""
        from aiterm.cli.sessions import LiveSession

        # Create session file
        sessions_dir = tmp_path / "active"
        sessions_dir.mkdir(parents=True)
        session_file = sessions_dir / "test-123.json"
        session_file.write_text(json.dumps({
            "session_id": "test-123",
            "project": "test",
            "path": str(Path.cwd()),
            "started": datetime.now().isoformat(),
        }))

        mock_session = MagicMock(spec=LiveSession)
        mock_session.path = str(Path.cwd())
        mock_session.session_id = "test-123"

        with patch("aiterm.cli.workflows.get_current_live_session", return_value=mock_session):
            with patch("aiterm.cli.sessions.get_live_sessions_dir", return_value=tmp_path):
                result = runner.invoke(app, ["task", "Working on feature X"])
                assert result.exit_code == 0
                assert "Task updated" in result.output or "updated" in result.output.lower()

    def test_workflows_task_clear(self, tmp_path: Path):
        """Test clearing task."""
        from aiterm.cli.sessions import LiveSession

        # Create session file
        sessions_dir = tmp_path / "active"
        sessions_dir.mkdir(parents=True)
        session_file = sessions_dir / "test-123.json"
        session_file.write_text(json.dumps({
            "session_id": "test-123",
            "project": "test",
            "path": str(Path.cwd()),
            "started": datetime.now().isoformat(),
            "task": "Previous task",
        }))

        mock_session = MagicMock(spec=LiveSession)
        mock_session.path = str(Path.cwd())
        mock_session.session_id = "test-123"

        with patch("aiterm.cli.workflows.get_current_live_session", return_value=mock_session):
            with patch("aiterm.cli.sessions.get_live_sessions_dir", return_value=tmp_path):
                result = runner.invoke(app, ["task"])  # No description = clear
                assert result.exit_code == 0
                assert "cleared" in result.output.lower()


class TestNewBuiltinWorkflows:
    """Test new built-in workflows added in quick wins."""

    def test_new_workflows_defined(self):
        """Test that new built-in workflows are defined."""
        assert "format" in RUNNABLE_WORKFLOWS
        assert "check" in RUNNABLE_WORKFLOWS
        assert "build" in RUNNABLE_WORKFLOWS
        assert "clean" in RUNNABLE_WORKFLOWS
        assert "docs-serve" in RUNNABLE_WORKFLOWS
        assert "deploy-docs" in RUNNABLE_WORKFLOWS

    def test_workflow_has_required_fields(self):
        """Test each workflow has required fields."""
        for name, wf in RUNNABLE_WORKFLOWS.items():
            assert "name" in wf, f"{name} missing 'name'"
            assert "description" in wf, f"{name} missing 'description'"
            assert "steps" in wf, f"{name} missing 'steps'"
            assert "requires_session" in wf, f"{name} missing 'requires_session'"


class TestWorkflowChaining:
    """Test workflow chaining with + separator."""

    def test_chain_dry_run(self):
        """Test chaining multiple workflows in dry run."""
        with patch("aiterm.cli.workflows.get_current_live_session", return_value=None):
            result = runner.invoke(app, ["run", "lint+test", "--dry-run", "--no-session"])
            assert result.exit_code == 0
            assert "lint" in result.output.lower()
            assert "test" in result.output.lower()
            assert "chain" in result.output.lower() or "→" in result.output

    def test_chain_unknown_workflow(self):
        """Test chaining with unknown workflow fails."""
        result = runner.invoke(app, ["run", "lint+nonexistent+test"])
        assert result.exit_code == 1
        assert "unknown" in result.output.lower() or "Unknown" in result.output

    def test_single_workflow_no_chain_message(self):
        """Test single workflow doesn't show chain messages."""
        with patch("aiterm.cli.workflows.get_current_live_session", return_value=None):
            result = runner.invoke(app, ["run", "lint", "--dry-run", "--no-session"])
            assert result.exit_code == 0
            # Should not show chain-related output for single workflow
            assert "→" not in result.output


class TestCustomWorkflows:
    """Test custom YAML workflow support."""

    def test_get_custom_workflows_dir(self):
        """Test custom workflows directory path."""
        path = get_custom_workflows_dir()
        assert "aiterm" in str(path)
        assert "workflows" in str(path)

    def test_list_custom_workflows_empty(self, tmp_path: Path):
        """Test listing custom workflows when none exist."""
        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            custom = list_custom_workflows()
            assert custom == []

    def test_list_custom_workflows(self, tmp_path: Path):
        """Test listing custom workflows."""
        # Create some workflow files
        (tmp_path / "my-workflow.yaml").write_text("name: my-workflow")
        (tmp_path / "another.yml").write_text("name: another")
        (tmp_path / "not-a-workflow.txt").write_text("ignore me")

        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            custom = list_custom_workflows()
            assert "my-workflow" in custom
            assert "another" in custom
            assert "not-a-workflow" not in custom

    def test_load_custom_workflow(self, tmp_path: Path):
        """Test loading a custom workflow from YAML."""
        yaml_content = """
name: test-custom
description: A test workflow
requires_session: true
steps:
  - task: Step 1
    command: echo hello
  - task: Step 2
    command: echo world
"""
        (tmp_path / "test-custom.yaml").write_text(yaml_content)

        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            wf = load_custom_workflow("test-custom")
            assert wf is not None
            assert wf["name"] == "test-custom"
            assert wf["description"] == "A test workflow"
            assert wf["requires_session"] is True
            assert len(wf["steps"]) == 2

    def test_load_custom_workflow_not_found(self, tmp_path: Path):
        """Test loading non-existent custom workflow."""
        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            wf = load_custom_workflow("nonexistent")
            assert wf is None

    def test_get_all_workflows_includes_custom(self, tmp_path: Path):
        """Test get_all_workflows includes custom workflows."""
        yaml_content = """
name: custom-test
description: Custom
steps: []
"""
        (tmp_path / "custom-test.yaml").write_text(yaml_content)

        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            all_wf = get_all_workflows()
            assert "test" in all_wf  # Built-in
            assert "lint" in all_wf  # Built-in
            assert "custom-test" in all_wf  # Custom


class TestCustomWorkflowCommands:
    """Test custom workflow CLI commands."""

    def test_custom_list_empty(self, tmp_path: Path):
        """Test listing custom workflows when none exist."""
        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            result = runner.invoke(app, ["custom", "list"])
            assert result.exit_code == 0
            assert "No custom workflows" in result.output

    def test_custom_list_with_workflows(self, tmp_path: Path):
        """Test listing custom workflows."""
        (tmp_path / "my-wf.yaml").write_text("name: my-wf\ndescription: Test\n")

        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            result = runner.invoke(app, ["custom", "list"])
            assert result.exit_code == 0
            assert "my-wf" in result.output

    def test_custom_show(self, tmp_path: Path):
        """Test showing custom workflow details."""
        yaml_content = """
name: show-test
description: Show test workflow
steps:
  - task: Run tests
    command: pytest
"""
        (tmp_path / "show-test.yaml").write_text(yaml_content)

        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            result = runner.invoke(app, ["custom", "show", "show-test"])
            assert result.exit_code == 0
            assert "show-test" in result.output
            assert "Show test workflow" in result.output

    def test_custom_show_not_found(self, tmp_path: Path):
        """Test showing non-existent workflow."""
        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            result = runner.invoke(app, ["custom", "show", "nonexistent"])
            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_custom_create(self, tmp_path: Path):
        """Test creating custom workflow."""
        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            result = runner.invoke(app, ["custom", "create", "new-workflow"])
            assert result.exit_code == 0
            assert "Created" in result.output

            # Verify file was created
            yaml_file = tmp_path / "new-workflow.yaml"
            assert yaml_file.exists()
            content = yaml_file.read_text()
            assert "name: new-workflow" in content

    def test_custom_create_already_exists(self, tmp_path: Path):
        """Test creating workflow that already exists."""
        (tmp_path / "existing.yaml").write_text("name: existing")

        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            result = runner.invoke(app, ["custom", "create", "existing"])
            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_custom_delete(self, tmp_path: Path):
        """Test deleting custom workflow."""
        (tmp_path / "to-delete.yaml").write_text("name: to-delete")

        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            result = runner.invoke(app, ["custom", "delete", "to-delete"])
            assert result.exit_code == 0
            assert "Deleted" in result.output

            # Verify file was deleted
            assert not (tmp_path / "to-delete.yaml").exists()

    def test_custom_delete_not_found(self, tmp_path: Path):
        """Test deleting non-existent workflow."""
        with patch("aiterm.cli.workflows.get_custom_workflows_dir", return_value=tmp_path):
            result = runner.invoke(app, ["custom", "delete", "nonexistent"])
            assert result.exit_code == 1
            assert "not found" in result.output.lower()


class TestRunSingleWorkflow:
    """Test run_single_workflow helper function."""

    def test_run_single_workflow_dry_run(self):
        """Test running workflow in dry run mode."""
        wf = {
            "name": "Test",
            "description": "Test workflow",
            "steps": [
                {"task": "Echo", "command": "echo hello"},
            ],
        }

        # Dry run should always succeed
        result = run_single_workflow(
            name="test",
            wf=wf,
            dry_run=True,
            use_session=False,
            session=None,
        )
        assert result is True

    def test_run_single_workflow_with_chain_context(self):
        """Test running workflow with chain context prefix."""
        wf = {
            "name": "Test",
            "steps": [
                {"task": "Echo", "command": "echo hello"},
            ],
        }

        result = run_single_workflow(
            name="test",
            wf=wf,
            dry_run=True,
            use_session=False,
            session=None,
            chain_context="my-chain",
        )
        assert result is True
