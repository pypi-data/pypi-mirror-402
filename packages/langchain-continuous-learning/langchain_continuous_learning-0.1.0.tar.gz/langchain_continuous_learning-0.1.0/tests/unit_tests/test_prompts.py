"""Unit tests for prompt utilities."""

from langchain_core.messages import SystemMessage

from ace.prompts import (
    build_curator_prompt,
    build_reflector_prompt,
    build_system_prompt_with_playbook,
)


class TestBuildSystemPromptWithPlaybook:
    """Tests for build_system_prompt_with_playbook function."""

    def test_with_string_prompt(self):
        result = build_system_prompt_with_playbook(
            original_prompt="You are a helpful assistant.",
            playbook="## strategies_and_insights\n[str-00001] helpful=0 harmful=0 :: Test",
        )

        assert "You are a helpful assistant." in result
        assert "ACE PLAYBOOK" in result
        assert "[str-00001]" in result

    def test_with_system_message(self):
        original = SystemMessage(content="System prompt here")
        result = build_system_prompt_with_playbook(
            original_prompt=original,
            playbook="## test",
        )

        assert "System prompt here" in result
        assert "ACE PLAYBOOK" in result

    def test_with_none_prompt(self):
        result = build_system_prompt_with_playbook(
            original_prompt=None,
            playbook="## test",
        )

        assert "helpful AI assistant" in result
        assert "ACE PLAYBOOK" in result

    def test_with_reflection(self):
        result = build_system_prompt_with_playbook(
            original_prompt="Test",
            playbook="## test",
            reflection="Previous attempt failed due to X",
        )

        assert "PREVIOUS REFLECTION" in result
        assert "Previous attempt failed" in result

    def test_without_reflection(self):
        result = build_system_prompt_with_playbook(
            original_prompt="Test",
            playbook="## test",
            reflection="",
        )

        assert "PREVIOUS REFLECTION" not in result


class TestBuildReflectorPrompt:
    """Tests for build_reflector_prompt function."""

    def test_basic_prompt(self):
        result = build_reflector_prompt(
            question="What is 2 + 2?",
            reasoning_trace="[USER]: What is 2 + 2?\n[AGENT]: The answer is 4.",
            feedback="Response was correct",
            bullets_used="[str-00001] helpful=0 harmful=0 :: Test bullet",
        )

        assert "What is 2 + 2?" in result
        assert "[USER]:" in result or "User Query" in result
        assert "bullet_tags" in result
        assert "JSON" in result

    def test_with_ground_truth(self):
        result = build_reflector_prompt(
            question="What is 2 + 2?",
            reasoning_trace="Agent said 5",
            feedback="Incorrect",
            bullets_used="(No bullets)",
            ground_truth="4",
        )

        assert "Ground Truth" in result
        assert "4" in result

    def test_without_ground_truth(self):
        result = build_reflector_prompt(
            question="What is 2 + 2?",
            reasoning_trace="Agent said 4",
            feedback="Correct",
            bullets_used="(No bullets)",
            ground_truth=None,
        )

        assert "Ground Truth" not in result


class TestBuildCuratorPrompt:
    """Tests for build_curator_prompt function."""

    def test_basic_prompt(self):
        result = build_curator_prompt(
            current_step=5,
            total_samples=100,
            token_budget=80000,
            playbook_stats='{"total_bullets": 3}',
            recent_reflection="Agent made an error with percentages",
            current_playbook="## strategies_and_insights",
            question_context="Calculate 15% of 200",
        )

        assert "Step 5 of 100" in result
        assert "80000" in result
        assert "total_bullets" in result
        assert "percentages" in result
        assert "15% of 200" in result
        assert "strategies_and_insights" in result

    def test_includes_valid_sections(self):
        result = build_curator_prompt(
            current_step=1,
            total_samples=10,
            token_budget=1000,
            playbook_stats="{}",
            recent_reflection="",
            current_playbook="",
        )

        assert "strategies_and_insights" in result
        assert "common_mistakes_to_avoid" in result
        assert "others" in result

    def test_empty_question_context(self):
        result = build_curator_prompt(
            current_step=1,
            total_samples=10,
            token_budget=1000,
            playbook_stats="{}",
            recent_reflection="",
            current_playbook="",
            question_context="",
        )

        assert "No question context available" in result
