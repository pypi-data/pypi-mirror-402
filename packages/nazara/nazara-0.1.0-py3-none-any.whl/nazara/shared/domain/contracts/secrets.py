from abc import ABC, abstractmethod


class SecretResolver(ABC):
    """
    Port for resolving secret references.

    This allows the host application to implement secret resolution
    using their preferred backend (Vault, AWS Secrets Manager,
    environment variables, etc.).
    """

    @abstractmethod
    def resolve(self, secret_ref: str) -> str:
        """
        Resolve a secret reference to its actual value.

        Args:
            secret_ref: The secret reference/key to resolve

        Returns:
            The secret value

        Raises:
            SecretNotFoundError: If the secret cannot be resolved
        """
        ...


class SecretNotFoundError(Exception):
    """Raised when a secret reference cannot be resolved."""

    def __init__(self, secret_ref: str) -> None:
        self.secret_ref = secret_ref
        super().__init__(f"Secret not found: {secret_ref}")
