import logging

from openai import OpenAI

from nazara.intelligence.domain.contracts.llm import (
    ChatResponse,
    EmbedResponse,
    LLMConnector,
)
from nazara.intelligence.domain.model_registry import (
    get_default_model,
    get_embedding_dimension,
)

logger = logging.getLogger(__name__)

_PROVIDER = "openai"


class OpenAIConnector(LLMConnector):
    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        embedding_model: str | None = None,
        max_tokens: int = 500,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model or get_default_model(_PROVIDER, "summary") or "gpt-4o-mini"
        self._embedding_model = (
            embedding_model or get_default_model(_PROVIDER, "embedding") or "text-embedding-3-small"
        )
        self._max_tokens = max_tokens
        self._base_url = base_url
        self._timeout = timeout
        self._client: OpenAI | None = None

    @property
    def provider_name(self) -> str:
        return _PROVIDER

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._client

    def chat(self, system: str, user: str) -> ChatResponse:
        logger.debug(f"OpenAI system prompt:\n{system}")
        logger.debug(f"OpenAI user message:\n{user}")
        response = self.client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=self._max_tokens,
            temperature=0.3,
        )

        content = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

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
        response = self.client.embeddings.create(
            model=self._embedding_model,
            input=text,
        )

        vector = response.data[0].embedding
        input_tokens = response.usage.total_tokens if response.usage else 0

        logger.debug(f"Generated embedding for text ({len(text)} chars): dim={len(vector)}")

        return EmbedResponse(vector=vector, input_tokens=input_tokens)

    def get_embedding_dimension(self) -> int:
        return get_embedding_dimension(_PROVIDER, self._embedding_model) or 1536
