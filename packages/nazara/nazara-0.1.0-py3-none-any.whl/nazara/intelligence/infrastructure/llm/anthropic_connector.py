import logging
from typing import Any

from anthropic import Anthropic

from nazara.intelligence.domain.contracts.llm import (
    ChatResponse,
    EmbedResponse,
    LLMConnector,
)
from nazara.intelligence.domain.model_registry import get_default_model

logger = logging.getLogger(__name__)

_PROVIDER = "anthropic"


class AnthropicConnector(LLMConnector):
    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        max_tokens: int = 500,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = (
            model or get_default_model(_PROVIDER, "summary") or "claude-3-5-haiku-20241022"
        )
        self._max_tokens = max_tokens
        self._base_url = base_url
        self._timeout = timeout
        self._client: Anthropic | None = None

    @property
    def provider_name(self) -> str:
        return _PROVIDER

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def client(self) -> Anthropic:
        if self._client is None:
            kwargs: dict[str, Any] = {
                "api_key": self._api_key,
                "timeout": self._timeout,
            }
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = Anthropic(**kwargs)
        return self._client

    def chat(self, system: str, user: str) -> ChatResponse:
        logger.debug(f"Anthropic system prompt:\n{system}")
        logger.debug(f"Anthropic user message:\n{user}")
        response = self.client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        input_tokens = response.usage.input_tokens if response.usage else 0
        output_tokens = response.usage.output_tokens if response.usage else 0

        logger.info(
            f"Token usage: input={input_tokens}, output={output_tokens}, "
            f"total={input_tokens + output_tokens}"
        )
        logger.debug(f"Response: {content[:100]}...")

        return ChatResponse(
            content=content.strip(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def embed(self, text: str) -> EmbedResponse:
        raise NotImplementedError("Anthropic does not support embeddings")

    def get_embedding_dimension(self) -> int:
        raise NotImplementedError("Anthropic does not support embeddings")
