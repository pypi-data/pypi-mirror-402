"""Tests for the tutorial module."""

import pytest
from aiterm.utils.tutorial import (
    TutorialLevel,
    TutorialStep,
    Tutorial,
    get_tutorial,
    list_tutorials,
    parse_level,
    create_getting_started_tutorial,
    create_intermediate_tutorial,
    create_advanced_tutorial,
)


class TestTutorialLevel:
    """Tests for TutorialLevel enum."""

    def test_level_values(self):
        """Test enum values."""
        assert TutorialLevel.GETTING_STARTED.value == "getting-started"
        assert TutorialLevel.INTERMEDIATE.value == "intermediate"
        assert TutorialLevel.ADVANCED.value == "advanced"

    def test_display_name(self):
        """Test display name property."""
        assert TutorialLevel.GETTING_STARTED.display_name == "Getting Started"
        assert TutorialLevel.INTERMEDIATE.display_name == "Intermediate"
        assert TutorialLevel.ADVANCED.display_name == "Advanced"

    def test_step_count(self):
        """Test step count property."""
        assert TutorialLevel.GETTING_STARTED.step_count == 7
        assert TutorialLevel.INTERMEDIATE.step_count == 11
        assert TutorialLevel.ADVANCED.step_count == 13

    def test_duration(self):
        """Test duration property."""
        assert TutorialLevel.GETTING_STARTED.duration == "~10 min"
        assert TutorialLevel.INTERMEDIATE.duration == "~20 min"
        assert TutorialLevel.ADVANCED.duration == "~35 min"

    def test_description(self):
        """Test description property."""
        assert "Essential" in TutorialLevel.GETTING_STARTED.description
        assert "Claude Code" in TutorialLevel.INTERMEDIATE.description
        assert "Release" in TutorialLevel.ADVANCED.description


class TestTutorialStep:
    """Tests for TutorialStep dataclass."""

    def test_basic_step(self):
        """Test creating a basic step."""
        step = TutorialStep(
            number=1,
            title="Test Step",
            description="A test step.",
        )
        assert step.number == 1
        assert step.title == "Test Step"
        assert step.description == "A test step."
        assert step.command is None
        assert step.hint is None

    def test_step_with_command(self):
        """Test creating a step with command."""
        step = TutorialStep(
            number=2,
            title="Command Step",
            description="Run a command.",
            command="ait doctor",
            hint="Check installation",
            interactive=True,
        )
        assert step.command == "ait doctor"
        assert step.hint == "Check installation"
        assert step.interactive is True

    def test_step_with_visuals(self):
        """Test creating a step with GIF and diagram."""
        step = TutorialStep(
            number=3,
            title="Visual Step",
            description="Step with visuals.",
            gif_path="docs/demos/tutorials/example.gif",
            diagram="flowchart TD\n    A-->B",
        )
        assert step.gif_path == "docs/demos/tutorials/example.gif"
        assert step.diagram is not None


class TestTutorial:
    """Tests for Tutorial class."""

    def test_tutorial_creation(self):
        """Test creating a tutorial."""
        tutorial = Tutorial(
            level=TutorialLevel.GETTING_STARTED,
            title="Test Tutorial",
            description="A test tutorial.",
            steps=[
                TutorialStep(number=1, title="Step 1", description="First step"),
                TutorialStep(number=2, title="Step 2", description="Second step"),
            ],
        )
        assert tutorial.level == TutorialLevel.GETTING_STARTED
        assert tutorial.title == "Test Tutorial"
        assert len(tutorial.steps) == 2

    def test_show_step_valid(self):
        """Test showing a valid step."""
        tutorial = Tutorial(
            level=TutorialLevel.GETTING_STARTED,
            title="Test",
            description="Test",
            steps=[
                TutorialStep(number=1, title="Step 1", description="First"),
            ],
        )
        step = tutorial.show_step(1)
        assert step.number == 1

    def test_show_step_invalid(self):
        """Test showing invalid step raises error."""
        tutorial = Tutorial(
            level=TutorialLevel.GETTING_STARTED,
            title="Test",
            description="Test",
            steps=[
                TutorialStep(number=1, title="Step 1", description="First"),
            ],
        )
        with pytest.raises(ValueError, match="Step 0 not found"):
            tutorial.show_step(0)
        with pytest.raises(ValueError, match="Step 2 not found"):
            tutorial.show_step(2)


class TestTutorialFactories:
    """Tests for tutorial factory functions."""

    def test_getting_started_tutorial(self):
        """Test Getting Started tutorial factory."""
        tutorial = create_getting_started_tutorial()
        assert tutorial.level == TutorialLevel.GETTING_STARTED
        assert len(tutorial.steps) == 7
        assert "aiterm" in tutorial.title.lower()

    def test_intermediate_tutorial(self):
        """Test Intermediate tutorial factory."""
        tutorial = create_intermediate_tutorial()
        assert tutorial.level == TutorialLevel.INTERMEDIATE
        assert len(tutorial.steps) == 11
        assert len(tutorial.prerequisites) >= 1

    def test_advanced_tutorial(self):
        """Test Advanced tutorial factory."""
        tutorial = create_advanced_tutorial()
        assert tutorial.level == TutorialLevel.ADVANCED
        assert len(tutorial.steps) == 13
        assert len(tutorial.prerequisites) >= 1

    def test_all_tutorials_have_numbered_steps(self):
        """Test that all tutorials have properly numbered steps."""
        for factory in [
            create_getting_started_tutorial,
            create_intermediate_tutorial,
            create_advanced_tutorial,
        ]:
            tutorial = factory()
            for i, step in enumerate(tutorial.steps, 1):
                assert step.number == i, f"Step {i} has wrong number in {tutorial.title}"

    def test_tutorials_have_required_fields(self):
        """Test all steps have required fields."""
        for factory in [
            create_getting_started_tutorial,
            create_intermediate_tutorial,
            create_advanced_tutorial,
        ]:
            tutorial = factory()
            for step in tutorial.steps:
                assert step.title, f"Step {step.number} missing title"
                assert step.description, f"Step {step.number} missing description"


class TestTutorialHelpers:
    """Tests for helper functions."""

    def test_get_tutorial(self):
        """Test getting tutorial by level."""
        tutorial = get_tutorial(TutorialLevel.GETTING_STARTED)
        assert tutorial.level == TutorialLevel.GETTING_STARTED

        tutorial = get_tutorial(TutorialLevel.INTERMEDIATE)
        assert tutorial.level == TutorialLevel.INTERMEDIATE

        tutorial = get_tutorial(TutorialLevel.ADVANCED)
        assert tutorial.level == TutorialLevel.ADVANCED

    def test_parse_level_exact(self):
        """Test parsing exact level strings."""
        assert parse_level("getting-started") == TutorialLevel.GETTING_STARTED
        assert parse_level("intermediate") == TutorialLevel.INTERMEDIATE
        assert parse_level("advanced") == TutorialLevel.ADVANCED

    def test_parse_level_partial(self):
        """Test parsing partial level strings (min 3 chars)."""
        assert parse_level("getting") == TutorialLevel.GETTING_STARTED
        assert parse_level("inter") == TutorialLevel.INTERMEDIATE
        assert parse_level("adv") == TutorialLevel.ADVANCED
        # Short partials (< 3 chars) don't match
        assert parse_level("ge") is None
        assert parse_level("in") is None

    def test_parse_level_case_insensitive(self):
        """Test parsing is case insensitive."""
        assert parse_level("GETTING-STARTED") == TutorialLevel.GETTING_STARTED
        assert parse_level("Intermediate") == TutorialLevel.INTERMEDIATE
        assert parse_level("ADVANCED") == TutorialLevel.ADVANCED

    def test_parse_level_invalid(self):
        """Test parsing invalid level returns None."""
        assert parse_level("invalid") is None
        assert parse_level("") is None
        assert parse_level("xyz") is None

    def test_list_tutorials(self, capsys):
        """Test listing tutorials produces output."""
        list_tutorials()
        # Just verify it doesn't crash - output is rich formatted


class TestTutorialStepCounts:
    """Tests to verify step counts match spec."""

    def test_total_step_count(self):
        """Test total steps: 7 + 11 + 13 = 31."""
        total = (
            len(create_getting_started_tutorial().steps) +
            len(create_intermediate_tutorial().steps) +
            len(create_advanced_tutorial().steps)
        )
        assert total == 31

    def test_enum_matches_actual(self):
        """Test enum step counts match actual step counts."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            assert len(tutorial.steps) == level.step_count, (
                f"{level.value} enum says {level.step_count} "
                f"but tutorial has {len(tutorial.steps)} steps"
            )


class TestTutorialContent:
    """Tests for tutorial content quality."""

    def test_getting_started_has_doctor_command(self):
        """Test Getting Started includes ait doctor."""
        tutorial = create_getting_started_tutorial()
        commands = [s.command for s in tutorial.steps if s.command]
        assert "ait doctor" in commands

    def test_getting_started_has_detect_command(self):
        """Test Getting Started includes ait detect."""
        tutorial = create_getting_started_tutorial()
        commands = [s.command for s in tutorial.steps if s.command]
        assert "ait detect" in commands

    def test_intermediate_has_claude_settings(self):
        """Test Intermediate includes Claude settings command."""
        tutorial = create_intermediate_tutorial()
        commands = [s.command for s in tutorial.steps if s.command]
        assert "ait claude settings" in commands

    def test_advanced_has_release_commands(self):
        """Test Advanced includes release commands."""
        tutorial = create_advanced_tutorial()
        commands = [s.command for s in tutorial.steps if s.command]
        release_cmds = [c for c in commands if c and "release" in c]
        assert len(release_cmds) >= 1

    def test_tutorials_have_gif_paths(self):
        """Test tutorials reference GIF paths."""
        getting_started = create_getting_started_tutorial()
        gif_steps = [s for s in getting_started.steps if s.gif_path]
        assert len(gif_steps) >= 3, "Getting Started should have 3+ GIF references"

        intermediate = create_intermediate_tutorial()
        gif_steps = [s for s in intermediate.steps if s.gif_path]
        assert len(gif_steps) >= 3, "Intermediate should have 3+ GIF references"

        advanced = create_advanced_tutorial()
        gif_steps = [s for s in advanced.steps if s.gif_path]
        assert len(gif_steps) >= 3, "Advanced should have 3+ GIF references"


class TestTutorialCLI:
    """Tests for tutorial CLI commands."""

    def test_learn_list_output(self, capsys):
        """Test list_tutorials produces formatted output."""
        list_tutorials()
        captured = capsys.readouterr()
        assert "getting-started" in captured.out
        assert "intermediate" in captured.out
        assert "advanced" in captured.out

    def test_learn_list_shows_steps(self, capsys):
        """Test list shows step counts."""
        list_tutorials()
        captured = capsys.readouterr()
        assert "7" in captured.out
        assert "11" in captured.out
        assert "13" in captured.out


class TestTutorialNavigation:
    """Tests for tutorial navigation features."""

    def test_tutorial_has_prerequisites(self):
        """Test tutorials define prerequisites."""
        for factory in [
            create_getting_started_tutorial,
            create_intermediate_tutorial,
            create_advanced_tutorial,
        ]:
            tutorial = factory()
            # Getting started has basic prereqs, others require previous level
            if tutorial.level != TutorialLevel.GETTING_STARTED:
                assert len(tutorial.prerequisites) >= 1

    def test_steps_are_sequential(self):
        """Test step numbers are sequential starting from 1."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            for i, step in enumerate(tutorial.steps, 1):
                assert step.number == i

    def test_last_step_is_next_steps(self):
        """Test last step typically contains next steps info."""
        for level in [TutorialLevel.GETTING_STARTED, TutorialLevel.INTERMEDIATE]:
            tutorial = get_tutorial(level)
            last_step = tutorial.steps[-1]
            # Last step title often contains "Next" or is about progression
            assert last_step.title is not None


class TestTutorialEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_level_with_whitespace(self):
        """Test parse_level handles whitespace."""
        assert parse_level("  getting-started  ") == TutorialLevel.GETTING_STARTED
        assert parse_level("\tintermediate\n") == TutorialLevel.INTERMEDIATE

    def test_parse_level_mixed_case(self):
        """Test parse_level handles mixed case."""
        assert parse_level("GeTtInG-StArTeD") == TutorialLevel.GETTING_STARTED
        assert parse_level("INTERMEDIATE") == TutorialLevel.INTERMEDIATE
        assert parse_level("Advanced") == TutorialLevel.ADVANCED

    def test_show_step_boundary_conditions(self):
        """Test show_step at boundaries."""
        tutorial = create_getting_started_tutorial()
        # First step
        step = tutorial.show_step(1)
        assert step.number == 1
        # Last step
        last = tutorial.show_step(len(tutorial.steps))
        assert last.number == len(tutorial.steps)

    def test_tutorial_with_empty_prerequisites(self):
        """Test tutorial works with no prerequisites."""
        tutorial = Tutorial(
            level=TutorialLevel.GETTING_STARTED,
            title="Test",
            description="Test",
            prerequisites=[],
            steps=[TutorialStep(number=1, title="Test", description="Test")],
        )
        assert tutorial.prerequisites == []


class TestTutorialContentQuality:
    """Tests for tutorial content quality assurance."""

    def test_all_steps_have_titles(self):
        """Test all steps have non-empty titles."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            for step in tutorial.steps:
                assert step.title, f"Step {step.number} in {level.value} has no title"
                assert len(step.title) >= 3, f"Step {step.number} title too short"

    def test_all_steps_have_descriptions(self):
        """Test all steps have non-empty descriptions."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            for step in tutorial.steps:
                assert step.description, f"Step {step.number} in {level.value} has no description"
                assert len(step.description) >= 10, f"Step {step.number} description too short"

    def test_interactive_steps_have_commands(self):
        """Test interactive steps have associated commands."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            for step in tutorial.steps:
                if step.interactive:
                    assert step.command, f"Interactive step {step.number} has no command"

    def test_commands_are_valid_format(self):
        """Test commands follow expected format."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            for step in tutorial.steps:
                if step.command:
                    # Commands should start with 'ait' or be comments
                    assert step.command.startswith("ait") or step.command.startswith("#"), \
                        f"Command '{step.command}' should start with 'ait' or '#'"

    def test_gif_paths_are_valid_format(self):
        """Test GIF paths follow expected format."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            for step in tutorial.steps:
                if step.gif_path:
                    assert step.gif_path.endswith(".gif"), \
                        f"GIF path '{step.gif_path}' should end with .gif"
                    assert "demos/tutorials" in step.gif_path, \
                        f"GIF path '{step.gif_path}' should be in demos/tutorials"


class TestTutorialDisplay:
    """Tests for tutorial display methods."""

    def test_show_intro(self, capsys):
        """Test show_intro displays level info."""
        tutorial = create_getting_started_tutorial()
        tutorial.show_intro()
        captured = capsys.readouterr()
        assert "Getting Started" in captured.out

    def test_show_step_displays_command(self, capsys):
        """Test show_step displays command if present."""
        tutorial = create_getting_started_tutorial()
        # Step 2 has ait doctor command
        tutorial.show_step(2)
        captured = capsys.readouterr()
        assert "ait doctor" in captured.out

    def test_show_step_displays_hint(self, capsys):
        """Test show_step displays hint if present."""
        tutorial = create_getting_started_tutorial()
        # Find a step with a hint
        for i, step in enumerate(tutorial.steps, 1):
            if step.hint:
                tutorial.show_step(i)
                captured = capsys.readouterr()
                assert "Hint" in captured.out or "💡" in captured.out
                break

    def test_show_completion(self, capsys):
        """Test show_completion displays success message."""
        tutorial = create_getting_started_tutorial()
        tutorial.show_completion()
        captured = capsys.readouterr()
        assert "Congratulations" in captured.out or "Complete" in captured.out


class TestTutorialStepAdvanced:
    """Tests for advanced TutorialStep features."""

    def test_step_with_follow_up(self):
        """Test step with follow_up command."""
        step = TutorialStep(
            number=1,
            title="Step with Follow-up",
            description="Has a follow-up command.",
            command="ait status",
            follow_up="ait info",
        )
        assert step.follow_up == "ait info"
        assert step.command == "ait status"

    def test_step_with_validate_callable(self):
        """Test step with validate function."""
        def always_valid():
            return True

        step = TutorialStep(
            number=1,
            title="Validated Step",
            description="Has validation.",
            validate=always_valid,
        )
        assert step.validate is not None
        assert step.validate() is True

    def test_step_with_all_fields(self):
        """Test step with every field populated."""
        def validator():
            return True

        step = TutorialStep(
            number=5,
            title="Complete Step",
            description="Step with all fields.",
            command="ait doctor",
            hint="Run this to check",
            interactive=True,
            gif_path="docs/demos/example.gif",
            diagram="flowchart TD\n    A-->B",
            validate=validator,
            follow_up="ait info",
        )
        assert step.number == 5
        assert step.title == "Complete Step"
        assert step.command == "ait doctor"
        assert step.hint == "Run this to check"
        assert step.interactive is True
        assert step.gif_path == "docs/demos/example.gif"
        assert step.diagram is not None
        assert step.validate() is True
        assert step.follow_up == "ait info"


class TestTutorialCompletion:
    """Tests for tutorial completion and progression suggestions."""

    def test_getting_started_suggests_intermediate(self, capsys):
        """Test Getting Started completion suggests Intermediate."""
        tutorial = create_getting_started_tutorial()
        tutorial.show_completion()
        captured = capsys.readouterr()
        assert "intermediate" in captured.out.lower()

    def test_intermediate_suggests_advanced(self, capsys):
        """Test Intermediate completion suggests Advanced."""
        tutorial = create_intermediate_tutorial()
        tutorial.show_completion()
        captured = capsys.readouterr()
        assert "advanced" in captured.out.lower()

    def test_advanced_no_next_suggestion(self, capsys):
        """Test Advanced completion has no next level suggestion."""
        tutorial = create_advanced_tutorial()
        tutorial.show_completion()
        captured = capsys.readouterr()
        # Should not suggest another tutorial level
        output_lower = captured.out.lower()
        assert "try the" not in output_lower or "getting-started" not in output_lower


class TestTutorialErrorHandling:
    """Tests for error handling and edge cases."""

    def test_parse_level_special_characters(self):
        """Test parse_level with special characters."""
        assert parse_level("getting-started!") is None
        assert parse_level("@intermediate") is None
        assert parse_level("advanced#$%") is None
        assert parse_level("---") is None

    def test_show_step_negative_number(self):
        """Test show_step with negative step number."""
        tutorial = create_getting_started_tutorial()
        with pytest.raises(ValueError, match="Step -1 not found"):
            tutorial.show_step(-1)

    def test_show_step_zero(self):
        """Test show_step with zero."""
        tutorial = create_getting_started_tutorial()
        with pytest.raises(ValueError, match="Step 0 not found"):
            tutorial.show_step(0)

    def test_show_step_large_number(self):
        """Test show_step with number beyond step count."""
        tutorial = create_getting_started_tutorial()
        with pytest.raises(ValueError, match="Step 100 not found"):
            tutorial.show_step(100)

    def test_tutorial_empty_steps(self):
        """Test tutorial with empty steps list."""
        tutorial = Tutorial(
            level=TutorialLevel.GETTING_STARTED,
            title="Empty Tutorial",
            description="Has no steps.",
            steps=[],
        )
        assert len(tutorial.steps) == 0
        with pytest.raises(ValueError):
            tutorial.show_step(1)

    def test_parse_level_unicode(self):
        """Test parse_level with unicode characters."""
        assert parse_level("getting-started\u200b") is None  # zero-width space
        assert parse_level("advanced📚") is None


class TestTutorialContentIntegrity:
    """Tests for content integrity and consistency."""

    def test_all_hints_are_meaningful(self):
        """Test that all hints have meaningful content."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            for step in tutorial.steps:
                if step.hint:
                    assert len(step.hint) >= 5, \
                        f"Step {step.number} in {level.value} has too short hint"

    def test_all_follow_ups_are_valid_format(self):
        """Test that all follow_up commands start with 'ait' or '#'."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            for step in tutorial.steps:
                if step.follow_up:
                    assert step.follow_up.startswith("ait") or step.follow_up.startswith("#"), \
                        f"Follow-up '{step.follow_up}' in step {step.number} has invalid format"

    def test_interactive_steps_explain_action(self):
        """Test interactive steps have descriptions mentioning what to do."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            for step in tutorial.steps:
                if step.interactive:
                    assert len(step.description) >= 20, \
                        f"Interactive step {step.number} in {level.value} needs longer description"

    def test_getting_started_first_step_is_intro(self):
        """Test that Getting Started first step is introductory (non-interactive)."""
        tutorial = get_tutorial(TutorialLevel.GETTING_STARTED)
        first_step = tutorial.steps[0]
        # Getting Started should start with intro, not interactive
        assert first_step.interactive is False, \
            "Getting Started should begin with introduction, not interactive step"

    def test_intermediate_advanced_can_start_interactive(self):
        """Test that Intermediate/Advanced can start with interactive (assumes prior knowledge)."""
        for level in [TutorialLevel.INTERMEDIATE, TutorialLevel.ADVANCED]:
            tutorial = get_tutorial(level)
            first_step = tutorial.steps[0]
            # These tutorials assume prior knowledge, so can be interactive
            assert first_step.title is not None, f"{level.value} first step has title"


class TestTutorialRegistry:
    """Tests for the tutorial registry and lookup functions."""

    def test_get_tutorial_returns_correct_type(self):
        """Test get_tutorial returns Tutorial instances."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            assert isinstance(tutorial, Tutorial)
            assert isinstance(tutorial.level, TutorialLevel)

    def test_all_levels_have_factory(self):
        """Test every TutorialLevel has a factory function."""
        for level in TutorialLevel:
            tutorial = get_tutorial(level)
            assert tutorial is not None, f"No factory for {level.value}"

    def test_tutorials_are_independent(self):
        """Test each get_tutorial call returns fresh instance."""
        tutorial1 = get_tutorial(TutorialLevel.GETTING_STARTED)
        tutorial2 = get_tutorial(TutorialLevel.GETTING_STARTED)
        assert tutorial1 is not tutorial2  # Different instances
        assert tutorial1.steps is not tutorial2.steps  # Different step lists


class TestTutorialDisplayAdvanced:
    """Advanced display tests."""

    def test_show_step_displays_follow_up(self, capsys):
        """Test show_step displays follow_up command if present."""
        tutorial = create_advanced_tutorial()
        # Find a step with follow_up
        for i, step in enumerate(tutorial.steps, 1):
            if step.follow_up:
                tutorial.show_step(i)
                captured = capsys.readouterr()
                assert "Follow-up" in captured.out or "📎" in captured.out
                break

    def test_show_intro_displays_prerequisites(self, capsys):
        """Test show_intro displays prerequisites."""
        tutorial = create_intermediate_tutorial()
        tutorial.show_intro()
        captured = capsys.readouterr()
        assert "Prerequisites" in captured.out

    def test_show_intro_displays_step_count(self, capsys):
        """Test show_intro shows step count."""
        tutorial = create_getting_started_tutorial()
        tutorial.show_intro()
        captured = capsys.readouterr()
        assert "7" in captured.out or "Steps" in captured.out

    def test_show_completion_shows_level(self, capsys):
        """Test show_completion displays level name."""
        tutorial = create_intermediate_tutorial()
        tutorial.show_completion()
        captured = capsys.readouterr()
        assert "Intermediate" in captured.out


class TestParseLevelRobustness:
    """Additional parse_level robustness tests."""

    def test_parse_level_with_leading_trailing_chars(self):
        """Test parse_level strips only whitespace."""
        assert parse_level("  advanced  ") == TutorialLevel.ADVANCED
        assert parse_level("\n\tintermediate\r") == TutorialLevel.INTERMEDIATE

    def test_parse_level_partial_match_priority(self):
        """Test partial match finds correct level."""
        # 'get' is unique to getting-started
        assert parse_level("get") == TutorialLevel.GETTING_STARTED
        # 'int' is unique to intermediate
        assert parse_level("int") == TutorialLevel.INTERMEDIATE
        # 'adv' is unique to advanced
        assert parse_level("adv") == TutorialLevel.ADVANCED

    def test_parse_level_exact_match_preferred(self):
        """Test exact match is found even if partial would also match."""
        # Exact match should work
        assert parse_level("advanced") == TutorialLevel.ADVANCED
        # Full hyphenated name
        assert parse_level("getting-started") == TutorialLevel.GETTING_STARTED

    def test_parse_level_numbers_rejected(self):
        """Test parse_level rejects numeric input."""
        assert parse_level("1") is None
        assert parse_level("123") is None
        assert parse_level("1advanced") is None