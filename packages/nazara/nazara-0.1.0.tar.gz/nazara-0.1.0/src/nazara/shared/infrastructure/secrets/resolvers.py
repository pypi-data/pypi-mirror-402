import json
import os
from pathlib import Path
from typing import Any

from nazara.shared.domain.contracts.secrets import SecretNotFoundError, SecretResolver


class JSONSecretResolver(SecretResolver):
    """
    Secret resolver that reads secrets from a JSON file.

    This is suitable for development and testing. In production,
    use a proper secrets manager (Vault, AWS Secrets Manager, etc.).

    The JSON file should have a flat structure:
    {
        "slack_api_token": "xoxb-...",
        "sentry_api_key": "...",
        "datadog_api_key": "...",
        "incident_io_api_key": "..."
    }

    Secret references in IngestorConfig.secret_ref should match
    the keys in this JSON file.

    Example:
        resolver = JSONSecretResolver("/path/to/secrets.json")
        api_key = resolver.resolve("sentry_api_key")
    """

    def __init__(self, secrets_file: str | Path | None = None) -> None:
        """
        Initialize the JSON secret resolver.

        Args:
            secrets_file: Path to the secrets JSON file.
                         Defaults to the path specified in NAZARA_SECRETS_FILE env var,
                         or 'secrets.json' in the current working directory.
        """
        if secrets_file is None:
            secrets_file = os.environ.get(
                "NAZARA_SECRETS_FILE",
                Path.cwd() / "secrets.json",
            )

        self._secrets_file = Path(secrets_file)
        self._secrets: dict[str, Any] = {}
        self._loaded = False

    def _load_secrets(self, force: bool = False) -> None:
        if self._loaded and not force:
            return

        if not self._secrets_file.exists():
            # Create an empty secrets file as a template
            self._secrets_file.write_text(
                json.dumps(
                    {
                        "_comment": "Add your API keys here. Keys should match secret_ref in IngestorConfig.",
                        "slack_api_token": "",
                        "sentry_api_key": "",
                        "datadog_api_key": "",
                        "incident_io_api_key": "",
                    },
                    indent=2,
                )
            )
            self._secrets = {}
        else:
            with open(self._secrets_file) as f:
                self._secrets = json.load(f)

        self._loaded = True

    def resolve(self, secret_ref: str) -> str:
        """
        Resolve a secret reference to its actual value.

        Args:
            secret_ref: The key in the secrets JSON file

        Returns:
            The secret value

        Raises:
            SecretNotFoundError: If the secret is not found or is empty
        """
        # Check if Django is available and in DEBUG mode
        force_reload = False
        try:
            from django.conf import settings

            force_reload = getattr(settings, "DEBUG", False)
        except (ImportError, Exception):
            pass

        self._load_secrets(force=force_reload)

        if secret_ref not in self._secrets:
            raise SecretNotFoundError(secret_ref)

        value = self._secrets[secret_ref]

        if not value or value == "":
            raise SecretNotFoundError(secret_ref)

        return str(value)

    def reload(self) -> None:
        self._loaded = False
        self._load_secrets()


class EnvSecretResolver(SecretResolver):
    """
    Secret resolver that reads secrets from environment variables.

    This is an alternative to JSONSecretResolver that reads from
    environment variables instead of a file.

    Secret references should be environment variable names,
    optionally with a prefix. For example:
    - secret_ref="SLACK_API_TOKEN" -> reads os.environ["SLACK_API_TOKEN"]
    - With prefix="NAZARA_": secret_ref="slack" -> reads os.environ["NAZARA_SLACK"]

    Example:
        resolver = EnvSecretResolver(prefix="NAZARA_")
        api_key = resolver.resolve("sentry_api_key")  # reads NAZARA_SENTRY_API_KEY
    """

    def __init__(self, prefix: str = "") -> None:
        """
        Initialize the environment variable secret resolver.

        Args:
            prefix: Optional prefix to prepend to all secret_ref lookups.
                   For example, prefix="NAZARA_" means secret_ref="slack"
                   will look up "NAZARA_SLACK" in environment variables.
        """
        self._prefix = prefix

    def resolve(self, secret_ref: str) -> str:
        """
        Resolve a secret reference to its environment variable value.

        Args:
            secret_ref: The environment variable name (without prefix)

        Returns:
            The secret value from the environment

        Raises:
            SecretNotFoundError: If the env var is not set or is empty
        """
        env_var = f"{self._prefix}{secret_ref}".upper()
        value = os.environ.get(env_var)

        if not value:
            raise SecretNotFoundError(f"{env_var} (from secret_ref={secret_ref})")

        return value


class DictSecretResolver(SecretResolver):
    """
    Secret resolver that uses an in-memory dictionary.

    Useful for testing when you want to inject secrets directly.

    Example:
        resolver = DictSecretResolver({
            "sentry_api_key": "test-key-123",
            "slack_token": "xoxb-test",
        })
        api_key = resolver.resolve("sentry_api_key")
    """

    def __init__(self, secrets: dict[str, str] | None = None) -> None:
        """
        Initialize with a dictionary of secrets.

        Args:
            secrets: Dictionary mapping secret_ref to secret values
        """
        self._secrets = secrets or {}

    def resolve(self, secret_ref: str) -> str:
        """
        Resolve a secret reference from the in-memory dictionary.

        Args:
            secret_ref: The key in the secrets dictionary

        Returns:
            The secret value

        Raises:
            SecretNotFoundError: If the secret is not found
        """
        if secret_ref not in self._secrets:
            raise SecretNotFoundError(secret_ref)

        value = self._secrets[secret_ref]
        if not value:
            raise SecretNotFoundError(secret_ref)

        return value

    def set_secret(self, secret_ref: str, value: str) -> None:
        self._secrets[secret_ref] = value

    def remove_secret(self, secret_ref: str) -> None:
        self._secrets.pop(secret_ref, None)
