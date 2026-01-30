from abc import ABC, abstractmethod
from dataclasses import dataclass


class ConnectorNotConfiguredError(Exception):
    pass


@dataclass(frozen=True)
class ChatResponse:
    content: str
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class EmbedResponse:
    vector: list[float]
    input_tokens: int


class LLMConnector(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    def chat(self, system: str, user: str) -> ChatResponse: ...

    @abstractmethod
    def embed(self, text: str) -> EmbedResponse: ...

    @abstractmethod
    def get_embedding_dimension(self) -> int: ...
