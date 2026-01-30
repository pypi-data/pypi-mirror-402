"""Utility functions for ACE middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel


def init_chat_model(model: str) -> BaseChatModel:
    """Initialize a chat model from a model name string.

    This is a convenience function that initializes common chat models
    by name. For production use, consider passing pre-configured model
    instances directly to ACEMiddleware.

    Supported formats:
    - "gpt-4o", "gpt-4o-mini", "gpt-4.1" -> OpenAI (requires langchain-openai)
    - "claude-3-5-sonnet-20241022" -> Anthropic (requires langchain-anthropic)
    - "gemini-1.5-pro" -> Google (requires langchain-google-genai)

    Args:
        model: Model name string.

    Returns:
        Initialized chat model.

    Raises:
        ImportError: If the required provider package is not installed.
        ValueError: If the model name format is not recognized.
    """
    model_lower = model.lower()

    # OpenAI models
    if any(
        model_lower.startswith(prefix) for prefix in ("gpt-", "o1", "o3", "chatgpt-", "ft:gpt-")
    ):
        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model=model)
        except ImportError as e:
            msg = (
                f"To use OpenAI model '{model}', install langchain-openai: "
                "pip install langchain-openai"
            )
            raise ImportError(msg) from e

    # Anthropic models
    if model_lower.startswith("claude"):
        try:
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(model=model)
        except ImportError as e:
            msg = (
                f"To use Anthropic model '{model}', install langchain-anthropic: "
                "pip install langchain-anthropic"
            )
            raise ImportError(msg) from e

    # Google models
    if model_lower.startswith("gemini"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(model=model)
        except ImportError as e:
            msg = (
                f"To use Google model '{model}', install langchain-google-genai: "
                "pip install langchain-google-genai"
            )
            raise ImportError(msg) from e

    # Try langchain's init_chat_model if available (langchain v1)
    try:
        from langchain.chat_models import init_chat_model as lc_init_chat_model

        return lc_init_chat_model(model)
    except ImportError:
        pass

    msg = (
        f"Could not determine provider for model '{model}'. "
        "Please pass a pre-configured BaseChatModel instance instead, or "
        "use a recognized model name format (e.g., 'gpt-4o', 'claude-3-5-sonnet')."
    )
    raise ValueError(msg)
