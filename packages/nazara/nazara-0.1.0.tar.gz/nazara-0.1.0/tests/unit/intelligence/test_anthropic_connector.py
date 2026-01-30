from unittest.mock import MagicMock, patch

import pytest

from nazara.intelligence.domain.contracts.llm import ChatResponse
from nazara.intelligence.infrastructure.llm.anthropic_connector import (
    AnthropicConnector,
)


@patch("nazara.intelligence.infrastructure.llm.anthropic_connector.Anthropic")
def test_chat_should_call_api_with_system_and_user_messages(mock_anthropic_class):
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client
    mock_block = MagicMock()
    mock_block.text = "Generated summary"
    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_response

    connector = AnthropicConnector(api_key="test-key")
    result = connector.chat(
        system="You are an expert.",
        user="Summarize this.",
    )

    assert isinstance(result, ChatResponse)
    assert result.content == "Generated summary"
    assert result.input_tokens == 100
    assert result.output_tokens == 50

    call_args = mock_client.messages.create.call_args
    assert call_args.kwargs["system"] == "You are an expert."
    assert call_args.kwargs["messages"][0]["content"] == "Summarize this."


@patch("nazara.intelligence.infrastructure.llm.anthropic_connector.Anthropic")
def test_chat_should_concatenate_multiple_text_blocks(mock_anthropic_class):
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client
    mock_block1 = MagicMock()
    mock_block1.text = "First part. "
    mock_block2 = MagicMock()
    mock_block2.text = "Second part."
    mock_response = MagicMock()
    mock_response.content = [mock_block1, mock_block2]
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 5
    mock_client.messages.create.return_value = mock_response

    connector = AnthropicConnector(api_key="test-key")
    result = connector.chat(system="System", user="User")

    assert result.content == "First part. Second part."


@patch("nazara.intelligence.infrastructure.llm.anthropic_connector.Anthropic")
def test_chat_should_strip_whitespace_from_response(mock_anthropic_class):
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client
    mock_block = MagicMock()
    mock_block.text = "  Generated summary  \n"
    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 5
    mock_client.messages.create.return_value = mock_response

    connector = AnthropicConnector(api_key="test-key")
    result = connector.chat(system="System", user="User")

    assert result.content == "Generated summary"


def test_embed_should_raise_not_implemented_error():
    connector = AnthropicConnector(api_key="test-key")

    with pytest.raises(NotImplementedError) as exc_info:
        connector.embed("Test text")

    assert "does not support embeddings" in str(exc_info.value)


def test_get_embedding_dimension_should_raise_not_implemented_error():
    connector = AnthropicConnector(api_key="test-key")

    with pytest.raises(NotImplementedError) as exc_info:
        connector.get_embedding_dimension()

    assert "does not support embeddings" in str(exc_info.value)


def test_client_should_be_lazily_initialized():
    connector = AnthropicConnector(api_key="test-key")

    assert connector._client is None


def test_provider_name_should_return_anthropic():
    connector = AnthropicConnector(api_key="test-key")

    assert connector.provider_name == "anthropic"


def test_model_name_should_return_configured_model():
    connector = AnthropicConnector(api_key="test-key", model="claude-3-opus")

    assert connector.model_name == "claude-3-opus"


def test_model_name_should_return_default_when_not_specified():
    connector = AnthropicConnector(api_key="test-key")

    assert connector.model_name == "claude-3-5-haiku-20241022"


@patch("nazara.intelligence.infrastructure.llm.anthropic_connector.Anthropic")
def test_client_should_use_custom_base_url(mock_anthropic_class):
    connector = AnthropicConnector(
        api_key="test-key",
        base_url="https://custom.api.com",
    )
    _ = connector.client

    mock_anthropic_class.assert_called_once_with(
        api_key="test-key",
        timeout=30.0,
        base_url="https://custom.api.com",
    )
