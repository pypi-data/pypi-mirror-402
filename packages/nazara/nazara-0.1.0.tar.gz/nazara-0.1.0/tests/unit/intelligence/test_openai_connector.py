from unittest.mock import MagicMock, patch

import pytest

from nazara.intelligence.domain.contracts.llm import ChatResponse, EmbedResponse
from nazara.intelligence.infrastructure.llm.openai_connector import OpenAIConnector


@patch("nazara.intelligence.infrastructure.llm.openai_connector.OpenAI")
def test_chat_should_call_api_with_system_and_user_messages(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Generated summary"
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_client.chat.completions.create.return_value = mock_response

    connector = OpenAIConnector(api_key="test-key")
    result = connector.chat(
        system="You are an expert.",
        user="Summarize this.",
    )

    assert isinstance(result, ChatResponse)
    assert result.content == "Generated summary"
    assert result.input_tokens == 100
    assert result.output_tokens == 50

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    assert messages[0]["content"] == "You are an expert."
    assert messages[1]["content"] == "Summarize this."


@patch("nazara.intelligence.infrastructure.llm.openai_connector.OpenAI")
def test_chat_should_strip_whitespace_from_response(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "  Generated summary  \n"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    mock_client.chat.completions.create.return_value = mock_response

    connector = OpenAIConnector(api_key="test-key")
    result = connector.chat(system="System", user="User")

    assert result.content == "Generated summary"


@patch("nazara.intelligence.infrastructure.llm.openai_connector.OpenAI")
def test_embed_should_return_vector_with_token_count(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.data = [MagicMock()]
    mock_response.data[0].embedding = [0.1, 0.2, 0.3]
    mock_response.usage.total_tokens = 25
    mock_client.embeddings.create.return_value = mock_response

    connector = OpenAIConnector(api_key="test-key")
    result = connector.embed("Test text")

    assert isinstance(result, EmbedResponse)
    assert result.vector == [0.1, 0.2, 0.3]
    assert result.input_tokens == 25


@pytest.mark.parametrize(
    "model,expected_dim",
    [
        ("text-embedding-3-small", 1536),
        ("text-embedding-3-large", 3072),
    ],
)
def test_get_embedding_dimension_should_return_correct_value(model, expected_dim):
    connector = OpenAIConnector(api_key="test-key", embedding_model=model)

    assert connector.get_embedding_dimension() == expected_dim


def test_client_should_be_lazily_initialized():
    connector = OpenAIConnector(api_key="test-key")

    assert connector._client is None


def test_provider_name_should_return_openai():
    connector = OpenAIConnector(api_key="test-key")

    assert connector.provider_name == "openai"


def test_model_name_should_return_configured_model():
    connector = OpenAIConnector(api_key="test-key", model="gpt-4o")

    assert connector.model_name == "gpt-4o"


def test_model_name_should_return_default_when_not_specified():
    connector = OpenAIConnector(api_key="test-key")

    assert connector.model_name == "gpt-4o-mini"


@patch("nazara.intelligence.infrastructure.llm.openai_connector.OpenAI")
def test_client_should_use_custom_base_url(mock_openai_class):
    connector = OpenAIConnector(
        api_key="test-key",
        base_url="https://custom.api.com",
    )
    _ = connector.client

    mock_openai_class.assert_called_once_with(
        api_key="test-key",
        base_url="https://custom.api.com",
        timeout=30.0,
    )
