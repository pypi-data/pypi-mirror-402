"""Unit tests for ACE middleware."""

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ace.middleware import ACEMiddleware, ACEState
from ace.types import ModelRequest, Runtime


class TestACEMiddlewareInit:
    """Tests for ACEMiddleware initialization."""

    def test_init_with_string_models(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        assert ace._reflector_model_spec == "gpt-4o-mini"
        assert ace._curator_model_spec == "gpt-4o-mini"
        assert ace._reflector_model is None  # Lazy init
        assert ace._curator_model is None

    def test_init_with_custom_config(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
            curator_frequency=10,
            playbook_token_budget=50000,
            auto_prune=True,
            prune_threshold=0.6,
            prune_min_interactions=5,
            expected_interactions=200,
        )

        assert ace.curator_frequency == 10
        assert ace.playbook_token_budget == 50000
        assert ace.auto_prune is True
        assert ace.prune_threshold == 0.6
        assert ace.prune_min_interactions == 5
        assert ace.expected_interactions == 200

    def test_init_with_custom_playbook(self):
        custom_playbook = """## strategies_and_insights
[str-00001] helpful=5 harmful=0 :: Pre-loaded strategy
"""
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
            initial_playbook=custom_playbook,
        )

        assert "[str-00001]" in ace.initial_playbook
        assert "Pre-loaded strategy" in ace.initial_playbook


class TestACEMiddlewareBeforeAgent:
    """Tests for before_agent hook."""

    def test_initializes_state_when_empty(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        state: ACEState = {"messages": []}
        runtime = Runtime()

        updates = ace.before_agent(state, runtime)

        assert updates is not None
        assert "ace_playbook" in updates
        assert "ace_last_reflection" in updates
        assert "ace_interaction_count" in updates
        assert updates["ace_interaction_count"] == 0

    def test_does_not_reinitialize_existing_state(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        state: ACEState = {
            "messages": [],
            "ace_playbook": {"content": "existing", "next_global_id": 5, "stats": {}},
        }
        runtime = Runtime()

        updates = ace.before_agent(state, runtime)

        assert updates is None


class TestACEMiddlewareWrapModelCall:
    """Tests for wrap_model_call hook."""

    def test_injects_playbook_into_system_prompt(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
            initial_playbook="## test\n[str-00001] helpful=0 harmful=0 :: Test bullet",
        )

        state: ACEState = {"messages": [HumanMessage(content="test")]}
        request = ModelRequest(
            state=state,
            system_message="Original prompt",
            messages=[HumanMessage(content="test")],
        )

        captured_request = None

        def mock_handler(req: ModelRequest):
            nonlocal captured_request
            captured_request = req
            return MagicMock()

        ace.wrap_model_call(request, mock_handler)

        assert captured_request is not None
        assert isinstance(captured_request.system_message, SystemMessage)
        assert "ACE PLAYBOOK" in captured_request.system_message.content
        assert "[str-00001]" in captured_request.system_message.content


class TestACEMiddlewareHelpers:
    """Tests for internal helper methods."""

    def test_get_last_user_message(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        messages = [
            HumanMessage(content="First question"),
            AIMessage(content="First answer"),
            HumanMessage(content="Second question"),
        ]

        result = ace._get_last_user_message(messages)
        assert result == "Second question"

    def test_get_last_user_message_empty(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        result = ace._get_last_user_message([])
        assert result == ""

    def test_get_last_exchange(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        messages = [
            HumanMessage(content="Q1"),
            AIMessage(content="A1"),
            HumanMessage(content="Q2"),
            AIMessage(content="A2"),
        ]

        result = ace._get_last_exchange(messages)
        assert len(result) == 2
        assert result[0].content == "Q2"
        assert result[1].content == "A2"

    def test_extract_text_content_string(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        result = ace._extract_text_content("Simple string")
        assert result == "Simple string"

    def test_extract_text_content_list(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        content = [
            {"type": "text", "text": "Part 1"},
            {"type": "text", "text": "Part 2"},
        ]
        result = ace._extract_text_content(content)
        assert "Part 1" in result
        assert "Part 2" in result

    def test_extract_json_from_response_direct(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        text = '{"key": "value"}'
        result = ace._extract_json_from_response(text)
        assert result == {"key": "value"}

    def test_extract_json_from_response_code_block(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        text = """Here's the response:
```json
{"key": "value"}
```
"""
        result = ace._extract_json_from_response(text)
        assert result == {"key": "value"}

    def test_extract_json_from_response_invalid(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        result = ace._extract_json_from_response("Not JSON at all")
        assert result is None


class TestACEMiddlewareReflectionContext:
    """Tests for reflection context preparation."""

    def test_skips_reflection_for_tool_calls(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
        )

        # AI message with pending tool calls
        ai_msg = AIMessage(
            content="Let me calculate that.",
            tool_calls=[{"name": "calculator", "args": {"expr": "2+2"}, "id": "1"}],
        )

        state: ACEState = {
            "messages": [HumanMessage(content="What is 2+2?"), ai_msg],
        }

        result = ace._prepare_reflection_context(state)
        assert result is None  # Should skip reflection

    def test_prepares_context_for_terminal_response(self):
        ace = ACEMiddleware(
            reflector_model="gpt-4o-mini",
            curator_model="gpt-4o-mini",
            initial_playbook="## test\n[str-00001] helpful=0 harmful=0 :: Test",
        )

        # AI message without tool calls (terminal response)
        ai_msg = AIMessage(content="The answer is 4. <!-- bullet_ids: [] -->")

        state: ACEState = {
            "messages": [HumanMessage(content="What is 2+2?"), ai_msg],
            "ace_playbook": {
                "content": "## test\n[str-00001] helpful=0 harmful=0 :: Test",
                "next_global_id": 2,
                "stats": {},
            },
        }

        result = ace._prepare_reflection_context(state)
        assert result is not None
        playbook, reflector_prompt, user_question, bullets_used = result
        assert "What is 2+2?" in user_question or "2+2" in reflector_prompt


class TestACEState:
    """Tests for ACEState type."""

    def test_ace_state_fields(self):
        state: ACEState = {
            "messages": [HumanMessage(content="test")],
            "ace_playbook": {"content": "test", "next_global_id": 1, "stats": {}},
            "ace_last_reflection": "Last reflection",
            "ace_interaction_count": 5,
            "ground_truth": "42",
        }

        assert state["ace_interaction_count"] == 5
        assert state["ground_truth"] == "42"
