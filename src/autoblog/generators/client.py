"""SDK client selection for generators: Anthropic API key vs AWS Bedrock.

Both paths expose the same ``messages.create`` / ``messages.stream`` surface, so
generators only differ in how the client is constructed and how the model ID is
spelled (Bedrock requires an ``anthropic.`` prefix).
"""

from __future__ import annotations

import anthropic

from ..config import GeneratorConfig


def resolve_model_id(cfg: GeneratorConfig) -> str:
    """Return the model ID for the configured provider.

    Bedrock model IDs are prefixed with ``anthropic.`` (e.g.
    ``anthropic.claude-opus-4-8``); the first-party API uses the bare ID.
    """
    if cfg.provider == "bedrock":
        if cfg.model.startswith("anthropic."):
            return cfg.model
        return f"anthropic.{cfg.model}"
    return cfg.model


def build_client(cfg: GeneratorConfig):
    """Construct the SDK client for the configured provider.

    - ``anthropic``: ``Anthropic()`` (resolves ANTHROPIC_API_KEY from the env).
    - ``bedrock``: ``AnthropicBedrockMantle(aws_region=...)`` (AWS credential
      chain: env vars, shared profile, or an IAM role). Requires the ``bedrock``
      extra (boto3).
    """
    if cfg.provider == "anthropic":
        return anthropic.Anthropic()
    if cfg.provider == "bedrock":
        from anthropic import AnthropicBedrockMantle

        return AnthropicBedrockMantle(aws_region=cfg.aws_region)
    raise ValueError(
        f"Unknown generator provider {cfg.provider!r}. Known: anthropic, bedrock."
    )
